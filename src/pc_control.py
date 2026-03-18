"""PC control module — execute system actions via voice commands."""

import logging
import subprocess

logger = logging.getLogger(__name__)

# App launch commands (Windows)
_APPS = {
    "spotify": "explorer shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
    "crunchyroll": "explorer shell:AppsFolder\\15EF7777.Crunchyroll_mgdgtskya6f22!App",
    "whatsapp": "explorer shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "outlook": "explorer shell:AppsFolder\\Microsoft.OutlookForWindows_8wekyb3d8bbwe!Microsoft.OutlookforWindows",
    "steam": "start steam://open/main",
    "wallpaper": "start steam://rungameid/431960",
    "youtube": "start msedge https://www.youtube.com",
}


def execute_pc_command(action: str) -> str:
    """Execute a PC control command and return a speech response."""
    action = action.lower().strip()
    logger.info("PC command: '%s'", action)

    try:
        # Power commands
        if action == "shutdown":
            subprocess.Popen("shutdown /s /t 5", shell=True)
            return "Apagando la PC en 5 segundos"
        elif action == "restart":
            subprocess.Popen("shutdown /r /t 5", shell=True)
            return "Reiniciando la PC en 5 segundos"
        elif action == "sleep":
            subprocess.Popen(
                "rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True
            )
            return "Suspendiendo la PC"
        elif action == "lock":
            subprocess.Popen(
                "rundll32.exe user32.dll,LockWorkStation", shell=True
            )
            return "PC bloqueada"
        elif action == "cancel_shutdown":
            subprocess.Popen("shutdown /a", shell=True)
            return "Apagado cancelado"
        elif action == "screen_off":
            _turn_off_screen()
            return "Pantalla apagada"
        elif action == "screen_on":
            _turn_on_screen()
            return "Pantalla encendida"

        # Volume commands
        elif action == "mute":
            _send_media_key(0xAD)  # VK_VOLUME_MUTE
            return "Volumen muteado"
        elif action == "volume_up":
            for _ in range(5):
                _send_media_key(0xAF)  # VK_VOLUME_UP
            return "Volumen subido"
        elif action == "volume_down":
            for _ in range(5):
                _send_media_key(0xAE)  # VK_VOLUME_DOWN
            return "Volumen bajado"

        # App launch commands
        elif action in _APPS:
            subprocess.Popen(_APPS[action], shell=True)
            return f"{action.capitalize()} abierto"

        else:
            return f"Comando de PC no reconocido: {action}"

    except Exception:
        logger.exception("Error executing PC command: %s", action)
        return f"Error ejecutando: {action}"


def _turn_off_screen() -> None:
    """Turn off the monitor (PC stays running)."""
    import ctypes
    SC_MONITORPOWER = 0xF170
    HWND_BROADCAST = 0xFFFF
    WM_SYSCOMMAND = 0x0112
    ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)


def _turn_on_screen() -> None:
    """Turn on the monitor by simulating mouse movement."""
    import ctypes
    ctypes.windll.user32.mouse_event(0x0001, 1, 0, 0, 0)  # MOUSEEVENTF_MOVE
    ctypes.windll.user32.mouse_event(0x0001, -1, 0, 0, 0)


def _send_media_key(vk_code: int) -> None:
    """Send a media key press using ctypes (Windows)."""
    import ctypes
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
