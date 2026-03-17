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

# Ambiguous commands that need clarification
_AMBIGUOUS = {
    "apagar": {
        "question": "Que apago? Luces, P.C., o una app?",
        "options": {
            "luces": ("power", "off"),
            "luz": ("power", "off"),
            "bombillos": ("power", "off"),
            "pc": ("pc", "shutdown"),
            "computadora": ("pc", "shutdown"),
            "computador": ("pc", "shutdown"),
            "todo": ("power_and_pc", "off"),
        },
    },
    "encender": {
        "question": "Que enciendo? Luces o una app?",
        "options": {
            "luces": ("power", "on"),
            "luz": ("power", "on"),
            "bombillos": ("power", "on"),
            "spotify": ("pc", "spotify"),
            "youtube": ("pc", "youtube"),
            "steam": ("pc", "steam"),
            "crunchyroll": ("pc", "crunchyroll"),
            "whatsapp": ("pc", "whatsapp"),
            "outlook": ("pc", "outlook"),
            "correo": ("pc", "outlook"),
            "wallpaper": ("pc", "wallpaper"),
        },
    },
}

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
    # Power (lights) - specific versions that won't trigger ambiguity
    "encender luces": ("power", "on"),
    "prender luces": ("power", "on"),
    "apagar luces": ("power", "off"),
    "encender bombillos": ("power", "on"),
    "apagar bombillos": ("power", "off"),
    "prender": ("power", "on"),
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
    # Abrir apps
    "abrir spotify": ("pc", "spotify"),
    "abrir youtube": ("pc", "youtube"),
    "abrir steam": ("pc", "steam"),
    "abrir crunchyroll": ("pc", "crunchyroll"),
    "abrir whatsapp": ("pc", "whatsapp"),
    "abrir outlook": ("pc", "outlook"),
    "abrir correo": ("pc", "outlook"),
    "abrir wallpaper": ("pc", "wallpaper"),
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


def _run_async(coro):
    """Run async coroutine from sync context."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=10)


def _execute_action(cmd_type: str, cmd_value: str) -> str:
    """Execute a resolved action and return speech."""
    if cmd_type == "scene":
        try:
            _run_async(_scene_manager.apply_scene(cmd_value))
            return f"{cmd_value} activado"
        except KeyError:
            return f"Escena {cmd_value} no encontrada"
    elif cmd_type == "music_mode":
        _visualizer.set_mode(cmd_value)
        _visualizer.start()
        return f"{cmd_value} activado"
    elif cmd_type == "music_stop":
        _visualizer.stop()
        return "Listo"
    elif cmd_type == "power":
        if cmd_value == "on":
            _run_async(_controller.turn_on())
        else:
            _run_async(_controller.turn_off())
        return "Listo"
    elif cmd_type == "power_and_pc":
        _run_async(_controller.turn_off())
        execute_pc_command("shutdown")
        return "Apagando luces y P.C."
    elif cmd_type == "pc":
        return execute_pc_command(cmd_value)
    return "Comando no reconocido"


def _is_ambiguous(command: str) -> str | None:
    """Check if command is ambiguous (just 'apagar' or 'encender' alone).

    Returns the ambiguous key if it matches, None otherwise.
    """
    # If the command has more specific words, it's not ambiguous
    for keyword in sorted(_COMMANDS, key=len, reverse=True):
        if keyword in command:
            return None  # Found a specific match, not ambiguous

    # Check if it's one of the ambiguous base words
    for key in _AMBIGUOUS:
        if key in command:
            return key
    return None


def _resolve_followup(pending_action: str, answer: str) -> tuple[str, str] | None:
    """Try to resolve a follow-up answer for an ambiguous command."""
    answer = answer.lower().strip()
    if pending_action not in _AMBIGUOUS:
        return None
    options = _AMBIGUOUS[pending_action]["options"]
    for keyword in sorted(options, key=len, reverse=True):
        if keyword in answer:
            return options[keyword]
    return None


def _execute_command(command: str) -> tuple[str, SimpleCard | None, str | None]:
    """Execute a command. Returns (speech, card, pending_action).

    pending_action is set when the command is ambiguous and needs clarification.
    """
    command = command.lower().strip()
    logger.info("Alexa command: '%s'", command)

    # Check for help command
    if command in ("ayuda", "help", "comandos", "lista", "commands"):
        return _HELP_SPEECH, SimpleCard(title="Jarvis - Comandos", content=_HELP_CARD), None

    # Check for ambiguous commands first
    ambiguous_key = _is_ambiguous(command)
    if ambiguous_key:
        question = _AMBIGUOUS[ambiguous_key]["question"]
        logger.info("Ambiguous command: '%s' -> asking for clarification", command)
        return question, None, ambiguous_key

    # Sort by keyword length (longest first) for greedy matching
    for keyword in sorted(_COMMANDS, key=len, reverse=True):
        cmd_type, cmd_value = _COMMANDS[keyword]
        if keyword in command:
            logger.info("Matched: '%s' -> %s(%s)", keyword, cmd_type, cmd_value)
            result = _execute_action(cmd_type, cmd_value)
            return result, None, None

    # Command not found -> suggest help
    return "No encontre ese comando. Di 'ayuda' para ver la lista.", None, None


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
        session_attrs = handler_input.attributes_manager.session_attributes

        if not command_text:
            return (
                handler_input.response_builder
                .speak("No escuche. Di 'ayuda' para ver los comandos.")
                .ask("Dime un comando.")
                .response
            )

        # Check if we're in a follow-up conversation
        pending = session_attrs.get("pending_action")
        if pending:
            session_attrs.pop("pending_action", None)
            resolved = _resolve_followup(pending, command_text)
            if resolved:
                cmd_type, cmd_value = resolved
                result = _execute_action(cmd_type, cmd_value)
                return handler_input.response_builder.speak(result).response
            else:
                return (
                    handler_input.response_builder
                    .speak(f"No entendi. Di luces, P.C., o el nombre de una app.")
                    .ask("Que quieres controlar?")
                    .response
                )

        # Normal command processing
        speech, card, pending_action = _execute_command(command_text)
        builder = handler_input.response_builder.speak(speech)

        if card:
            builder.set_card(card)

        if pending_action:
            # Ambiguous command -> keep session open for follow-up
            session_attrs["pending_action"] = pending_action
            builder.ask(speech)

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
        session_attrs = handler_input.attributes_manager.session_attributes

        # If we're waiting for a follow-up, re-prompt
        pending = session_attrs.get("pending_action")
        if pending and pending in _AMBIGUOUS:
            question = _AMBIGUOUS[pending]["question"]
            return (
                handler_input.response_builder
                .speak(f"No entendi. {question}")
                .ask(question)
                .response
            )

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
