"""Preset scene management — load, save, and apply lighting scenes."""

import json
import logging
from pathlib import Path

from .bulb_controller import BulbController

logger = logging.getLogger(__name__)

SCENES_FILE = Path(__file__).resolve().parent.parent / "scenes" / "default_scenes.json"


class SceneManager:
    """Manages lighting scene presets."""

    def __init__(self, controller: BulbController) -> None:
        self.controller = controller
        self.scenes: dict = {}
        self._load_scenes()

    def _load_scenes(self) -> None:
        """Load scenes from the JSON file."""
        if SCENES_FILE.exists():
            with open(SCENES_FILE) as f:
                self.scenes = json.load(f)
            logger.info("Loaded %d scene(s) from %s", len(self.scenes), SCENES_FILE)
        else:
            logger.warning("Scenes file not found: %s", SCENES_FILE)
            self.scenes = {}

    def _save_scenes(self) -> None:
        """Persist scenes to the JSON file."""
        SCENES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCENES_FILE, "w") as f:
            json.dump(self.scenes, f, indent=2)
        logger.info("Saved %d scene(s) to %s", len(self.scenes), SCENES_FILE)

    def list_scenes(self) -> list[str]:
        """Return names of all available scenes."""
        return list(self.scenes.keys())

    async def apply_scene(self, scene_name: str) -> None:
        """Apply a named scene to the connected bulbs.

        Args:
            scene_name: Name of the scene to apply.

        Raises:
            KeyError: If scene_name is not found.
        """
        if scene_name not in self.scenes:
            raise KeyError(f"Scene '{scene_name}' not found. Available: {self.list_scenes()}")

        scene = self.scenes[scene_name]
        bulbs_config = scene.get("bulbs", [])

        for i, bulb_cfg in enumerate(bulbs_config):
            if i >= len(self.controller.bulbs):
                break

            if "color_temp" in bulb_cfg:
                await self.controller.set_color_temp(bulb_cfg["color_temp"], bulb_index=i)
                await self.controller.set_brightness(bulb_cfg.get("brightness", 50), bulb_index=i)
            else:
                await self.controller.set_color(
                    bulb_cfg.get("hue", 0),
                    bulb_cfg.get("saturation", 100),
                    bulb_cfg.get("brightness", 50),
                    bulb_index=i,
                )

        logger.info("Applied scene: %s", scene_name)

    async def create_scene(self, name: str) -> None:
        """Save the current state of all bulbs as a new scene."""
        states = await self.controller.get_state()
        bulbs_config = []
        for state in states:
            bulbs_config.append({
                "hue": state.hue,
                "saturation": state.saturation,
                "brightness": state.brightness,
            })

        self.scenes[name] = {
            "bulbs": bulbs_config,
            "transition_ms": 500,
        }
        self._save_scenes()
        logger.info("Created scene '%s' from current bulb state", name)
