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
};
