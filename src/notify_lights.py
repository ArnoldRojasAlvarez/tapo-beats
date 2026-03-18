"""Notification lights — flash bulbs on Windows notifications."""

import asyncio
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Notification color map (hue, saturation)
_APP_COLORS = {
    "whatsapp": (130, 90),    # green
    "discord": (235, 80),     # purple-blue
    "outlook": (210, 90),     # blue
    "mail": (210, 90),        # blue
    "teams": (250, 70),       # purple
    "telegram": (200, 85),    # light blue
    "slack": (340, 80),       # pinkish
    "chrome": (45, 90),       # yellow-orange
    "edge": (210, 90),        # blue
    "default": (50, 90),      # orange
}


class NotifyLights:
    """Monitors Windows notifications and flashes bulbs."""

    def __init__(self, controller, loop: asyncio.AbstractEventLoop):
        self._controller = controller
        self._loop = loop
        self._running = False
        self._thread: threading.Thread | None = None
        self._flash_queue: list[tuple[int, int]] = []
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start notification monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Notification lights started")

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("Notification lights stopped")

    def flash(self, app_name: str = "default") -> None:
        """Queue a flash for a specific app."""
        app_key = app_name.lower()
        color = _APP_COLORS.get(app_key, _APP_COLORS["default"])
        with self._lock:
            self._flash_queue.append(color)

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=5)

    def _monitor_loop(self) -> None:
        """Process flash queue."""
        while self._running:
            flash = None
            with self._lock:
                if self._flash_queue:
                    flash = self._flash_queue.pop(0)

            if flash:
                self._do_flash(flash[0], flash[1])
            else:
                time.sleep(0.2)

    def _do_flash(self, hue: int, sat: int) -> None:
        """Execute a 3-pulse flash effect."""
        try:
            # Save current state
            states = self._run_async(self._controller.get_state())
            was_on = [s.is_on for s in states]
            old_colors = [(s.hue, s.saturation, s.brightness) for s in states]

            # Flash 3 times
            for _ in range(3):
                self._run_async(self._controller.turn_on())
                self._run_async(self._controller.set_color(hue, sat, 100))
                time.sleep(0.15)
                self._run_async(self._controller.set_color(hue, sat, 10))
                time.sleep(0.15)

            # Restore previous state
            for i, (h, s, b) in enumerate(old_colors):
                if was_on[i]:
                    self._run_async(self._controller.set_color(h, s, b, i))
                else:
                    self._run_async(self._controller.turn_off(i))

        except Exception:
            logger.exception("Flash error")
