"""Notification lights — flash bulbs when windows request attention in taskbar."""

import asyncio
import ctypes
import ctypes.wintypes
import logging
import threading
import time
import subprocess

logger = logging.getLogger(__name__)

# App color map: window title/process keyword -> (hue, saturation)
_APP_COLORS = {
    "discord": (235, 80),
    "whatsapp": (130, 90),
    "outlook": (210, 90),
    "mail": (210, 90),
    "teams": (250, 70),
    "telegram": (200, 85),
    "slack": (340, 80),
    "chrome": (45, 90),
    "edge": (210, 90),
    "spotify": (130, 90),
    "steam": (210, 60),
}

_DEFAULT_COLOR = (50, 90)

_user32 = ctypes.windll.user32


class NotifyLights:
    """Monitors taskbar for flashing windows and flashes bulbs."""

    def __init__(self, controller, loop: asyncio.AbstractEventLoop):
        self._controller = controller
        self._loop = loop
        self._running = False
        self._thread: threading.Thread | None = None
        self._flash_lock = threading.Lock()
        self._cooldown: dict[int, float] = {}

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._cooldown.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Notification lights started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("Notification lights stopped")

    def flash(self, app_name: str = "default") -> None:
        """Trigger a flash for a specific app."""
        hue, sat = self._match_color(app_name)
        threading.Thread(target=self._do_flash, args=(hue, sat), daemon=True).start()

    def _match_color(self, app_name: str) -> tuple[int, int]:
        app_key = app_name.lower()
        for keyword, color in _APP_COLORS.items():
            if keyword in app_key:
                return color
        return _DEFAULT_COLOR

    def _monitor_loop(self) -> None:
        """Use PowerShell to poll for flashing taskbar buttons."""
        while self._running:
            try:
                self._check_flashing_ps()
            except Exception:
                logger.exception("Notification monitor error")
            time.sleep(2.0)

    def _check_flashing_ps(self) -> None:
        """Use PowerShell to find windows requesting attention via taskbar flash."""
        now = time.monotonic()
        # PowerShell script to find flashing windows
        # Uses Windows accessibility to detect taskbar button flash state
        ps_script = '''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class FlashCheck {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool FlashWindowEx(ref FLASHWINFO pwfi);

    [StructLayout(LayoutKind.Sequential)]
    public struct FLASHWINFO {
        public uint cbSize;
        public IntPtr hwnd;
        public uint dwFlags;
        public uint uCount;
        public uint dwTimeout;
    }

    // FLASHW_STOP = 0, FLASHW_TIMER = 4
    public static bool IsFlashing(IntPtr hwnd) {
        FLASHWINFO info = new FLASHWINFO();
        info.cbSize = (uint)Marshal.SizeOf(info);
        info.hwnd = hwnd;
        info.dwFlags = 0; // FLASHW_STOP - this stops flashing and returns previous state
        info.uCount = 0;
        info.dwTimeout = 0;
        return FlashWindowEx(ref info);
    }
}
"@
$fg = [FlashCheck]::GetForegroundWindow()
Get-Process | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero -and $_.MainWindowHandle -ne $fg } | ForEach-Object {
    try {
        if ([FlashCheck]::IsFlashing($_.MainWindowHandle)) {
            Write-Output "$($_.Id)|$($_.ProcessName)|$($_.MainWindowTitle)"
        }
    } catch {}
}
'''
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    parts = line.strip().split('|', 2)
                    if len(parts) >= 2:
                        pid = int(parts[0])
                        proc_name = parts[1]
                        title = parts[2] if len(parts) > 2 else proc_name

                        # Cooldown: 15 seconds per process
                        last = self._cooldown.get(pid, 0)
                        if now - last > 15:
                            self._cooldown[pid] = now
                            logger.info("Flashing app detected: %s ('%s')", proc_name, title)
                            self.flash(proc_name)
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            logger.exception("PowerShell flash check error")

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=5)

    def _do_flash(self, hue: int, sat: int) -> None:
        """Execute a 3-pulse flash effect, thread-safe."""
        if not self._flash_lock.acquire(blocking=False):
            return
        try:
            states = self._run_async(self._controller.get_state())
            was_on = [s.is_on for s in states]
            old_colors = [(s.hue, s.saturation, s.brightness) for s in states]

            for _ in range(3):
                self._run_async(self._controller.turn_on())
                self._run_async(self._controller.set_color(hue, sat, 100))
                time.sleep(0.15)
                self._run_async(self._controller.set_color(hue, sat, 10))
                time.sleep(0.15)

            for i, (h, s, b) in enumerate(old_colors):
                if was_on[i]:
                    self._run_async(self._controller.set_color(h, s, b, i))
                else:
                    self._run_async(self._controller.turn_off(i))

        except Exception:
            logger.exception("Flash error")
        finally:
            self._flash_lock.release()
