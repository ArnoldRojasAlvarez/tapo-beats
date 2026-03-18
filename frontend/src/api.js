const BASE = '';

async function post(url, data = {}) {
  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

async function get(url) {
  const res = await fetch(`${BASE}${url}`);
  return res.json();
}

export const api = {
  getState: () => get('/api/state'),
  setColor: (hue, saturation, brightness, bulb_index) =>
    post('/api/color', { hue, saturation, brightness, bulb_index }),
  setPower: (action, bulb_index) =>
    post('/api/power', { action, bulb_index }),
  applyScene: (scene) => post('/api/scene', { scene }),
  musicStart: (mode) => post('/api/music/start', { mode }),
  musicStop: () => post('/api/music/stop'),
  voiceStart: () => post('/api/voice/start'),
  voiceStop: () => post('/api/voice/stop'),
  pcCommand: (action) => post('/api/pc', { action }),
  ambilightStart: (zones) => post('/api/ambilight/start', { zones }),
  ambilightStop: () => post('/api/ambilight/stop'),
  clapStart: () => post('/api/clap/start'),
  clapStop: () => post('/api/clap/stop'),
  routineSleep: (duration, suspend_pc) => post('/api/routine/sleep', { duration, suspend_pc }),
  routineWake: (duration) => post('/api/routine/wake', { duration }),
  routineCancel: () => post('/api/routine/cancel'),
  notifyStart: () => post('/api/notify/start'),
  notifyStop: () => post('/api/notify/stop'),
  notifyFlash: (app) => post('/api/notify/flash', { app }),
};
