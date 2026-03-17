"""Alexa Skill handler for TapoBeats - invocation name: 'Jarvis'."""

import asyncio
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from .pc_control import execute_pc_command

logger = logging.getLogger(__name__)

# These get set by init_alexa_skill()
_controller = None
_scene_manager = None
_visualizer = None
_loop = None

# All recognized commands
_COMMANDS = {
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
    # Power (lights)
    "encender": ("power", "on"),
    "prender": ("power", "on"),
    "apagar": ("power", "off"),
    "on": ("power", "on"),
    "off": ("power", "off"),
    # Stop
    "stop": ("music_stop", None),
    "para": ("music_stop", None),
    "parar": ("music_stop", None),
    "detener": ("music_stop", None),
    # PC control
    "apagar pc": ("pc", "shutdown"),
    "shutdown": ("pc", "shutdown"),
    "reiniciar": ("pc", "restart"),
    "restart": ("pc", "restart"),
    "suspender": ("pc", "sleep"),
    "dormir": ("pc", "sleep"),
    "sleep": ("pc", "sleep"),
    "bloquear": ("pc", "lock"),
    "lock": ("pc", "lock"),
    "cancelar apagado": ("pc", "cancel_shutdown"),
    # Volume
    "mutear": ("pc", "mute"),
    "mute": ("pc", "mute"),
    "subir volumen": ("pc", "volume_up"),
    "volume up": ("pc", "volume_up"),
    "bajar volumen": ("pc", "volume_down"),
    "volume down": ("pc", "volume_down"),
    # Apps
    "spotify": ("pc", "spotify"),
    "crunchyroll": ("pc", "crunchyroll"),
    "whatsapp": ("pc", "whatsapp"),
    "outlook": ("pc", "outlook"),
    "correo": ("pc", "outlook"),
    "steam": ("pc", "steam"),
    "wallpaper": ("pc", "wallpaper"),
    "youtube": ("pc", "youtube"),
}

# Help card content organized by category
_HELP_CARD = (
    "━━━ JARVIS - Comandos ━━━\n"
    "\n"
    "🎨 ESCENAS\n"
    "  party · chill · gaming\n"
    "  movie · sunset · focus · sex\n"
    "\n"
    "🎵 MUSICA\n"
    "  sync · spectrum · energy\n"
    "  pulse · dual · chase · stop\n"
    "\n"
    "💡 LUCES\n"
    "  encender · apagar\n"
    "\n"
    "🖥️ PC\n"
    "  apagar pc · reiniciar\n"
    "  suspender · bloquear\n"
    "  cancelar apagado\n"
    "\n"
    "🔊 VOLUMEN\n"
    "  subir volumen · bajar volumen\n"
    "  mutear\n"
    "\n"
    "📱 APPS\n"
    "  spotify · youtube · steam\n"
    "  crunchyroll · whatsapp\n"
    "  outlook · wallpaper\n"
    "\n"
    "💬 Di 'ayuda' para ver esto de nuevo"
)

_HELP_SPEECH = (
    "Te envie la lista de comandos a la app de Alexa. "
    "Tienes escenas, musica, control de luces, P.C. y apps."
)

_HELP_SHORT_SPEECH = "Revisa la app de Alexa para ver todos los comandos."


def _run_async(coro):
    """Run async coroutine from sync context."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=10)


def _execute_command(command: str) -> tuple[str, SimpleCard | None]:
    """Execute a command and return (speech, card) tuple."""
    command = command.lower().strip()
    logger.info("Alexa command: '%s'", command)

    # Check for help command
    if command in ("ayuda", "help", "comandos", "lista", "commands"):
        return _HELP_SPEECH, SimpleCard(title="Jarvis - Comandos", content=_HELP_CARD)

    # Sort by keyword length (longest first) for greedy matching
    for keyword in sorted(_COMMANDS, key=len, reverse=True):
        cmd_type, cmd_value = _COMMANDS[keyword]
        if keyword in command:
            logger.info("Matched: '%s' -> %s(%s)", keyword, cmd_type, cmd_value)
            if cmd_type == "scene":
                try:
                    _run_async(_scene_manager.apply_scene(cmd_value))
                    return f"{cmd_value} activado", None
                except KeyError:
                    return f"Escena {cmd_value} no encontrada", None
            elif cmd_type == "music_mode":
                _visualizer.set_mode(cmd_value)
                _visualizer.start()
                return f"{cmd_value} activado", None
            elif cmd_type == "music_stop":
                _visualizer.stop()
                return "Listo", None
            elif cmd_type == "power":
                if cmd_value == "on":
                    _run_async(_controller.turn_on())
                    return "Listo", None
                else:
                    _run_async(_controller.turn_off())
                    return "Listo", None
            elif cmd_type == "pc":
                result = execute_pc_command(cmd_value)
                return result, None

    # Command not found -> suggest help
    return (
        f"No encontre '{command}'. Di 'ayuda' para ver los comandos.",
        None,
    )


class LaunchHandler(AbstractRequestHandler):
    """Handle skill launch: 'Alexa, abre Jarvis'."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak("Dime un comando.")
            .ask("Dime un comando.")
            .response
        )


class CommandHandler(AbstractRequestHandler):
    """Handle the CommandIntent: 'dile a Jarvis {command}'."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("CommandIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots
        command = slots.get("command")
        command_text = command.value if command and command.value else ""

        if not command_text:
            return (
                handler_input.response_builder
                .speak("No escuche. Di 'ayuda' para ver los comandos.")
                .ask("Dime un comando.")
                .response
            )

        speech, card = _execute_command(command_text)
        builder = handler_input.response_builder.speak(speech)
        if card:
            builder.set_card(card)
        return builder.response


class HelpHandler(AbstractRequestHandler):
    """Handle help request."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak(_HELP_SPEECH)
            .set_card(SimpleCard(title="Jarvis - Comandos", content=_HELP_CARD))
            .ask("Dime un comando.")
            .response
        )


class StopHandler(AbstractRequestHandler):
    """Handle stop/cancel."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return (
            is_intent_name("AMAZON.StopIntent")(handler_input)
            or is_intent_name("AMAZON.CancelIntent")(handler_input)
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak("Chao").response


class FallbackHandler(AbstractRequestHandler):
    """Handle unrecognized input."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak("No entendi. Di 'ayuda' para ver los comandos.")
            .ask("Dime un comando.")
            .response
        )


class SessionEndedHandler(AbstractRequestHandler):
    """Handle session end."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response


# Build the skill
sb = SkillBuilder()
sb.add_request_handler(LaunchHandler())
sb.add_request_handler(CommandHandler())
sb.add_request_handler(HelpHandler())
sb.add_request_handler(StopHandler())
sb.add_request_handler(FallbackHandler())
sb.add_request_handler(SessionEndedHandler())

skill = sb.create()


def init_alexa_skill(controller, scene_manager, visualizer, loop):
    """Initialize the Alexa skill with shared components."""
    global _controller, _scene_manager, _visualizer, _loop
    _controller = controller
    _scene_manager = scene_manager
    _visualizer = visualizer
    _loop = loop
