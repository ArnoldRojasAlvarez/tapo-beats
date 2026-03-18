<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=30&pause=1000&color=7AA2F7&center=true&vCenter=true&width=500&lines=TapoBeats+%F0%9F%92%A1%F0%9F%8E%B5;Music-Reactive+Smart+Lighting;Alexa+Voice+Control;PC+Automation;Ambilight+%7C+Clap+Detection" alt="TapoBeats" />

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![Alexa](https://img.shields.io/badge/Alexa-Skill-00CAFF?style=for-the-badge&logo=amazon-alexa&logoColor=white)
![TP-Link](https://img.shields.io/badge/TP--Link-Tapo_L530-4ACBD6?style=for-the-badge&logo=tp-link&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Full smart home control system for TP-Link Tapo bulbs.**
Music sync, Ambilight, clap detection, sleep/wake routines, notification lights, PC automation, and Alexa voice control — all from one dashboard.

[Features](#features) · [Setup](#setup) · [Dashboard](#react-dashboard) · [Voice Commands](#voice-commands) · [Advanced Features](#advanced-features) · [API](#api-endpoints)

</div>

---

## Features

<table>
  <tr>
    <td width="50%">
      <h3>🎵 Music Sync</h3>
      <p>Captures system audio via WASAPI loopback and maps frequency/beat data to light colors in real-time. 7 visualization modes: <code>spectrum</code> · <code>energy</code> · <code>pulse</code> · <code>dual</code> · <code>complementary</code> · <code>chase</code> · <code>sync</code></p>
    </td>
    <td width="50%">
      <h3>🖥️ Ambilight</h3>
      <p>Syncs bulb colors with your screen content in real-time. Captures dominant colors from your display and maps them to the bulbs. Split mode (left/right) or uniform mode.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🗣️ Alexa Skill ("Jarvis")</h3>
      <p>Custom Alexa skill with multi-turn dialog. Say "apagar" and Jarvis asks what to turn off — lights, PC, or an app. Bilingual (EN/ES) with 45+ synonyms.</p>
    </td>
    <td width="50%">
      <h3>👏 Clap Detection</h3>
      <p>Double clap to toggle lights on/off. Uses your microphone with configurable sensitivity and cooldown to prevent false triggers.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🌙 Sleep & Wake Routines</h3>
      <p><strong>Sleep:</strong> Gradually dims lights from warm amber to off over 5-30 min, then suspends PC. <strong>Wake:</strong> Simulates sunrise from deep red to bright daylight over 1-15 min.</p>
    </td>
    <td width="50%">
      <h3>🔔 Notification Lights</h3>
      <p>Flashes bulbs when apps request attention in the taskbar. Each app has a unique color: Discord (purple), WhatsApp (green), Outlook (blue), etc.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🖥️ PC Control</h3>
      <p>Shutdown, restart, sleep, lock, volume control, and launch apps (Spotify, YouTube, Steam, Crunchyroll, WhatsApp, Outlook, Wallpaper Engine) — all by voice.</p>
    </td>
    <td width="50%">
      <h3>⚛️ React Dashboard</h3>
      <p>Modern dark-themed UI with interactive color picker, real-time state polling, optimistic updates, and mobile-responsive design. Built with Vite + React 18.</p>
    </td>
  </tr>
</table>

---

## Requirements

| Requirement | Details |
|:-----------:|---------|
| ![Python](https://img.shields.io/badge/-Python_3.11+-3776AB?style=flat-square&logo=python&logoColor=white) | Python 3.11 or newer |
| ![Node](https://img.shields.io/badge/-Node.js_18+-339933?style=flat-square&logo=node.js&logoColor=white) | For building the React frontend |
| ![Windows](https://img.shields.io/badge/-Windows_10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white) | WASAPI loopback for audio capture |
| ![TP-Link](https://img.shields.io/badge/-Tapo_L530-4ACBD6?style=flat-square&logo=tp-link&logoColor=white) | Bulbs on the same local network |
| ![Alexa](https://img.shields.io/badge/-Echo_(optional)-00CAFF?style=flat-square&logo=amazon-alexa&logoColor=white) | For Alexa skill integration |
| ![Ngrok](https://img.shields.io/badge/-Ngrok_(optional)-1F1E37?style=flat-square&logo=ngrok&logoColor=white) | To expose local server to Alexa |

---

## Setup

```bash
# 1. Clone and install
git clone https://github.com/ArnoldRojasAlvarez/tapo-beats.git
cd tapo-beats
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure credentials
copy .env.example .env
# Edit .env with your TP-Link cloud email & password

# 3. Build the React frontend
cd frontend
npm install
npm run build
cd ..

# 4. Launch
python -m src.main serve
# Open http://localhost:5000
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m src.main serve` | Start web UI + all integrations |
| `python -m src.main music <mode>` | Start music mode (spectrum/energy/pulse/dual) |
| `python -m src.main test-bulbs` | Discover bulbs, print state, cycle RGB |
| `python -m src.main test-audio` | Capture 10s of system audio, print band energies |

---

## React Dashboard

Modern dark-themed dashboard built with **Vite + React 18**, served by Flask.

### Panels

| Panel | Description |
|-------|-------------|
| **Bombillos** | Individual bulb control with HSL color picker wheel, brightness slider, and power toggle. Click to expand. |
| **Escenas** | One-click scene presets with icons (Party, Chill, Gaming, Movie, Sunset, Focus, Sex). |
| **Musica** | Pill-button selector for 7 music visualization modes with start/stop. |
| **Control PC** | System commands (shutdown, restart, sleep, lock), volume control, and app launchers with color-coded icons. |
| **Features** | Advanced features: Ambilight, Clap Detection, Sleep/Wake Routines, Notification Lights. |
| **Voz** | Toggle for Vosk offline voice recognition (Spanish + English). |
| **Comandos Jarvis** | Collapsible reference card of all available voice commands. |

### Tech Stack

- **react-colorful** — HSL color picker (2KB, zero dependencies)
- **lucide-react** — Tree-shakeable icon set
- **Optimistic updates** — UI reflects changes instantly, no 2s poll delay
- **Polling** — `GET /api/state` every 2 seconds for real-time sync
- **Mobile responsive** — Works on phone, tablet, and desktop

---

## Advanced Features

### 🖥️ Ambilight (Screen Sync)

Captures dominant colors from your screen in real-time and applies them to the bulbs.

| Setting | Description |
|---------|-------------|
| **Split mode** | Left half of screen → Bulb 1, right half → Bulb 2 |
| **Uniform mode** | Average color → Both bulbs |
| **Capture rate** | 10 FPS, downscaled to 40x22 for speed |
| **Smart filtering** | Weighted toward saturated, bright pixels (ignores dark/gray UI elements) |

### 👏 Clap Detection

Detects double claps to toggle lights. Uses the Razer BlackShark V2 microphone (auto-detected, falls back to default input).

| Parameter | Value |
|-----------|-------|
| Threshold | 0.06 (configurable in `src/clap_detector.py`) |
| Min gap | 0.1s between claps |
| Max gap | 0.6s between claps |
| Cooldown | 1.5s after trigger |

### 🌙 Sleep & Wake Routines

**Sleep (Buenas Noches):**
1. Sets warm orange (hue 30) at 50% brightness
2. Gradually shifts to deep red while dimming over configurable duration (5-30 min)
3. Turns off lights
4. Suspends PC (optional)

**Wake (Buenos Dias):**
1. Turns on at deep red, 1% brightness
2. Gradually shifts to warm daylight while brightening over configurable duration (1-15 min)
3. Ends at bright warm white (hue 40, 100% brightness)

### 🔔 Notification Lights

Monitors the Windows taskbar for apps requesting attention (flashing). When detected, the bulbs flash 3 times in the app's color, then restore the previous state.

| App | Flash Color |
|-----|-------------|
| Discord | Purple-blue (hue 235) |
| WhatsApp | Green (hue 130) |
| Outlook/Mail | Blue (hue 210) |
| Teams | Purple (hue 250) |
| Telegram | Light blue (hue 200) |
| Steam | Steel blue (hue 210) |
| Others | Orange (hue 50) |

---

## Alexa Skill Setup ("Jarvis")

### 1. Create the Skill
1. Go to the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Create a new **custom** skill with invocation name **Jarvis**
3. In the JSON Editor, import `alexa_model.json` from this repo
4. Build the model

### 2. Configure the Endpoint
1. Start ngrok: `ngrok http 5000 --domain YOUR_DOMAIN`
2. In the Alexa console, set the HTTPS endpoint to `https://YOUR_NGROK_URL/alexa`
3. Your Echo device must use the **same Amazon account** as the developer console

### Multi-Turn Dialog

When you say an ambiguous command like "apagar" (turn off), Jarvis asks for clarification:

```
You: "Jarvis, apagar"
Jarvis: "Que apago? Luces, P.C., o una app?"
You: "Luces"
Jarvis: "Listo"
```

```
You: "Jarvis, encender"
Jarvis: "Que enciendo? Luces o una app?"
You: "Spotify"
Jarvis: "Spotify abierto"
```

---

## Voice Commands

Say *"Alexa, abre Jarvis"* followed by:

| Category | Commands |
|----------|----------|
| **Scenes** | `party` · `chill` · `gaming` · `movie` · `sunset` · `focus` · `sex` |
| **Music Modes** | `sync` · `spectrum` · `energy` · `pulse` · `dual` · `chase` · `complementary` |
| **Lights** | `encender` / `apagar` (triggers follow-up dialog) |
| **Lights (direct)** | `encender luces` · `apagar luces` · `on` · `off` |
| **Stop** | `stop` / `para` / `detener` |
| **PC Power** | `apagar pc` · `reiniciar` · `suspender` · `bloquear` · `cancelar apagado` |
| **Volume** | `subir volumen` · `bajar volumen` · `mutear` |
| **Apps** | `spotify` · `youtube` · `crunchyroll` · `whatsapp` · `outlook` · `steam` · `wallpaper` |
| **Help** | `ayuda` · `help` · `comandos` (sends command list to Alexa app) |

> All commands support multiple Spanish and English synonyms. See `alexa_model.json` for the full list.

---

## Auto-Start

Run TapoBeats automatically when Windows starts:

```bash
# Option 1: Manual silent launch (no console window)
start_silent.vbs

# Option 2: Install auto-start (run as Administrator, once)
install_autostart.bat

# To remove auto-start
schtasks /delete /tn "TapoBeats" /f
```

> **Tip:** Claim a [free static ngrok domain](https://dashboard.ngrok.com/domains) and set `NGROK_DOMAIN` in your `.env` so the Alexa endpoint URL never changes.

---

## API Endpoints

### State & Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/state` | Complete app state (bulbs, scenes, music, voice, features) |
| `POST` | `/api/color` | Set bulb color `{hue, saturation, brightness, bulb_index}` |
| `POST` | `/api/power` | Power control `{action: "on"/"off"/"toggle", bulb_index}` |
| `POST` | `/api/scene` | Apply scene `{scene: "Party"}` |
| `POST` | `/api/pc` | PC command `{action: "shutdown"/"spotify"/"volume_up"/...}` |

### Music

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/music/start` | Start visualizer `{mode: "spectrum"}` |
| `POST` | `/api/music/stop` | Stop visualizer |

### Advanced Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ambilight/start` | Start ambilight `{zones: "split"/"average"}` |
| `POST` | `/api/ambilight/stop` | Stop ambilight |
| `POST` | `/api/clap/start` | Start clap detection |
| `POST` | `/api/clap/stop` | Stop clap detection |
| `POST` | `/api/routine/sleep` | Sleep routine `{duration: 15, suspend_pc: true}` |
| `POST` | `/api/routine/wake` | Wake routine `{duration: 5}` |
| `POST` | `/api/routine/cancel` | Cancel active routine |
| `POST` | `/api/notify/start` | Start notification monitoring |
| `POST` | `/api/notify/stop` | Stop notification monitoring |
| `POST` | `/api/notify/flash` | Manual flash `{app: "discord"}` |

### Voice & Integrations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice/start` | Start offline voice recognition |
| `POST` | `/api/voice/stop` | Stop voice recognition |
| `GET` | `/api/voice/status` | Voice status |
| `POST` | `/api/webhook/ifttt` | IFTTT/Alexa webhook (requires API key) |
| `POST` | `/alexa` | Alexa Skill endpoint |

---

## Project Structure

```
tapo-beats/
├── src/
│   ├── main.py              # Entry point & CLI
│   ├── config.py             # Environment config
│   ├── discovery.py          # LAN device discovery
│   ├── bulb_controller.py    # python-kasa wrapper
│   ├── audio_capture.py      # WASAPI loopback
│   ├── audio_analyzer.py     # FFT & beat detection
│   ├── visualizer.py         # Audio → light mapping (7 modes)
│   ├── scene_manager.py      # Scene presets (JSON-driven)
│   ├── web_ui.py             # Flask dashboard + all API endpoints
│   ├── alexa_skill.py        # Alexa Skill handlers (multi-turn dialog)
│   ├── voice_control.py      # Vosk offline recognition (EN/ES)
│   ├── pc_control.py         # PC automation (shutdown, apps, volume)
│   ├── ambilight.py          # Screen color sync
│   ├── clap_detector.py      # Double clap detection
│   ├── routines.py           # Sleep/wake gradual transitions
│   └── notify_lights.py      # Taskbar flash notification lights
├── frontend/                  # React 18 + Vite dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js            # API client
│   │   ├── hooks/useAppState.js  # State polling + optimistic updates
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── BulbCard.jsx       # Color picker + brightness
│   │       ├── BulbsPanel.jsx
│   │       ├── ScenesPanel.jsx
│   │       ├── MusicPanel.jsx
│   │       ├── PcControlPanel.jsx
│   │       ├── FeaturesPanel.jsx  # Ambilight, clap, routines, notify
│   │       ├── VoicePanel.jsx
│   │       ├── CommandsCard.jsx
│   │       ├── MasterControls.jsx
│   │       └── InfoTip.jsx        # Tooltip component
│   └── vite.config.js
├── scenes/
│   └── default_scenes.json
├── alexa_model.json           # Alexa interaction model (45+ synonyms)
├── start_tapobeats.bat        # Manual launcher
├── start_silent.vbs           # Silent background launcher
├── install_autostart.bat      # Auto-start installer
├── requirements.txt
└── .env.example
```

---

<div align="center">

**Built with** ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) ![React](https://img.shields.io/badge/-React-61DAFB?style=flat-square&logo=react&logoColor=black) ![Flask](https://img.shields.io/badge/-Flask-000?style=flat-square&logo=flask&logoColor=white) ![Alexa](https://img.shields.io/badge/-Alexa_Skills_Kit-00CAFF?style=flat-square&logo=amazon-alexa&logoColor=white) ![Kasa](https://img.shields.io/badge/-python--kasa-4ACBD6?style=flat-square)

MIT License

</div>
