import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';

const MOCK_STATE = {
  bulbs: [
    { alias: "Bombillo 1", ip: "192.168.137.x", is_on: true, hue: 270, saturation: 80, brightness: 70 },
    { alias: "Bombillo 2", ip: "192.168.137.x", is_on: true, hue: 180, saturation: 90, brightness: 50 },
  ],
  scenes: ["Party", "Chill", "Gaming", "Movie", "Sunset", "Focus", "Sex"],
  music: { active: false, mode: null },
  voice: { listening: false },
  ambilight: { running: false, zones: "split" },
  clap: { running: false },
  routine: { active: null },
  notify: { running: false },
};

export function useAppState(interval = 2000) {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [useMock, setUseMock] = useState(false);
  const mockRef = useRef(false);

  const refresh = useCallback(async () => {
    try {
      const data = await api.getState();
      if (data && data.bulbs) {
        setState(data);
        setError(null);
        setUseMock(false);
        mockRef.current = false;
      } else {
        throw new Error('Invalid response');
      }
    } catch (err) {
      if (!mockRef.current) {
        setState(MOCK_STATE);
        setUseMock(true);
        mockRef.current = true;
      }
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, interval);
    return () => clearInterval(id);
  }, [refresh, interval]);

  return { state, error: useMock ? null : error, refresh, useMock };
}
