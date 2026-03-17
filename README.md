# TapoBeats — Music-Reactive Smart Lighting with Alexa Voice Control

Control TP-Link Tapo L530 smart bulbs with music playing on your PC. Real-time beat detection and frequency analysis drive color changes across multiple visualization modes. Trigger scenes and modes hands-free with Alexa or local voice commands.

## Features

- **Music Sync** — Captures system audio (WASAPI loopback) and maps frequency/beat data to light colors in real-time
- **7 Visualization Modes** — spectrum, energy, pulse, dual, complementary, chase, sync
- **7 Scene Presets** — Chill, Party, Gaming, Movie, Sunset, Focus, Sex
- **Alexa Skill ("Jarvis")** — Custom Alexa skill to trigger scenes and music modes by voice on Echo devices
- **IFTTT Webhook** — Alternative voice control via IFTTT webhook integration
- **Local Voice Control** — Offline speech recognition (Vosk) with dual-language support (English + Spanish)
- **Web Dashboard** — Flask UI for manual control from any device on LAN
- **Bulb Control** — Programmatic color, brightness, effects, on/off via python-kasa

## Requirements

- Python 3.11+
- Windows 10/11 (WASAPI loopback for audio capture)
- TP-Link Tapo L530 bulbs on the same local network
- TP-Link cloud account (email + password)
- (Optional) Amazon Echo device for Alexa skill integration
- (Optional) [Ngrok](https://ngrok.com/) for exposing the local server to Alexa

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   git clone https://github.com/YOUR_USER/tapo-beats.git
   cd tapo-beats
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your TP-Link credentials:
   ```bash
   copy .env.example .env
   ```

3. Start the server (web UI + all integrations):
   ```bash
   python -m src.main serve
   ```
   Open http://localhost:5000 in your browser.

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m src.main test-bulbs` | Discover bulbs, print state, cycle RGB |
| `python -m src.main test-audio` | Capture 10s of system audio, print band energies |
| `python -m src.main music <mode>` | Start music mode (spectrum/energy/pulse/dual) |
| `python -m src.main serve` | Start Flask web UI on port 5000 |

## Alexa Skill Setup ("Jarvis")

The project includes a custom Alexa skill that lets you control lights with voice commands on any Echo device.

### 1. Create the Alexa Skill

1. Go to the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Create a new custom skill
3. Set the invocation name to **Jarvis** (or your preferred name)
4. Import the interaction model from `alexa_model.json` in the JSON Editor
5. Build the model

### 2. Configure the Endpoint

1. Install and authenticate [ngrok](https://ngrok.com/):
   ```bash
   ngrok http 5000
   ```
2. In the Alexa Developer Console, set the endpoint to:
   ```
   https://YOUR_NGROK_URL/alexa
   ```
   (Select HTTPS, "My development endpoint is a sub-domain of a domain that has a wildcard certificate")

3. Make sure your Echo device is logged into the **same Amazon account** as the developer console — dev skills auto-appear on devices with the same account.

### 3. Voice Commands

Say: *"Alexa, abre Jarvis"* then any of these:

| Command | Action |
|---------|--------|
| `party` / `fiesta` | Party scene |
| `chill` / `relax` | Chill scene |
| `gaming` / `juego` | Gaming scene |
| `movie` / `pelicula` / `cine` | Movie scene |
| `sunset` / `atardecer` | Sunset scene |
| `focus` / `enfoque` | Focus scene |
| `sex` / `romantico` | Sex scene |
| `sync` / `spectrum` / `energy` / `pulse` | Music visualization modes |
| `stop` / `para` / `detener` | Stop music |
| `on` / `encender` | Turn lights on |
| `off` / `apagar` | Turn lights off |

## IFTTT Webhook (Alternative)

Send a POST request to `/api/webhook/ifttt` with:

```json
{"action": "party"}
```

Or structured format:
```json
{"action": "scene:Party"}
{"action": "music:start", "mode": "spectrum"}
{"action": "power:on"}
```

## Scenes

| Scene | Description |
|-------|-------------|
| Chill | Warm amber, low brightness |
| Party | Vibrant magenta + cyan, full brightness |
| Gaming | Purple + teal |
| Movie | Warm dim, cinema feel |
| Sunset | Orange gradient |
| Focus | Cool white 4000K |
| Sex | Deep red + purple, very low brightness |

## Project Structure

```
tapo-beats/
├── src/
│   ├── main.py             # Entry point, CLI
│   ├── config.py           # .env loading, settings
│   ├── discovery.py        # Tapo device LAN discovery
│   ├── bulb_controller.py  # python-kasa bulb wrapper
│   ├── audio_capture.py    # WASAPI loopback capture
│   ├── audio_analyzer.py   # FFT, beat detection, freq bands
│   ├── visualizer.py       # Audio → light color mapping
│   ├── scene_manager.py    # Scene presets
│   ├── web_ui.py           # Flask web UI + API endpoints
│   ├── alexa_skill.py      # Alexa Skill handlers
│   └── voice_control.py    # Vosk offline voice recognition
├── scenes/
│   └── default_scenes.json
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── alexa_model.json        # Alexa interaction model (import to dev console)
├── requirements.txt
└── .env.example
```

## License

MIT
