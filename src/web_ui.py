"""Flask web UI for manual bulb control and music mode management."""

import asyncio
import logging
import threading
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler

from .bulb_controller import BulbController
from .scene_manager import SceneManager
from .visualizer import MusicVisualizer
from .voice_control import VoiceControl
from .alexa_skill import skill, init_alexa_skill
from .pc_control import execute_pc_command
from .config import get_flask_port, get_flask_debug, get_api_key

from functools import wraps

logger = logging.getLogger(__name__)


def _require_api_key(f):
    """Decorator that requires a valid API key for external endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = get_api_key()
        if api_key:
            provided = request.headers.get("X-API-Key") or request.args.get("api_key")
            if provided != api_key:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

_project_root = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(_project_root / "templates"),
    static_folder=str(_project_root / "static"),
)

# These will be set by create_app()
_controller: BulbController | None = None
_scene_manager: SceneManager | None = None
_visualizer: MusicVisualizer | None = None
_voice: VoiceControl | None = None
_loop: asyncio.AbstractEventLoop | None = None


def _run_async(coro):
    """Run an async coroutine from the Flask sync context."""
    if _loop is None:
        raise RuntimeError("Event loop not initialized")
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=10)


@app.route("/")
def index():
    """Render the main dashboard."""
    states = _run_async(_controller.get_state())
    scenes = _scene_manager.list_scenes()
    return render_template("index.html", bulbs=states, scenes=scenes)


@app.route("/api/color", methods=["POST"])
def api_set_color():
    """Set color on a specific bulb."""
    data = request.get_json()
    hue = int(data.get("hue", 0))
    saturation = int(data.get("saturation", 100))
    brightness = int(data.get("brightness", 50))
    bulb_index = data.get("bulb_index")
    if bulb_index is not None:
        bulb_index = int(bulb_index)
    _run_async(_controller.set_color(hue, saturation, brightness, bulb_index))
    return jsonify({"status": "ok"})


@app.route("/api/scene", methods=["POST"])
def api_apply_scene():
    """Apply a named scene."""
    data = request.get_json()
    scene_name = data.get("scene")
    try:
        _run_async(_scene_manager.apply_scene(scene_name))
        return jsonify({"status": "ok"})
    except KeyError as e:
        return jsonify({"status": "error", "message": str(e)}), 404


@app.route("/api/music/start", methods=["POST"])
def api_music_start():
    """Start music visualizer with specified mode."""
    data = request.get_json()
    mode = data.get("mode", "spectrum")
    _visualizer.set_mode(mode)
    _visualizer.start()
    return jsonify({"status": "ok", "mode": mode})


@app.route("/api/music/stop", methods=["POST"])
def api_music_stop():
    """Stop the music visualizer."""
    _visualizer.stop()
    return jsonify({"status": "ok"})


@app.route("/api/power", methods=["POST"])
def api_power():
    """Toggle bulb power."""
    data = request.get_json()
    action = data.get("action", "toggle")
    bulb_index = data.get("bulb_index")
    if bulb_index is not None:
        bulb_index = int(bulb_index)

    if action == "on":
        _run_async(_controller.turn_on(bulb_index))
    elif action == "off":
        _run_async(_controller.turn_off(bulb_index))
    else:
        # Toggle: read state first
        states = _run_async(_controller.get_state(bulb_index))
        if states and states[0].is_on:
            _run_async(_controller.turn_off(bulb_index))
        else:
            _run_async(_controller.turn_on(bulb_index))

    return jsonify({"status": "ok"})


# Smart command mapping for natural voice phrases from Alexa/IFTTT
_ALEXA_COMMANDS = {
    # Scenes
    "party": ("scene", "Party"),
    "fiesta": ("scene", "Party"),
    "chill": ("scene", "Chill"),
    "gaming": ("scene", "Gaming"),
    "movie": ("scene", "Movie"),
    "pelicula": ("scene", "Movie"),
    "sunset": ("scene", "Sunset"),
    "focus": ("scene", "Focus"),
    "sex": ("scene", "Sex"),
    # Music modes
    "spectrum": ("music_mode", "spectrum"),
    "energy": ("music_mode", "energy"),
    "pulse": ("music_mode", "pulse"),
    "dual": ("music_mode", "dual"),
    "complementary": ("music_mode", "complementary"),
    "chase": ("music_mode", "chase"),
    "sync": ("music_mode", "sync"),
    "music": ("music_mode", "sync"),
    "musica": ("music_mode", "sync"),
    # Power
    "on": ("power", "on"),
    "off": ("power", "off"),
    "encender": ("power", "on"),
    "apagar": ("power", "off"),
    "prender": ("power", "on"),
    # Music stop
    "stop": ("music_stop", None),
    "para": ("music_stop", None),
    "parar": ("music_stop", None),
    # PC control
    "apagar pc": ("pc", "shutdown"),
    "shutdown": ("pc", "shutdown"),
    "reiniciar": ("pc", "restart"),
    "restart": ("pc", "restart"),
    "suspender": ("pc", "sleep"),
    "dormir": ("pc", "sleep"),
    "bloquear": ("pc", "lock"),
    "lock": ("pc", "lock"),
    "cancelar apagado": ("pc", "cancel_shutdown"),
    "mutear": ("pc", "mute"),
    "mute": ("pc", "mute"),
    "subir volumen": ("pc", "volume_up"),
    "bajar volumen": ("pc", "volume_down"),
    "spotify": ("pc", "spotify"),
    "crunchyroll": ("pc", "crunchyroll"),
    "whatsapp": ("pc", "whatsapp"),
    "outlook": ("pc", "outlook"),
    "correo": ("pc", "outlook"),
    "steam": ("pc", "steam"),
    "wallpaper": ("pc", "wallpaper"),
    "youtube": ("pc", "youtube"),
}


@app.route("/api/webhook/ifttt", methods=["POST"])
@_require_api_key
def api_ifttt_webhook():
    """IFTTT webhook endpoint for Alexa integration.

    Accepts two formats:
    1. Structured: {"action": "scene:Party"} or {"action": "music:start"}
    2. Natural: {"action": "party"} - matched against _ALEXA_COMMANDS
    """
    data = request.get_json() or {}
    action = data.get("action", "").lower().strip()
    logger.info("IFTTT webhook received: action='%s'", action)

    # Format 1: structured commands (scene:X, music:start, etc.)
    if action.startswith("scene:"):
        scene_name = action.split(":", 1)[1].strip()
        try:
            _run_async(_scene_manager.apply_scene(scene_name))
            return jsonify({"status": "ok", "applied": scene_name})
        except KeyError as e:
            return jsonify({"status": "error", "message": str(e)}), 404
    elif action == "music:start":
        mode = data.get("mode", "spectrum")
        _visualizer.set_mode(mode)
        _visualizer.start()
        return jsonify({"status": "ok", "mode": mode})
    elif action == "music:stop":
        _visualizer.stop()
        return jsonify({"status": "ok"})
    elif action == "power:on":
        _run_async(_controller.turn_on())
        return jsonify({"status": "ok"})
    elif action == "power:off":
        _run_async(_controller.turn_off())
        return jsonify({"status": "ok"})
    elif action.startswith("pc:"):
        pc_action = action.split(":", 1)[1].strip()
        result = execute_pc_command(pc_action)
        return jsonify({"status": "ok", "message": result})

    # Format 2: natural language from Alexa "say a phrase with text ingredient"
    for keyword in sorted(_ALEXA_COMMANDS, key=len, reverse=True):
        cmd_type, cmd_value = _ALEXA_COMMANDS[keyword]
        if keyword in action:
            logger.info("Alexa command matched: '%s' -> %s(%s)", keyword, cmd_type, cmd_value)
            if cmd_type == "scene":
                try:
                    _run_async(_scene_manager.apply_scene(cmd_value))
                    return jsonify({"status": "ok", "applied": cmd_value})
                except KeyError as e:
                    return jsonify({"status": "error", "message": str(e)}), 404
            elif cmd_type == "music_mode":
                _visualizer.set_mode(cmd_value)
                _visualizer.start()
                return jsonify({"status": "ok", "mode": cmd_value})
            elif cmd_type == "music_stop":
                _visualizer.stop()
                return jsonify({"status": "ok"})
            elif cmd_type == "power":
                if cmd_value == "on":
                    _run_async(_controller.turn_on())
                else:
                    _run_async(_controller.turn_off())
                return jsonify({"status": "ok", "power": cmd_value})
            elif cmd_type == "pc":
                result = execute_pc_command(cmd_value)
                return jsonify({"status": "ok", "message": result})

    return jsonify({"status": "error", "message": f"Unknown action: {action}"}), 400


# Alexa Skill endpoint
_alexa_handler: WebserviceSkillHandler | None = None


@app.route("/alexa", methods=["POST"])
def alexa_endpoint():
    """Handle Alexa Skill requests."""
    if _alexa_handler is None:
        return jsonify({"error": "Alexa not initialized"}), 500
    response = _alexa_handler.verify_request_and_dispatch(
        http_request_headers=dict(request.headers),
        http_request_body=request.data.decode("utf-8"),
    )
    import json
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype="application/json",
    )


@app.route("/api/voice/start", methods=["POST"])
def api_voice_start():
    """Start voice control listening."""
    if _voice is None:
        return jsonify({"status": "error", "message": "Voice control not initialized"}), 500
    _voice.start()
    return jsonify({"status": "ok", "listening": True})


@app.route("/api/voice/stop", methods=["POST"])
def api_voice_stop():
    """Stop voice control listening."""
    if _voice is None:
        return jsonify({"status": "error", "message": "Voice control not initialized"}), 500
    _voice.stop()
    return jsonify({"status": "ok", "listening": False})


@app.route("/api/voice/status", methods=["GET"])
def api_voice_status():
    """Get voice control status."""
    running = _voice is not None and _voice._running
    return jsonify({"status": "ok", "listening": running})


def _handle_voice_action(action_type: str, action_value: str | None) -> None:
    """Handle a voice command by dispatching to the appropriate controller."""
    try:
        if action_type == "music_mode":
            _visualizer.set_mode(action_value)
            _visualizer.start()
            logger.info("Voice: music mode -> %s", action_value)
        elif action_type == "music_start":
            _visualizer.start()
            logger.info("Voice: music started")
        elif action_type == "music_stop":
            _visualizer.stop()
            logger.info("Voice: music stopped")
        elif action_type == "scene":
            _run_async(_scene_manager.apply_scene(action_value))
            logger.info("Voice: scene -> %s", action_value)
        elif action_type == "power":
            if action_value == "on":
                _run_async(_controller.turn_on())
            else:
                _run_async(_controller.turn_off())
            logger.info("Voice: power -> %s", action_value)
        elif action_type == "pc":
            result = execute_pc_command(action_value)
            logger.info("Voice: PC -> %s (%s)", action_value, result)
    except Exception:
        logger.exception("Error handling voice action: %s(%s)", action_type, action_value)


def create_app(
    controller: BulbController,
    scene_manager: SceneManager,
    visualizer: MusicVisualizer,
    loop: asyncio.AbstractEventLoop,
) -> Flask:
    """Initialize the Flask app with shared components."""
    global _controller, _scene_manager, _visualizer, _voice, _loop, _alexa_handler
    _controller = controller
    _scene_manager = scene_manager
    _visualizer = visualizer
    _loop = loop
    _voice = VoiceControl(action_callback=_handle_voice_action)
    # Init Alexa skill
    init_alexa_skill(controller, scene_manager, visualizer, loop)
    _alexa_handler = WebserviceSkillHandler(
        skill=skill, verify_signature=True, verify_timestamp=True
    )
    return app


def run_server(
    controller: BulbController,
    scene_manager: SceneManager,
    visualizer: MusicVisualizer,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """Start the Flask web server in a background thread."""
    create_app(controller, scene_manager, visualizer, loop)
    port = get_flask_port()
    debug = get_flask_debug()
    logger.info("Starting web UI on http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
