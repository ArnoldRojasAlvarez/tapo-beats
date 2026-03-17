"""Discover Tapo devices on the local network using python-kasa."""

import asyncio
import logging
import subprocess
from kasa import Discover

from .config import get_tapo_credentials, get_bulb_ips

logger = logging.getLogger(__name__)


def _get_hotspot_clients() -> list[str]:
    """Get IPs of devices connected to the Windows mobile hotspot via ARP."""
    try:
        result = subprocess.run(
            ["arp", "-a", "-N", "192.168.137.1"],
            capture_output=True, text=True, timeout=5,
        )
        ips = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].startswith("192.168.137."):
                ip = parts[0]
                if ip not in ("192.168.137.1", "192.168.137.255") and not ip.startswith("224."):
                    ips.append(ip)
        return ips
    except Exception:
        logger.exception("Failed to read ARP table")
        return []


async def discover_bulbs() -> list:
    """Discover all Tapo L530 bulbs on the LAN.

    If BULB_IPS is set in .env, connects to those IPs directly.
    Otherwise probes devices on the hotspot via ARP, falling back to
    network-wide broadcast discovery.

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
        # Try ARP-based discovery first (works better on Windows hotspot)
        hotspot_ips = _get_hotspot_clients()
        if hotspot_ips:
            logger.info("Probing hotspot clients: %s", hotspot_ips)
            tasks = []
            for ip in hotspot_ips:
                tasks.append(_try_connect(ip, username, password))
            results = await asyncio.gather(*tasks)
            devices = [dev for dev in results if dev is not None]

        # Fallback to broadcast discovery
        if not devices:
            logger.info("Discovering Tapo devices on LAN via broadcast...")
            found = await Discover.discover(username=username, password=password)
            for ip, dev in found.items():
                if dev.is_light_strip or dev.is_bulb:
                    devices.append(dev)
                    logger.info("Discovered bulb at %s: %s", ip, dev.alias)

    if not devices:
        logger.warning("No Tapo bulbs found on the network.")

    return devices


async def _try_connect(ip: str, username: str, password: str):
    """Try to connect to a single IP as a Tapo device."""
    try:
        dev = await Discover.discover_single(
            ip, username=username, password=password, timeout=5
        )
        await dev.update()
        if dev.is_bulb or dev.is_light_strip:
            logger.info("Found bulb at %s: %s", ip, dev.alias)
            return dev
        else:
            logger.debug("Device at %s is not a bulb: %s", ip, dev.alias)
    except Exception:
        logger.debug("No Tapo device at %s", ip)
    return None
