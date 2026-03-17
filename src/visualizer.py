"""Maps audio features to HSV color commands for the bulbs."""

import asyncio
import logging
import time

from .audio_analyzer import AudioFeatures
from .bulb_controller import BulbController

logger = logging.getLogger(__name__)

# Rate limiting: minimum seconds between commands to same bulb
MIN_COMMAND_INTERVAL = 0.070  # 70ms
# Minimum perceptual delta to send a new command (avoid flickering)
COLOR_DELTA_THRESHOLD = 8

# Gamma correction for perceptually linear brightness
GAMMA = 2.2
GAMMA_LUT = [int((i / 100.0) ** (1.0 / GAMMA) * 100) for i in range(101)]

# Beat decay duration in seconds
BEAT_DECAY_S = 0.25  # 250ms hold + fade


def _gamma(brightness: int) -> int:
    """Apply gamma correction so brightness changes look linear to the eye."""
    return GAMMA_LUT[min(100, max(0, brightness))]


def _hue_distance(h1: int, h2: int) -> int:
    """Shortest distance between two hues on the 0-360 circle."""
    d = abs(h1 - h2)
    return min(d, 360 - d)


def _hsv_delta(hsv1: tuple[int, int, int], hsv2: tuple[int, int, int]) -> float:
    """Perceptually weighted HSV delta (0-255 scale)."""
    hue_d = _hue_distance(hsv1[0], hsv2[0]) / 360.0
    sat_d = abs(hsv1[1] - hsv2[1]) / 100.0
    bri_d = abs(hsv1[2] - hsv2[2]) / 100.0
    return (hue_d * 0.4 + sat_d * 0.2 + bri_d * 0.4) * 255


def _exp_brightness(volume: float, min_bri: int = 15, max_bri: int = 100) -> int:
    """Exponential brightness mapping — small volumes still visible, loud is dramatic."""
    volume = min(1.0, max(0.0, volume))
    curved = volume ** 0.45  # sqrt-ish curve: boosts low end, compresses high end
    return int(min_bri + curved * (max_bri - min_bri))


def _lerp_hue(h1: int, h2: int, t: float) -> int:
    """Interpolate between two hues via shortest path on the circle."""
    d = h2 - h1
    if d > 180:
        d -= 360
    elif d < -180:
        d += 360
    return int(h1 + d * t) % 360


