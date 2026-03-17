"""Voice control module for TapoBeats using Vosk offline speech recognition."""

import json
import logging
import queue
import threading
import time
from typing import Callable

import pyaudio
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)

# Microphone settings
MIC_RATE = 16000
MIC_CHANNELS = 1
MIC_CHUNK = 4000  # ~250ms at 16kHz

# Command mapping: keywords -> (action_type, action_value)
# Supports both English and Spanish keywords
COMMANDS = {
    # Music modes
    "spectrum": ("music_mode", "spectrum"),
    "energy": ("music_mode", "energy"),
    "pulse": ("music_mode", "pulse"),
    "dual": ("music_mode", "dual"),
    "complementary": ("music_mode", "complementary"),
    "chase": ("music_mode", "chase"),
    "sync": ("music_mode", "sync"),
    "sincronizar": ("music_mode", "sync"),
    # Music control
    "start music": ("music_start", None),
    "iniciar musica": ("music_start", None),
    "empezar musica": ("music_start", None),
    "stop music": ("music_stop", None),
    "parar musica": ("music_stop", None),
    "detener musica": ("music_stop", None),
    "stop": ("music_stop", None),
    "para": ("music_stop", None),
    # Scenes
    "chill": ("scene", "Chill"),
    "party": ("scene", "Party"),
    "fiesta": ("scene", "Party"),
    "gaming": ("scene", "Gaming"),
    "movie": ("scene", "Movie"),
    "pelicula": ("scene", "Movie"),
    "sunset": ("scene", "Sunset"),
    "focus": ("scene", "Focus"),
    "enfoque": ("scene", "Focus"),
    "sex": ("scene", "Sex"),
    "sexy": ("scene", "Sex"),
    # Power
    "turn on": ("power", "on"),
    "turn off": ("power", "off"),
    "encender": ("power", "on"),
    "apagar": ("power", "off"),
    "prender": ("power", "on"),
    "lights on": ("power", "on"),
    "lights off": ("power", "off"),
    "luces": ("power", "on"),
    # PC control
    "apagar pc": ("pc", "shutdown"),
    "shutdown pc": ("pc", "shutdown"),
    "reiniciar": ("pc", "restart"),
    "restart": ("pc", "restart"),
    "suspender": ("pc", "sleep"),
    "dormir": ("pc", "sleep"),
    "bloquear": ("pc", "lock"),
    "lock": ("pc", "lock"),
    "mutear": ("pc", "mute"),
    "mute": ("pc", "mute"),
    "subir volumen": ("pc", "volume_up"),
    "bajar volumen": ("pc", "volume_down"),
    "abrir spotify": ("pc", "spotify"),
    "open spotify": ("pc", "spotify"),
    "abrir crunchyroll": ("pc", "crunchyroll"),
    "abrir whatsapp": ("pc", "whatsapp"),
    "abrir outlook": ("pc", "outlook"),
    "abrir correo": ("pc", "outlook"),
    "abrir steam": ("pc", "steam"),
    "abrir youtube": ("pc", "youtube"),
}

# Multi-word commands sorted by length (longest first for greedy matching)
_SORTED_COMMANDS = sorted(COMMANDS.keys(), key=len, reverse=True)


def _find_mic_device(p: pyaudio.PyAudio) -> int | None:
    """Find the SteelSeries Sonar Microphone or best available input device."""
    best = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] < 1:
            continue
        name = info["name"].lower()
        # Prefer SteelSeries Sonar Microphone (routes through Razer)
        if "sonar" in name and "microphone" in name and "stream" not in name:
            logger.info("Using mic: [%d] %s", i, info["name"])
            return i
        # Fallback: Razer BlackShark directly
        if "razer" in name and "blackshark" in name and best is None:
            best = i
    if best is not None:
        info = p.get_device_info_by_index(best)
        logger.info("Using mic (fallback): [%d] %s", best, info["name"])
    return best


class VoiceControl:
    """Listens for voice commands via microphone using Vosk offline recognition."""

    def __init__(self, action_callback: Callable[[str, str | None], None]) -> None:
        self.action_callback = action_callback
        self._running = False
        self._thread: threading.Thread | None = None
        self._model_es: Model | None = None
        self._model_en: Model | None = None

    def _load_models(self) -> None:
        """Load Vosk models (lazy, first use only)."""
        if self._model_es is None:
            logger.info("Loading Spanish voice model...")
            self._model_es = Model(model_name="vosk-model-small-es-0.42")
            logger.info("Spanish model loaded")
        if self._model_en is None:
            logger.info("Loading English voice model...")
            self._model_en = Model(model_name="vosk-model-small-en-us-0.15")
            logger.info("English model loaded")

    def start(self) -> None:
        """Start listening for voice commands in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Voice control started - listening for commands")

    def stop(self) -> None:
        """Stop listening."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Voice control stopped")

    def _listen_loop(self) -> None:
        """Continuously listen for voice commands using Vosk."""
        try:
            self._load_models()
        except Exception:
            logger.exception("Failed to load voice models")
            self._running = False
            return

        p = pyaudio.PyAudio()
        mic_index = _find_mic_device(p)

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=MIC_CHANNELS,
                rate=MIC_RATE,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=MIC_CHUNK,
            )
        except Exception:
            logger.exception("Failed to open microphone")
            p.terminate()
            self._running = False
            return

        # Create recognizers for both languages
        rec_es = KaldiRecognizer(self._model_es, MIC_RATE)
        rec_en = KaldiRecognizer(self._model_en, MIC_RATE)

        logger.info("Voice control ready! Say a command (party, sync, stop, etc.)")

        while self._running:
            try:
                data = stream.read(MIC_CHUNK, exception_on_overflow=False)
            except Exception:
                logger.exception("Mic read error")
                time.sleep(0.5)
                continue

            # Feed to both recognizers
            es_done = rec_es.AcceptWaveform(data)
            en_done = rec_en.AcceptWaveform(data)

            # Check Spanish result
            if es_done:
                result = json.loads(rec_es.Result())
                text = result.get("text", "").strip()
                if text:
                    logger.info("Heard (ES): '%s'", text)
                    if self._match_command(text):
                        # Reset both recognizers after a match
                        rec_es = KaldiRecognizer(self._model_es, MIC_RATE)
                        rec_en = KaldiRecognizer(self._model_en, MIC_RATE)
                        continue

            # Check English result
            if en_done:
                result = json.loads(rec_en.Result())
                text = result.get("text", "").strip()
                if text:
                    logger.info("Heard (EN): '%s'", text)
                    if self._match_command(text):
                        rec_es = KaldiRecognizer(self._model_es, MIC_RATE)
                        rec_en = KaldiRecognizer(self._model_en, MIC_RATE)
                        continue

        stream.stop_stream()
        stream.close()
        p.terminate()
        logger.info("Voice control listener stopped")

    def _match_command(self, text: str) -> bool:
        """Try to match recognized text to a command."""
        text = text.strip().lower()

        for keyword in _SORTED_COMMANDS:
            if keyword in text:
                action_type, action_value = COMMANDS[keyword]
                logger.info(
                    "Command matched: '%s' -> %s(%s)", keyword, action_type, action_value
                )
                try:
                    self.action_callback(action_type, action_value)
                except Exception:
                    logger.exception("Error executing voice command")
                return True

        logger.debug("No command matched for: '%s'", text)
        return False
