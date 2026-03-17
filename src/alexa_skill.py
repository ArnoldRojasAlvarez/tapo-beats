"""Alexa Skill handler for TapoBeats - invocation name: 'eco'."""

import asyncio
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

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
    # Power
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
}


def _run_async(coro):
    """Run async coroutine from sync context."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=10)


def _execute_command(command: str) -> str:
    """Execute a command and return a speech response."""
    command = command.lower().strip()
    logger.info("Alexa command: '%s'", command)

    for keyword, (cmd_type, cmd_value) in _COMMANDS.items():
        if keyword in command:
            logger.info("Matched: '%s' -> %s(%s)", keyword, cmd_type, cmd_value)
            if cmd_type == "scene":
                try:
                    _run_async(_scene_manager.apply_scene(cmd_value))
                    return f"Escena {cmd_value} activada"
                except KeyError:
                    return f"No encontre la escena {cmd_value}"
            elif cmd_type == "music_mode":
                _visualizer.set_mode(cmd_value)
                _visualizer.start()
                return f"Modo {cmd_value} activado"
            elif cmd_type == "music_stop":
                _visualizer.stop()
                return "Musica detenida"
            elif cmd_type == "power":
                if cmd_value == "on":
                    _run_async(_controller.turn_on())
                    return "Luces encendidas"
                else:
                    _run_async(_controller.turn_off())
                    return "Luces apagadas"

    return f"No entendi el comando: {command}"


class LaunchHandler(AbstractRequestHandler):
    """Handle skill launch: 'Alexa, abre eco'."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech = "Listo. Dime un comando como party, sync, o apagar."
        return (
            handler_input.response_builder
            .speak(speech)
            .ask("Dime un comando")
            .response
        )


class CommandHandler(AbstractRequestHandler):
    """Handle the CommandIntent: 'dile a eco {command}'."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("CommandIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots
        command = slots.get("command")
        command_text = command.value if command and command.value else ""

        if not command_text:
            return (
                handler_input.response_builder
                .speak("No escuche el comando. Intenta de nuevo.")
                .ask("Dime un comando")
                .response
            )

        result = _execute_command(command_text)
        return handler_input.response_builder.speak(result).response


class HelpHandler(AbstractRequestHandler):
    """Handle help request."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech = (
            "Puedes decir: party, gaming, chill, movie, sunset, focus, sex, "
            "sync, spectrum, energy, pulse, chase, stop, encender, o apagar."
        )
        return (
            handler_input.response_builder
            .speak(speech)
            .ask("Dime un comando")
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
        return handler_input.response_builder.speak("Hasta luego").response


class FallbackHandler(AbstractRequestHandler):
    """Handle unrecognized input."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak("No entendi. Di un comando como party, sync o apagar.")
            .ask("Dime un comando")
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
