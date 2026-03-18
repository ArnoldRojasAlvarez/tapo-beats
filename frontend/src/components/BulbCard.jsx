import { useState, useCallback, useRef, useEffect } from 'react';
import { HslColorPicker } from 'react-colorful';
import { Lightbulb, LightbulbOff, ChevronDown, ChevronUp, Sun } from 'lucide-react';
import { api } from '../api';

export default function BulbCard({ bulb, index, onAction, optimistic }) {
  const [expanded, setExpanded] = useState(false);
  const [localHue, setLocalHue] = useState(bulb.hue);
  const [localSat, setLocalSat] = useState(bulb.saturation);
  const [localBri, setLocalBri] = useState(bulb.brightness);
  const [localOn, setLocalOn] = useState(bulb.is_on);
  const colorDebounce = useRef(null);
  const brightDebounce = useRef(null);
  const userInteracting = useRef(false);

  // Sync from server only when not interacting
  useEffect(() => {
    if (!userInteracting.current) {
      setLocalHue(bulb.hue);
      setLocalSat(bulb.saturation);
      setLocalBri(bulb.brightness);
      setLocalOn(bulb.is_on);
    }
  }, [bulb.hue, bulb.saturation, bulb.brightness, bulb.is_on]);

  const hslColor = { h: localHue, s: localSat, l: 50 };

  const handleColorChange = useCallback((color) => {
    userInteracting.current = true;
    const h = Math.round(color.h);
    const s = Math.round(color.s);
    setLocalHue(h);
    setLocalSat(s);

    if (colorDebounce.current) clearTimeout(colorDebounce.current);
    colorDebounce.current = setTimeout(() => {
      api.setColor(h, s, localBri, index);
      setTimeout(() => { userInteracting.current = false; }, 500);
    }, 100);
  }, [index, localBri]);

  const handleBrightness = useCallback((e) => {
    userInteracting.current = true;
    const val = parseInt(e.target.value);
    setLocalBri(val);

    if (brightDebounce.current) clearTimeout(brightDebounce.current);
    brightDebounce.current = setTimeout(() => {
      api.setColor(localHue, localSat, val, index);
      setTimeout(() => { userInteracting.current = false; }, 500);
    }, 100);
  }, [localHue, localSat, index]);

  const togglePower = () => {
    const newState = !localOn;
    setLocalOn(newState);
    api.setPower(newState ? 'on' : 'off', index).then(onAction);
  };

  return (
    <div className="card bulb-card">
      <div className="bulb-header" onClick={() => setExpanded(!expanded)}>
        <div
          className="bulb-preview"
          style={{
            background: localOn
              ? `hsl(${localHue}, ${localSat}%, ${Math.max(20, localBri * 0.6)}%)`
              : '#333',
            boxShadow: localOn
              ? `0 0 ${localBri * 0.2}px hsl(${localHue}, ${localSat}%, 50%)`
              : 'none',
          }}
        />
        <div className="bulb-info">
          <span className="bulb-name">{bulb.alias}</span>
          <span className="bulb-ip">{bulb.ip}</span>
        </div>
        <div className="bulb-actions">
          <span className={`badge ${localOn ? 'badge-on' : 'badge-off'}`}>
            {localOn ? 'ON' : 'OFF'}
          </span>
          <button className={`btn-icon ${localOn ? 'btn-on' : 'btn-off'}`} onClick={(e) => { e.stopPropagation(); togglePower(); }}>
            {localOn ? <Lightbulb size={20} /> : <LightbulbOff size={20} />}
          </button>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>
      {expanded && (
        <div className="bulb-controls">
          <div className="color-picker-wrapper">
            <HslColorPicker color={hslColor} onChange={handleColorChange} />
          </div>
          <div className="brightness-control">
            <Sun size={16} className="brightness-icon" />
            <input
              type="range"
              min="1"
              max="100"
              value={localBri}
              onChange={handleBrightness}
              className="slider brightness-slider"
            />
            <span className="brightness-value">{localBri}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
