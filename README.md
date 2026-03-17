<div align="center">

<img src="https://readme-typing-svg.demolabs.com?font=Fira+Code&weight=600&size=30&pause=1000&color=7AA2F7&center=true&vCenter=true&width=500&lines=TapoBeats+%F0%9F%92%A1%F0%9F%8E%B5;Music-Reactive+Smart+Lighting;Alexa+Voice+Control" alt="TapoBeats" />

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![Alexa](https://img.shields.io/badge/Alexa-Skill-00CAFF?style=for-the-badge&logo=amazon-alexa&logoColor=white)
![TP-Link](https://img.shields.io/badge/TP--Link-Tapo_L530-4ACBD6?style=for-the-badge&logo=tp-link&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Control your TP-Link Tapo smart bulbs with music in real-time.**
Beat detection, frequency analysis, 7 scene presets, and hands-free Alexa voice control.

[Features](#features) · [Setup](#setup) · [Voice Commands](#voice-commands) · [API](#ifttt-webhook-api)

</div>

---

## Features

<table>
  <tr>
    <td width="50%">
      <h3>🎵 Music Sync</h3>
      <p>Captures system audio via WASAPI loopback and maps frequency/beat data to light colors in real-time. No mic needed — it listens to whatever is playing on your PC.</p>
    </td>
    <td width="50%">
      <h3>🗣️ Alexa Skill ("Jarvis")</h3>
      <p>Custom Alexa skill to trigger scenes and music modes by voice on any Echo device. Bilingual support (English + Spanish).</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎨 7 Visualization Modes</h3>
      <p><code>spectrum</code> · <code>energy</code> · <code>pulse</code> · <code>dual</code> · <code>complementary</code> · <code>chase</code> · <code>sync</code></p>
    </td>
    <td width="50%">
      <h3>🌐 Web Dashboard</h3>
      <p>Flask-powered UI for manual control from any device on your LAN — phone, tablet, or PC.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>💡 7 Scene Presets</h3>
      <p><code>Chill</code> · <code>Party</code> · <code>Gaming</code> · <code>Movie</code> · <code>Sunset</code> · <code>Focus</code> · <code>Sex</code></p>
    </td>
    <td width="50%">
      <h3>🎙️ Offline Voice Control</h3>
      <p>Local speech recognition via Vosk — works without internet, dual-language (EN/ES).</p>
    </td>
  </tr>
</table>

---

## Requirements

| Requirement | Details |
|:-----------:|---------|
| ![Python](https://img.shields.io/badge/-Python_3.11+-3776AB?style=flat-square&logo=python&logoColor=white) | Python 3.11 or newer |
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

# 3. Launch
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

## Alexa Skill Setup ("Jarvis")

> Custom Alexa skill — no third-party service fees, no cloud dependency beyond the initial handshake.

### 1. Create the Skill
1. Go to the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Create a new **custom** skill with invocation name **Jarvis**
3. In the JSON Editor, import `alexa_model.json` from this repo
4. Build the model

### 2. Configure the Endpoint
1. Start ngrok: `ngrok http 5000`
2. In the Alexa console, set the HTTPS endpoint to `https://YOUR_NGROK_URL/alexa`
3. Your Echo device must use the **same Amazon account** as the developer console

---

## Voice Commands

Say *"Alexa, abre Jarvis"* followed by:

| Category | Commands |
|----------|----------|
| **Scenes** | `party` · `chill` · `gaming` · `movie` · `sunset` · `focus` · `sex` |
| **Music Modes** | `sync` · `spectrum` · `energy` · `pulse` · `chase` |
| **Power** | `on` / `encender` · `off` / `apagar` |
| **Stop** | `stop` / `para` / `detener` |

> Supports both English and Spanish keywords.

---

## IFTTT Webhook API

`POST /api/webhook/ifttt`

```json
// Natural language
{"action": "party"}

// Structured
{"action": "scene:Party"}
{"action": "music:start", "mode": "spectrum"}
{"action": "power:on"}
{"action": "power:off"}
```

---

## Scenes

| Scene | Bulb 1 | Bulb 2 | Vibe |
|-------|--------|--------|------|
| **Chill** | Warm amber, low | Warm amber, dim | Relaxation |
| **Party** | Magenta, full | Cyan, full | High energy |
| **Gaming** | Purple | Teal | Immersive |
| **Movie** | Warm dim | Warm dim | Cinema |
| **Sunset** | Deep orange | Golden | Warm atmosphere |
| **Focus** | Cool white 4000K | Cool white 4000K | Productivity |
| **Sex** | Deep red | Purple | Ambient mood |

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
│   ├── visualizer.py         # Audio → light mapping
│   ├── scene_manager.py      # Scene presets
│   ├── web_ui.py             # Flask dashboard + APIs
│   ├── alexa_skill.py        # Alexa Skill handlers
│   └── voice_control.py      # Vosk offline recognition
├── scenes/
│   └── default_scenes.json
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── alexa_model.json           # Alexa interaction model
├── requirements.txt
└── .env.example
```

---

<div align="center">

**Built with** ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/-Flask-000?style=flat-square&logo=flask&logoColor=white) ![Alexa](https://img.shields.io/badge/-Alexa_Skills_Kit-00CAFF?style=flat-square&logo=amazon-alexa&logoColor=white) ![Kasa](https://img.shields.io/badge/-python--kasa-4ACBD6?style=flat-square)

MIT License

</div>
