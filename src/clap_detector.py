"""Clap detection module — detect double claps to toggle lights."""

import logging
import threading
import time

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

# Detection parameters
_SAMPLE_RATE = 44100
_BLOCK_SIZE = 1024
_CLAP_THRESHOLD = 0.35      # amplitude threshold for a clap
_CLAP_MIN_GAP = 0.1         # min seconds between two claps
_CLAP_MAX_GAP = 0.5         # max seconds between two claps
_COOLDOWN = 1.5             # seconds to wait after triggering


class ClapDetector:
    """Detects double claps via microphone to trigger actions."""

    def __init__(self, callback=None):
        self._callback = callback  # called on double clap
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_clap_time = 0.0
        self._last_trigger_time = 0.0
        self._stream = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start listening for claps."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        logger.info("Clap detector started")

    def stop(self) -> None:
        """Stop listening."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("Clap detector stopped")

    def _listen(self) -> None:
        """Audio capture loop."""
        try:
            self._stream = sd.InputStream(
                samplerate=_SAMPLE_RATE,
                blocksize=_BLOCK_SIZE,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            while self._running:
                time.sleep(0.1)
        except Exception:
            logger.exception("Clap detector error")
        finally:
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass

    def _audio_callback(self, indata, frames, time_info, status):
        """Process audio block looking for clap-like transients."""
        if not self._running:
            return

        amplitude = np.abs(indata).max()

        if amplitude > _CLAP_THRESHOLD:
            now = time.monotonic()

            # Cooldown after trigger
            if now - self._last_trigger_time < _COOLDOWN:
                return

            gap = now - self._last_clap_time

            if _CLAP_MIN_GAP < gap < _CLAP_MAX_GAP:
                # Double clap detected!
                logger.info("Double clap detected! (gap=%.2fs)", gap)
                self._last_trigger_time = now
                self._last_clap_time = 0
                if self._callback:
                    try:
                        self._callback()
                    except Exception:
                        logger.exception("Clap callback error")
            else:
                self._last_clap_time = now