class MusicVisualizer:
    """Drives bulb colors based on real-time audio features."""

    def __init__(self, controller: BulbController, mode: str = "spectrum") -> None:
        self.controller = controller
        self.mode = mode
        self._running = False
        self._last_command_time: dict[int, float] = {}
        self._last_hsv: dict[int, tuple[int, int, int]] = {}
        self._current_hsv: dict[int, tuple[int, int, int]] = {}
        self._beat_peak_time: dict[int, float] = {}
        self._pending_commands: dict[int, tuple] = {}
        self._base_hue: int = 240  # For pulse mode (default blue)
        self._smoothing: float = 0.35  # 0=instant, 1=frozen. 0.35 = snappy but smooth

    def set_mode(self, mode: str) -> None:
        """Change visualization mode."""
        self.mode = mode
        self._beat_peak_time.clear()
        logger.info("Visualizer mode set to: %s", mode)

    def set_base_hue(self, hue: int) -> None:
        """Set base hue for pulse mode."""
        self._base_hue = hue

    async def update(self, features: AudioFeatures) -> None:
        """Process audio features and update bulb colors."""
        if not self._running:
            return

        if self.mode == "spectrum":
            await self._mode_spectrum(features)
        elif self.mode == "energy":
            await self._mode_energy(features)
        elif self.mode == "pulse":
            await self._mode_pulse(features)
        elif self.mode == "dual":
            await self._mode_dual(features)
        elif self.mode == "complementary":
            await self._mode_complementary(features)
        elif self.mode == "chase":
            await self._mode_chase(features)
        elif self.mode == "sync":
            await self._mode_sync(features)

    # ------------------------------------------------------------------
    # Core send with smoothing, gamma, perceptual delta, and rate limit
    # ------------------------------------------------------------------

    async def _send_color(self, hue: int, sat: int, bri: int,
                          bulb_index: int | None = None, *, force: bool = False) -> None:
        """Send color command with smoothing, gamma, rate limiting, and delta check."""
        idx = bulb_index if bulb_index is not None else -1
        now = time.monotonic()

        # Rate limit
        if not force:
            last_time = self._last_command_time.get(idx, 0)
            if now - last_time < MIN_COMMAND_INTERVAL:
                return

        # Smooth interpolation toward target
        if idx in self._current_hsv and not force:
            cur = self._current_hsv[idx]
            hue = _lerp_hue(cur[0], hue, 1.0 - self._smoothing)
            sat = int(cur[1] + (sat - cur[1]) * (1.0 - self._smoothing))
            bri = int(cur[2] + (bri - cur[2]) * (1.0 - self._smoothing))

        # Gamma-correct brightness
        bri = _gamma(bri)

        # Perceptual delta check
        last_hsv = self._last_hsv.get(idx, (-999, -999, -999))
        if not force and _hsv_delta(last_hsv, (hue, sat, bri)) < COLOR_DELTA_THRESHOLD:
            return

        hue = hue % 360
        sat = max(0, min(100, sat))
        bri = max(1, min(100, bri))

        # Store prepared values for parallel send (if _send_parallel is used)
        self._pending_commands[idx] = (hue, sat, bri, bulb_index)

        await self.controller.set_color(hue, sat, bri, bulb_index)
        self._last_command_time[idx] = now
        self._last_hsv[idx] = (hue, sat, bri)
        self._current_hsv[idx] = (hue, sat, bri)

    def _prepare_color(self, hue: int, sat: int, bri: int,
                       bulb_index: int, *, force: bool = False) -> tuple[int, int, int] | None:
        """Prepare a color command (smoothing, gamma, delta) without sending.

        Returns (hue, sat, bri) if command should be sent, None if skipped.
        """
        idx = bulb_index
        now = time.monotonic()

        if not force:
            last_time = self._last_command_time.get(idx, 0)
            if now - last_time < MIN_COMMAND_INTERVAL:
                return None

        if idx in self._current_hsv and not force:
            cur = self._current_hsv[idx]
            hue = _lerp_hue(cur[0], hue, 1.0 - self._smoothing)
            sat = int(cur[1] + (sat - cur[1]) * (1.0 - self._smoothing))
            bri = int(cur[2] + (bri - cur[2]) * (1.0 - self._smoothing))

        bri = _gamma(bri)

        last_hsv = self._last_hsv.get(idx, (-999, -999, -999))
        if not force and _hsv_delta(last_hsv, (hue, sat, bri)) < COLOR_DELTA_THRESHOLD:
            return None

        hue = hue % 360
        sat = max(0, min(100, sat))
        bri = max(1, min(100, bri))

        self._last_command_time[idx] = now
        self._last_hsv[idx] = (hue, sat, bri)
        self._current_hsv[idx] = (hue, sat, bri)
        return (hue, sat, bri)

    async def _send_parallel(self, commands: list[tuple[int, int, int, int]],
                              *, force: bool = False) -> None:
        """Prepare and send color commands to multiple bulbs simultaneously.

        Args:
            commands: List of (hue, sat, bri, bulb_index).
        """
        prepared = []
        for hue, sat, bri, idx in commands:
            result = self._prepare_color(hue, sat, bri, idx, force=force)
            if result is not None:
                prepared.append((result[0], result[1], result[2], idx))

        if prepared:
            await self.controller.set_color_parallel(prepared)

    # ------------------------------------------------------------------
    # Beat helpers
    # ------------------------------------------------------------------

    def _register_beat(self, bulb_index: int | None = None) -> None:
        idx = bulb_index if bulb_index is not None else -1
        self._beat_peak_time[idx] = time.monotonic()

    def _beat_decay(self, bulb_index: int | None = None) -> float:
        """Return 1.0 at beat peak, decaying to 0.0 over BEAT_DECAY_S."""
        idx = bulb_index if bulb_index is not None else -1
        elapsed = time.monotonic() - self._beat_peak_time.get(idx, 0)
        if elapsed >= BEAT_DECAY_S:
            return 0.0
        progress = elapsed / BEAT_DECAY_S
        return 1.0 - progress ** 2  # ease-out curve

    # ------------------------------------------------------------------
    # Modes
    # ------------------------------------------------------------------

    async def _mode_spectrum(self, f: AudioFeatures) -> None:
        """Hue follows dominant frequency, brightness follows volume."""
        freq = f.dominant_frequency
        if freq < 250:
            hue = int(freq / 250 * 30)                                  # 0-30
        elif freq < 2000:
            hue = int(30 + (freq - 250) / 1750 * 90)                    # 30-120
        else:
            hue = int(120 + min(freq - 2000, 14000) / 14000 * 160)      # 120-280

        brightness = _exp_brightness(f.overall_volume)
        saturation = int(50 + f.overall_volume * 50)  # energy-responsive: 50-100

        if f.is_beat:
            self._register_beat()
        decay = self._beat_decay()
        if decay > 0:
            brightness = int(brightness + (100 - brightness) * decay)

        await self._send_color(hue % 360, saturation, brightness)

    async def _mode_energy(self, f: AudioFeatures) -> None:
        """Color shifts based on total energy; white flash on beats with decay."""
        energy = f.overall_volume

        if f.is_beat:
            self._register_beat()

        decay = self._beat_decay()

        if decay > 0.5:
            # Still in beat flash — bright white fading to color
            bri = int(60 + decay * 40)
            sat = int((1.0 - decay) * 90)
            await self._send_color(0, sat, bri, force=True)
            return

        # Normal energy-based color
        if energy < 0.3:
            hue = 240
            brightness = _exp_brightness(energy, min_bri=15, max_bri=50)
        elif energy < 0.6:
            hue = 160
            brightness = _exp_brightness(energy, min_bri=40, max_bri=75)
        else:
            hue = int(30 - energy * 30) % 360
            brightness = _exp_brightness(energy, min_bri=60, max_bri=100)

        saturation = int(50 + energy * 50)

        # Blend in remaining beat decay
        if decay > 0:
            brightness = int(brightness + (100 - brightness) * decay)

        await self._send_color(hue, saturation, brightness)

    async def _mode_pulse(self, f: AudioFeatures) -> None:
        """Single color that breathes with the bass."""
        bass = min(1.0, f.band_energies.get("bass", 0) + f.band_energies.get("sub_bass", 0))

        if f.is_beat:
            self._register_beat()

        decay = self._beat_decay()
        base_bri = _exp_brightness(bass, min_bri=10, max_bri=70)

        # Beat spike
        brightness = int(base_bri + (100 - base_bri) * decay)
        saturation = int(60 + bass * 40)  # more vivid when bass is strong

        await self._send_color(self._base_hue, saturation, brightness)

    async def _mode_dual(self, f: AudioFeatures) -> None:
        """Each bulb reacts to a different frequency range."""
        if len(self.controller.bulbs) < 2:
            await self._mode_spectrum(f)
            return

        if f.is_beat:
            self._register_beat(0)
            self._register_beat(1)

        decay0 = self._beat_decay(0)
        decay1 = self._beat_decay(1)

        # Bulb 0: bass + low-mids -> warm colors
        warm = min(1.0, (f.band_energies.get("bass", 0) + f.band_energies.get("low_mid", 0)) / 2)
        warm_hue = int(warm * 40)
        warm_bri = _exp_brightness(warm)
        warm_bri = int(warm_bri + (100 - warm_bri) * decay0)
        warm_sat = int(50 + warm * 50)

        # Bulb 1: high-mids + highs -> cool colors
        cool = min(1.0, (f.band_energies.get("high_mid", 0) + f.band_energies.get("high", 0)) / 2)
        cool_hue = int(200 + cool * 80)
        cool_bri = _exp_brightness(cool)
        cool_bri = int(cool_bri + (100 - cool_bri) * decay1)
        cool_sat = int(50 + cool * 50)

        await self._send_parallel([
            (warm_hue, warm_sat, warm_bri, 0),
            (cool_hue % 360, cool_sat, cool_bri, 1),
        ])

    async def _mode_complementary(self, f: AudioFeatures) -> None:
        """Both bulbs use complementary colors (180 degrees apart) for dramatic contrast."""
        if len(self.controller.bulbs) < 2:
            await self._mode_spectrum(f)
            return

        if f.is_beat:
            self._register_beat(0)
            self._register_beat(1)

        energy = f.overall_volume
        freq = f.dominant_frequency

        # Primary hue from frequency
        hue = int(freq / 16000 * 360) % 360
        brightness = _exp_brightness(energy)
        saturation = int(50 + energy * 50)

        decay0 = self._beat_decay(0)
        decay1 = self._beat_decay(1)

        bri0 = int(brightness + (100 - brightness) * decay0)
        bri1 = int(brightness + (100 - brightness) * decay1)

        await self._send_parallel([
            (hue, saturation, bri0, 0),
            ((hue + 180) % 360, saturation, bri1, 1),
        ])

    async def _mode_chase(self, f: AudioFeatures) -> None:
        """Bulbs alternate — one leads with bass, the other follows with a color offset."""
        if len(self.controller.bulbs) < 2:
            await self._mode_spectrum(f)
            return

        bass = min(1.0, f.band_energies.get("bass", 0) + f.band_energies.get("sub_bass", 0))
        high = min(1.0, f.band_energies.get("high_mid", 0) + f.band_energies.get("high", 0))

        if f.is_beat:
            self._register_beat(0)
            self._register_beat(1)

        decay0 = self._beat_decay(0)
        decay1 = self._beat_decay(1)

        hue_base = int(bass * 40)  # warm 0-40
        bri0 = _exp_brightness(bass)
        bri0 = int(bri0 + (100 - bri0) * decay0)

        bri1 = _exp_brightness(high)
        bri1 = int(bri1 + (100 - bri1) * decay1)

        await self._send_parallel([
            (hue_base, int(50 + bass * 50), bri0, 0),
            ((hue_base + 120) % 360, int(50 + high * 50), bri1, 1),
        ])

    async def _mode_sync(self, f: AudioFeatures) -> None:
        """Both bulbs show the same color, reacting together to the music.

        Combines all frequency bands into a rich color that evolves with the song:
        - Hue cycles through the full spectrum driven by the dominant frequency
        - Bass energy adds warmth (pulls hue toward red/orange)
        - High energy adds coolness (pulls hue toward blue/purple)
        - Brightness and saturation respond to overall energy + beats
        """
        if f.is_beat:
            for i in range(len(self.controller.bulbs)):
                self._register_beat(i)

        # Base hue from dominant frequency — full 360 range
        freq = f.dominant_frequency
        if freq < 150:
            hue = int(freq / 150 * 30)                                  # 0-30 deep red/orange
        elif freq < 400:
            hue = int(30 + (freq - 150) / 250 * 30)                     # 30-60 orange/yellow
        elif freq < 1000:
            hue = int(60 + (freq - 400) / 600 * 60)                     # 60-120 yellow/green
        elif freq < 3000:
            hue = int(120 + (freq - 1000) / 2000 * 80)                  # 120-200 green/cyan
        else:
            hue = int(200 + min(freq - 3000, 13000) / 13000 * 120)      # 200-320 blue/purple

        # Blend in bass warmth and high coolness
        bass = f.band_energies.get("bass", 0) + f.band_energies.get("sub_bass", 0)
        highs = f.band_energies.get("high_mid", 0) + f.band_energies.get("high", 0)
        bass = min(1.0, bass)
        highs = min(1.0, highs)

        # Bass pulls toward red (hue 0-20), highs pull toward blue (hue 220-260)
        hue_shift = int(-bass * 30 + highs * 40)
        hue = (hue + hue_shift) % 360

        # Brightness from overall energy with exponential curve
        brightness = _exp_brightness(f.overall_volume)

        # Saturation: more vivid when louder, softer when quiet
        saturation = int(40 + f.overall_volume * 60)  # 40-100

        # Apply beat decay and send to all bulbs simultaneously
        commands = []
        for i in range(len(self.controller.bulbs)):
            decay = self._beat_decay(i)
            bri = int(brightness + (100 - brightness) * decay)
            sat = int(saturation + (100 - saturation) * decay * 0.5)
            commands.append((hue, sat, bri, i))
        await self._send_parallel(commands)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Enable the visualizer."""
        self._running = True
        logger.info("Visualizer started in '%s' mode", self.mode)

    def stop(self) -> None:
        """Disable the visualizer."""
        self._running = False
        self._last_command_time.clear()
        self._last_hsv.clear()
        self._current_hsv.clear()
        self._beat_peak_time.clear()
        logger.info("Visualizer stopped")
