"""Discover Tapo devices on the local network using python-kasa."""

import logging
from kasa import Discover

from .config import get_tapo_credentials, get_bulb_ips

logger = logging.getLogger(__name__)


async def discover_bulbs() -> list:
    """Discover all Tapo L530 bulbs on the LAN.

    If BULB_IPS is set in .env, connects to those IPs directly.
    Otherwise performs network-wide discovery.

    Returns:
        List of discovered kasa SmartDevice instances (not yet updated).
    """
    username, password = get_tapo_credentials()
    static_ips = get_bulb_ips()

    devices = []

    if static_ips:
        logger.info("Using static bulb IPs: %s", static_ips)
        for ip in static_ips:
            try:
                dev = await Discover.discover_single(
                    ip, username=username, password=password
                )
                devices.append(dev)
                logger.info("Connected to bulb at %s: %s", ip, dev.alias)
            except Exception:
                logger.exception("Failed to connect to bulb at %s", ip)
    else:
        logger.info("Discovering Tapo devices on LAN...")
        found = await Discover.discover(username=username, password=password)
        for ip, dev in found.items():
            # Filter for bulb-type devices
            if dev.is_light_strip or dev.is_bulb:
                devices.append(dev)
                logger.info("Discovered bulb at %s: %s", ip, dev.alias)
            else:
                logger.debug("Skipping non-bulb device at %s: %s", ip, dev.alias)

    if not devices:
        logger.warning("No Tapo bulbs found on the network.")

    return devices
