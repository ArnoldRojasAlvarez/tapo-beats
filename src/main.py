"""CLI entry point for TapoBeats."""

import argparse
import asyncio
import logging
import sys
import time
import threading

from .bulb_controller import BulbController
from .audio_capture import AudioCapture
from .audio_analyzer import AudioAnalyzer
from .visualizer import MusicVisualizer
from .scene_manager import SceneManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def cmd_test_bulbs() -> None:
    """Discover bulbs, print state, cycle RGB, restore original state."""
    ctrl = BulbController()
    await ctrl.connect_all()

    if not ctrl.bulbs:
        logger.error("No bulbs found. Check your network and .env credentials.")
        return

    # Print current state
    states = await ctrl.get_state()
    for s in states:
        print(f"  {s.alias} ({s.ip}): on={s.is_on}, HSV=({s.hue},{s.saturation},{s.brightness}), temp={s.color_temp}K")

    # Save original state
    original_states = states

    # Cycle through red -> green -> blue
    print("\nCycling colors: red -> green -> blue...")
    await ctrl.turn_on()
    for color_name, hue in [("Red", 0), ("Green", 120), ("Blue", 240)]:
        print(f"  -> {color_name}")
        await ctrl.set_color(hue, 100, 80)
        await asyncio.sleep(1.5)

    # Restore original state
    print("Restoring original state...")
    for i, orig in enumerate(original_states):
        if orig.is_on:
            await ctrl.turn_on(i)
            await ctrl.set_color(orig.hue, orig.saturation, orig.brightness, i)
        else:
            await ctrl.turn_off(i)

    print("Done!")


async def cmd_test_audio() -> None:
    """Capture 10 seconds of system audio and print band energies."""
    analyzer_ref = [None]

    def on_audio(chunk):
        if analyzer_ref[0] is None:
            return
        features = analyzer_ref[0].analyze(chunk)
        bars = {name: "#" * int(energy * 20) for name, energy in features.band_energies.items()}
        beat_marker = " *** BEAT ***" if features.is_beat else ""
        print(
            f"  sub={bars['sub_bass']:20s} | bass={bars['bass']:20s} | "
            f"mid={bars['mid']:20s} | high={bars['high']:20s} | "
            f"vol={features.overall_volume:.2f}{beat_marker}",
            end="\r",
        )

    capture = AudioCapture(callback=on_audio)
    print("Capturing system audio for 10 seconds... (play some music!)")
    capture.start()
    analyzer_ref[0] = AudioAnalyzer(sample_rate=capture.sample_rate)

    try:
        await asyncio.sleep(10)
    finally:
        capture.stop()

    print("\nDone!")


async def cmd_music(mode: str) -> None:
    """Start music-reactive lighting mode."""
    ctrl = BulbController()
    await ctrl.connect_all()

    if not ctrl.bulbs:
        logger.error("No bulbs found.")
        return

    visualizer = MusicVisualizer(ctrl, mode=mode)
    visualizer.start()

    latest_features = [None]
    analyzer_ref = [None]

    def on_audio(chunk):
        if analyzer_ref[0] is not None:
            latest_features[0] = analyzer_ref[0].analyze(chunk)

    capture = AudioCapture(callback=on_audio)
    capture.start()
    analyzer_ref[0] = AudioAnalyzer(sample_rate=capture.sample_rate)

    print(f"Music mode '{mode}' active. Press Ctrl+C to stop.")
    try:
        while True:
            if latest_features[0] is not None:
                await visualizer.update(latest_features[0])
                latest_features[0] = None
            await asyncio.sleep(0.070)  # ~14 Hz update rate
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        visualizer.stop()
        capture.stop()


async def cmd_serve() -> None:
    """Start the Flask web UI."""
    from .web_ui import run_server

    ctrl = BulbController()
    await ctrl.connect_all()

    visualizer = MusicVisualizer(ctrl)
    scene_mgr = SceneManager(ctrl)

    loop = asyncio.get_event_loop()

    # Run music visualizer update loop in background
    latest_features = [None]
    analyzer_ref = [None]

    def on_audio(chunk):
        if analyzer_ref[0] is not None:
            latest_features[0] = analyzer_ref[0].analyze(chunk)

    capture = AudioCapture(callback=on_audio)

    async def visualizer_loop():
        while True:
            if latest_features[0] is not None and visualizer._running:
                await visualizer.update(latest_features[0])
                latest_features[0] = None
            await asyncio.sleep(0.070)

    # Start audio capture
    capture.start()
    analyzer_ref[0] = AudioAnalyzer(sample_rate=capture.sample_rate)

    # Start visualizer loop as background task
    asyncio.ensure_future(visualizer_loop())

    # Run Flask in a thread (it's synchronous)
    flask_thread = threading.Thread(
        target=run_server,
        args=(ctrl, scene_mgr, visualizer, loop),
        daemon=True,
    )
    flask_thread.start()

    print("Web UI running at http://localhost:5000 — Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        capture.stop()


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="tapo-beats",
        description="TapoBeats — Music-Reactive Smart Lighting Controller",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("test-bulbs", help="Discover bulbs, cycle RGB test")
    sub.add_parser("test-audio", help="Capture 10s of system audio, print bands")

    music_parser = sub.add_parser("music", help="Start music-reactive mode")
    music_parser.add_argument(
        "mode",
        choices=["spectrum", "energy", "pulse", "dual", "complementary", "chase", "sync"],
        help="Visualization mode",
    )

    sub.add_parser("serve", help="Start Flask web UI")

    args = parser.parse_args()

    if args.command == "test-bulbs":
        asyncio.run(cmd_test_bulbs())
    elif args.command == "test-audio":
        asyncio.run(cmd_test_audio())
    elif args.command == "music":
        asyncio.run(cmd_music(args.mode))
    elif args.command == "serve":
        asyncio.run(cmd_serve())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
