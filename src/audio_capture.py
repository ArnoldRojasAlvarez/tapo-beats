"""System audio loopback capture using WASAPI on Windows via PyAudioWPatch."""

import logging
import threading
from typing import Callable

import numpy as np

logger = logging.getLogger(__name__)

# Audio capture settings
SAMPLE_RATE = 44100
CHANNELS = 2
BLOCK_SIZE = 2048
DTYPE = np.float32
FORMAT_PYAUDIO = 8  # paFloat32


class AudioCapture:
    """Captures system audio output via WASAPI loopback using PyAudioWPatch."""

    def __init__(self, callback: Callable[[np.ndarray], None]) -> None:
        """Initialize audio capture.

        Args:
            callback: Function called with each audio chunk (numpy float32 array).
        """
        self.callback = callback
        self._stream = None
        self._pyaudio = None
        self._running = False
        self._thread: threading.Thread | None = None

    def _find_loopback_device(self, p) -> dict:
        """Find the WASAPI loopback device for the default output."""
        # Get default WASAPI output device
        default_output = p.get_default_wasapi_loopback()
        if default_output:
            logger.info(
                "Found WASAPI loopback: [%d] %s (%d ch, %d Hz)",
                default_output["index"],
                default_output["name"],
                default_output["maxInputChannels"],
                int(default_output["defaultSampleRate"]),
            )
            return default_output

        raise RuntimeError(
            "No WASAPI loopback device found. Ensure audio is playing through "
            "a Windows audio output device."
        )

    def start(self) -> None:
        """Start capturing system audio."""
        import pyaudiowpatch as pyaudio

        self._pyaudio = pyaudio.PyAudio()
        loopback = self._find_loopback_device(self._pyaudio)

        channels = loopback["maxInputChannels"]
        sample_rate = int(loopback["defaultSampleRate"])

        self._stream = self._pyaudio.open(
            format=pyaudio.paFloat32,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=loopback["index"],
            frames_per_buffer=BLOCK_SIZE,
            stream_callback=self._pyaudio_callback,
        )
        self._running = True
        self._channels = channels
        self.sample_rate = sample_rate
        self._stream.start_stream()
        logger.info(
            "Audio capture started (device %d, %d ch, %d Hz)",
            loopback["index"], channels, sample_rate,
        )

    def _pyaudio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio stream callback."""
        import pyaudiowpatch as pyaudio

        if not self._running:
            return (None, pyaudio.paComplete)

        # Convert raw bytes to numpy float32 array
        audio_data = np.frombuffer(in_data, dtype=np.float32)

        # Reshape to (frames, channels) and convert to mono
        if self._channels > 1:
            audio_data = audio_data.reshape(-1, self._channels)
            mono = np.mean(audio_data, axis=1)
        else:
            mono = audio_data

        self.callback(mono.copy())
        return (None, pyaudio.paContinue)

    def stop(self) -> None:
        """Stop capturing audio."""
        self._running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
        logger.info("Audio capture stopped")
