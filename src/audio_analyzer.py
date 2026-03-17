"""FFT-based audio analysis with frequency band extraction and beat detection."""

import logging
from collections import deque
from dataclasses import dataclass

import numpy as np

DEFAULT_SAMPLE_RATE = 44100

logger = logging.getLogger(__name__)

# Frequency band definitions (Hz)
BANDS = {
    "sub_bass":  (20, 60),
    "bass":      (60, 250),
    "low_mid":   (250, 500),
    "mid":       (500, 2000),
    "high_mid":  (2000, 4000),
    "high":      (4000, 16000),
}

# Beat detection settings
BEAT_HISTORY_SIZE = 43  # ~1 second at 43 Hz analysis rate
BEAT_THRESHOLD_MULTIPLIER = 1.4


@dataclass
class AudioFeatures:
    """Analyzed audio features from a single chunk."""
    band_energies: dict[str, float]  # 0.0-1.0 per band
    overall_volume: float            # 0.0-1.0
    is_beat: bool
    beat_intensity: float            # 0.0-1.0
    dominant_frequency: float        # Hz


class AudioAnalyzer:
    """Performs FFT analysis and beat detection on audio chunks."""

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
        self._sample_rate = sample_rate
        self._bass_history: deque[float] = deque(maxlen=BEAT_HISTORY_SIZE)
        self._max_energy: float = 1e-6  # For normalization, avoid div-by-zero

    def analyze(self, audio_chunk: np.ndarray) -> AudioFeatures:
        """Analyze a raw audio chunk and return extracted features.

        Args:
            audio_chunk: Mono float32 audio samples.

        Returns:
            AudioFeatures with band energies, volume, beat info.
        """
        # FFT
        fft_data = np.fft.rfft(audio_chunk)
        magnitudes = np.abs(fft_data)
        freqs = np.fft.rfftfreq(len(audio_chunk), 1.0 / self._sample_rate)

        # Calculate energy per frequency band
        raw_energies: dict[str, float] = {}
        for band_name, (low, high) in BANDS.items():
            mask = (freqs >= low) & (freqs < high)
            band_mags = magnitudes[mask]
            if len(band_mags) > 0:
                raw_energies[band_name] = float(np.sqrt(np.mean(band_mags ** 2)))  # RMS
            else:
                raw_energies[band_name] = 0.0

        # Track max energy for normalization
        max_raw = max(raw_energies.values()) if raw_energies else 0.0
        self._max_energy = max(self._max_energy, max_raw, 1e-6)
        # Slow decay of max to adapt to volume changes
        self._max_energy *= 0.999

        # Normalize band energies to 0.0-1.0
        band_energies = {
            name: min(1.0, val / self._max_energy)
            for name, val in raw_energies.items()
        }

        # Overall volume (RMS of raw audio)
        overall_volume = float(np.sqrt(np.mean(audio_chunk ** 2)))
        overall_volume = min(1.0, overall_volume * 10)  # Scale up for visibility

        # Beat detection: compare current bass energy to rolling average
        bass_energy = raw_energies.get("bass", 0.0) + raw_energies.get("sub_bass", 0.0)
        self._bass_history.append(bass_energy)
        avg_bass = np.mean(self._bass_history) if self._bass_history else 0.0

        is_beat = bass_energy > avg_bass * BEAT_THRESHOLD_MULTIPLIER and bass_energy > 0.01
        beat_intensity = min(1.0, (bass_energy / (avg_bass + 1e-6)) - 1.0) if is_beat else 0.0

        # Dominant frequency (frequency with highest magnitude, ignoring DC)
        if len(magnitudes) > 1:
            peak_idx = np.argmax(magnitudes[1:]) + 1
            dominant_frequency = float(freqs[peak_idx])
        else:
            dominant_frequency = 0.0

        return AudioFeatures(
            band_energies=band_energies,
            overall_volume=overall_volume,
            is_beat=is_beat,
            beat_intensity=beat_intensity,
            dominant_frequency=dominant_frequency,
        )
