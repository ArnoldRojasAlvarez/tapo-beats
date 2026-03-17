"""Async wrapper for controlling Tapo L530 bulbs via python-kasa."""

import logging
from dataclasses import dataclass

from kasa import Module

from .discovery import discover_bulbs

logger = logging.getLogger(__name__)


@dataclass
class BulbState:
    """Snapshot of a bulb's current state."""
    alias: str
    ip: str
    is_on: bool
    hue: int
    saturation: int
    brightness: int
    color_temp: int


class BulbController:
    """High-level async controller for one or more Tapo L530 bulbs."""

    def __init__(self) -> None:
        self.bulbs: list = []

    async def connect_all(self) -> None:
        """Discover and connect to all L530 bulbs on the network."""
        self.bulbs = await discover_bulbs()
        for dev in self.bulbs:
            await dev.update()
        logger.info("Connected to %d bulb(s)", len(self.bulbs))

    async def connect(self, ip: str) -> None:
        """Connect to a single bulb by IP address."""
        from kasa import Discover
        from .config import get_tapo_credentials

        username, password = get_tapo_credentials()
        dev = await Discover.discover_single(ip, username=username, password=password)
        await dev.update()
        self.bulbs.append(dev)
        logger.info("Connected to bulb at %s: %s", ip, dev.alias)

    async def set_color(self, hue: int, saturation: int, brightness: int, bulb_index: int | None = None) -> None:
        """Set HSV color on one or all bulbs.

        Args:
            hue: 0-360
            saturation: 0-100
            brightness: 0-100
            bulb_index: Target specific bulb, or None for all.
        """
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        for dev in targets:
            try:
                light = dev.modules[Module.Light]
                await light.set_hsv(hue, saturation, brightness)
            except Exception:
                logger.exception("Failed to set color on %s", dev.alias)

    async def _set_color_single(self, dev, hue: int, saturation: int, brightness: int) -> None:
        """Set color on a single device (for parallel use)."""
        try:
            light = dev.modules[Module.Light]
            await light.set_hsv(hue, saturation, brightness)
        except Exception:
            logger.exception("Failed to set color on %s", dev.alias)

    async def set_color_parallel(self, colors: list[tuple[int, int, int, int]]) -> None:
        """Set colors on multiple bulbs simultaneously.

        Args:
            colors: List of (hue, saturation, brightness, bulb_index) tuples.
        """
        import asyncio
        tasks = []
        for hue, sat, bri, idx in colors:
            if idx < len(self.bulbs):
                tasks.append(self._set_color_single(self.bulbs[idx], hue, sat, bri))
        if tasks:
            await asyncio.gather(*tasks)

    async def set_color_temp(self, kelvin: int, bulb_index: int | None = None) -> None:
        """Set color temperature (2500-6500K) on one or all bulbs."""
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        for dev in targets:
            try:
                light = dev.modules[Module.Light]
                await light.set_color_temp(kelvin)
                await dev.update()
            except Exception:
                logger.exception("Failed to set color temp on %s", dev.alias)

    async def set_brightness(self, percent: int, bulb_index: int | None = None) -> None:
        """Set brightness (0-100) on one or all bulbs."""
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        for dev in targets:
            try:
                light = dev.modules[Module.Light]
                await light.set_brightness(percent)
                await dev.update()
            except Exception:
                logger.exception("Failed to set brightness on %s", dev.alias)

    async def turn_on(self, bulb_index: int | None = None) -> None:
        """Turn on one or all bulbs."""
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        for dev in targets:
            try:
                await dev.turn_on()
                await dev.update()
            except Exception:
                logger.exception("Failed to turn on %s", dev.alias)

    async def turn_off(self, bulb_index: int | None = None) -> None:
        """Turn off one or all bulbs."""
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        for dev in targets:
            try:
                await dev.turn_off()
                await dev.update()
            except Exception:
                logger.exception("Failed to turn off %s", dev.alias)

    async def set_effect(self, name: str, bulb_index: int | None = None) -> None:
        """Set a light effect ('Party', 'Relax', or clear with 'Off').

        Args:
            name: Effect name — 'Party', 'Relax', or 'Off' to clear.
            bulb_index: Target specific bulb, or None for all.
        """
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        for dev in targets:
            try:
                effect_module = dev.modules[Module.LightEffect]
                if name.lower() == "off":
                    await effect_module.set_effect("Off")
                else:
                    await effect_module.set_effect(name)
                await dev.update()
            except Exception:
                logger.exception("Failed to set effect '%s' on %s", name, dev.alias)

    async def get_state(self, bulb_index: int | None = None) -> list[BulbState]:
        """Get current state of one or all bulbs."""
        targets = [self.bulbs[bulb_index]] if bulb_index is not None else self.bulbs
        states = []
        for dev in targets:
            try:
                await dev.update()
                light = dev.modules[Module.Light]
                hsv = light.hsv
                states.append(BulbState(
                    alias=dev.alias,
                    ip=str(dev.host),
                    is_on=dev.is_on,
                    hue=hsv.hue if hsv else 0,
                    saturation=hsv.saturation if hsv else 0,
                    brightness=light.brightness,
                    color_temp=light.color_temp,
                ))
            except Exception:
                logger.exception("Failed to get state from %s", dev.alias)
        return states
