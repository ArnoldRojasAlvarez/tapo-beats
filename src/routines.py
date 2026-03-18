"""Routines module — sleep/wake gradual lighting transitions."""

import asyncio
import logging
import threading
import time

from .pc_control import execute_pc_command

logger = logging.getLogger(__name__)


class RoutineManager:
    """Manages gradual lighting routines (sleep, wake, etc.)."""

    def __init__(self, controller, loop: asyncio.AbstractEventLoop):
        self._controller = controller
        self._loop = loop
        self._active_routine: str | None = None
        self._cancel = False
        self._thread: threading.Thread | None = None

    @property
    def active(self) -> str | None:
        return self._active_routine

    def sleep_routine(self, duration_min: int = 15, suspend_pc: bool = True) -> str:
        """Gradually dim lights over duration, then turn off and optionally suspend PC."""
        if self._active_routine:
            return f"Rutina '{self._active_routine}' ya esta activa"
        self._cancel = False
        self._active_routine = "sleep"
        self._thread = threading.Thread(
            target=self._run_sleep, args=(duration_min, suspend_pc), daemon=True
        )
        self._thread.start()
        return f"Buenas noches. Luces se apagan en {duration_min} minutos"

    def wake_routine(self, duration_min: int = 5) -> str:
        """Gradually brighten lights simulating sunrise."""
        if self._active_routine:
            return f"Rutina '{self._active_routine}' ya esta activa"
        self._cancel = False
        self._active_routine = "wake"
        self._thread = threading.Thread(
            target=self._run_wake, args=(duration_min,), daemon=True
        )
        self._thread.start()
        return f"Buenos dias. Amanecer en {duration_min} minutos"

    def cancel(self) -> str:
        """Cancel active routine."""
        if not self._active_routine:
            return "No hay rutina activa"
        name = self._active_routine
        self._cancel = True
        self._active_routine = None
        return f"Rutina '{name}' cancelada"

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=10)

    def _run_sleep(self, duration_min: int, suspend_pc: bool) -> None:
        """Sleep routine: warm color, gradually dim, then off."""
        steps = 20
        interval = (duration_min * 60) / steps

        try:
            # Start with warm orange, medium brightness
            self._run_async(self._controller.turn_on())
            self._run_async(self._controller.set_color(30, 80, 50))
            time.sleep(1)

            for step in range(steps):
                if self._cancel:
                    return
                brightness = max(1, int(50 * (1 - step / steps)))
                # Shift hue from warm orange (30) to deep red (0)
                hue = max(0, int(30 * (1 - step / steps)))
                self._run_async(self._controller.set_color(hue, 80, brightness))
                time.sleep(interval)

            if self._cancel:
                return

            # Turn off lights
            self._run_async(self._controller.turn_off())
            logger.info("Sleep routine: lights off")

            # Turn off screen (PC stays running so server keeps working)
            if suspend_pc:
                time.sleep(3)
                execute_pc_command("screen_off")
                logger.info("Sleep routine: screen off, server still running")

        except Exception:
            logger.exception("Sleep routine error")
        finally:
            self._active_routine = None

    def _run_wake(self, duration_min: int) -> None:
        """Wake routine: simulate sunrise from deep red to bright daylight."""
        steps = 20
        interval = (duration_min * 60) / steps

        try:
            # Start very dim red
            self._run_async(self._controller.turn_on())
            self._run_async(self._controller.set_color(0, 90, 1))
            time.sleep(1)

            for step in range(steps):
                if self._cancel:
                    return
                progress = step / steps
                # Hue: red(0) -> orange(30) -> warm white(40)
                hue = int(40 * progress)
                # Saturation: very saturated -> less saturated
                sat = max(20, int(90 * (1 - progress * 0.7)))
                # Brightness: dim -> bright
                brightness = max(1, int(100 * progress))
                self._run_async(self._controller.set_color(hue, sat, brightness))
                time.sleep(interval)

            if self._cancel:
                return

            # Final: bright warm daylight
            self._run_async(self._controller.set_color(40, 30, 100))
            logger.info("Wake routine: sunrise complete")

        except Exception:
            logger.exception("Wake routine error")
        finally:
            self._active_routine = None
