import { useState, useCallback, useRef } from 'react';
import { HslColorPicker } from 'react-colorful';
import { Lightbulb, LightbulbOff, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../api';

export default function BulbCard({ bulb, index, onAction }) {
  const [expanded, setExpanded] = useState(false);
  const [brightness, setBrightness] = useState(bulb.brightness);
  const debounceRef = useRef(null);

  const hslColor = {
    h: bulb.hue,
    s: bulb.saturation,
    l: 50,
  };

  const handleColorChange = useCallback((color) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      api.setColor(Math.round(color.h), Math.round(color.s), brightness, index).then(onAction);
    }, 300);
  }, [index, brightness, onAction]);

  const handleBrightness = useCallback((e) => {
    const val = parseInt(e.target.value);
    setBrightness(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      api.setColor(bulb.hue, bulb.saturation, val, index).then(onAction);
    }, 300);
  }, [bulb.hue, bulb.saturation, index, onAction]);

  const togglePower = () => {
    api.setPower(bulb.is_on ? 'off' : 'on', index).then(onAction);
  };

  return (
    <div className="card bulb-card">
      <div className="bulb-header" onClick={() => setExpanded(!expanded)}>
        <div
          className="bulb-preview"
          style={{ background: bulb.is_on ? `hsl(${bulb.hue}, ${bulb.saturation}%, 50%)` : '#333' }}
        />
        <div className="bulb-info">
          <span className="bulb-name">{bulb.alias}</span>
          <span className="bulb-ip">{bulb.ip}</span>
        </div>
        <div className="bulb-actions">
          <span className={`badge ${bulb.is_on ? 'badge-on' : 'badge-off'}`}>
            {bulb.is_on ? 'ON' : 'OFF'}
          </span>
          <button className={`btn-icon ${bulb.is_on ? 'btn-on' : 'btn-off'}`} onClick={(e) => { e.stopPropagation(); togglePower(); }}>
            {bulb.is_on ? <Lightbulb size={20} /> : <LightbulbOff size={20} />}
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
            <label>Brillo: {brightness}%</label>
            <input
              type="range"
              min="1"
              max="100"
              value={brightness}
              onChange={handleBrightness}
              className="slider"
            />
          </div>
        </div>
      )}
    </div>
  );
}
