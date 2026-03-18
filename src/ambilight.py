"""Ambilight module — sync bulb colors with screen content in real-time."""

import asyncio
import logging
import threading
import time
from colorsys import rgb_to_hsv

import mss
import numpy as np

logger = logging.getLogger(__name__)

# Screen capture settings
_CAPTURE_FPS = 10  # captures per second
_RESIZE_W = 40     # downscale for speed
_RESIZE_H = 22


class Ambilight:
    """Captures dominant screen colors and applies them to bulbs."""

    def __init__(self, controller, loop: asyncio.AbstractEventLoop):
        self._controller = controller
        self._loop = loop
        self._running = False
        self._thread: threading.Thread | None = None
        self._zones = "split"  # "split" = left/right, "average" = same color

    @property
    def running(self) -> bool:
        return self._running

    @property
    def zones(self) -> str:
        return self._zones

    def set_zones(self, mode: str) -> None:
        """Set zone mode: 'split' (left/right bulb) or 'average' (same color)."""
        if mode in ("split", "average"):
            self._zones = mode

    def start(self) -> None:
        """Start ambilight capture in background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Ambilight started (zones=%s)", self._zones)

    def stop(self) -> None:
        """Stop ambilight capture."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("Ambilight stopped")

    def _capture_loop(self) -> None:
        """Main capture loop running in a daemon thread."""
        interval = 1.0 / _CAPTURE_FPS
        last_hsv = {}

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor

            while self._running:
                start = time.monotonic()
                try:
                    # Capture screen
                    img = sct.grab(monitor)
                    pixels = np.frombuffer(img.rgb, dtype=np.uint8).reshape(
                        img.height, img.width, 3
                    )

                    # Downscale by slicing (fast, no PIL needed)
                    step_h = max(1, img.height // _RESIZE_H)
                    step_w = max(1, img.width // _RESIZE_W)
                    small = pixels[::step_h, ::step_w]

                    if self._zones == "split":
                        mid = small.shape[1] // 2
                        left = small[:, :mid]
                        right = small[:, mid:]
                        hsv_left = _dominant_hsv(left)
                        hsv_right = _dominant_hsv(right)
                        colors = [hsv_left, hsv_right]
                    else:
                        hsv_avg = _dominant_hsv(small)
                        colors = [hsv_avg, hsv_avg]

                    # Only send if color changed significantly
                    changed = False
                    for i, (h, s, b) in enumerate(colors):
                        prev = last_hsv.get(i)
                        if prev is None or _color_diff(prev, (h, s, b)) > 8:
                            last_hsv[i] = (h, s, b)
                            changed = True

                    if changed:
                        self._send_colors(colors)

                except Exception:
                    logger.exception("Ambilight capture error")

                elapsed = time.monotonic() - start
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def _send_colors(self, colors: list[tuple[int, int, int]]) -> None:
        """Send colors to bulbs asynchronously."""
        num_bulbs = len(self._controller.bulbs)
        for i, (h, s, b) in enumerate(colors):
            if i >= num_bulbs:
                break
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._controller.set_color(h, s, max(b, 5), i),
                    self._loop,
                )
                future.result(timeout=2)
            except Exception:
                pass  # Don't crash loop on send errors


def _dominant_hsv(pixels: np.ndarray) -> tuple[int, int, int]:
    """Get the dominant HSV color from a region of pixels.

    Uses weighted average biased toward saturated colors.
    """
    flat = pixels.reshape(-1, 3).astype(np.float32) / 255.0

    # Convert to HSV per pixel
    r, g, b = flat[:, 0], flat[:, 1], flat[:, 2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    diff = maxc - minc

    # Saturation
    sat = np.where(maxc > 0, diff / maxc, 0)

    # Weight: prefer saturated, bright pixels (ignore dark/gray)
    weights = sat * maxc
    weights = weights + 0.01  # avoid division by zero

    # Weighted average RGB
    total_w = weights.sum()
    avg_r = (r * weights).sum() / total_w
    avg_g = (g * weights).sum() / total_w
    avg_b = (b * weights).sum() / total_w

    # Convert to HSV
    h, s, v = rgb_to_hsv(float(avg_r), float(avg_g), float(avg_b))

    # Map to Tapo ranges: hue 0-360, sat 0-100, brightness 0-100
    return int(h * 360) % 360, int(s * 100), int(v * 100)


def _color_diff(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Calculate color difference (simple hue + sat + brightness)."""
    hue_diff = min(abs(a[0] - b[0]), 360 - abs(a[0] - b[0]))
    return hue_diff * 0.5 + abs(a[1] - b[1]) * 0.3 + abs(a[2] - b[2]) * 0.2
