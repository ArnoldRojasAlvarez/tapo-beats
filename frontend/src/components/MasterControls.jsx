import { Power, PowerOff } from 'lucide-react';
import { api } from '../api';

export default function MasterControls({ onAction, optimistic, bulbs }) {
  const handlePower = (action) => {
    // Optimistic: update all bulbs instantly
    if (optimistic && bulbs) {
      optimistic((prev) => ({
        ...prev,
        bulbs: prev.bulbs.map((b) => ({ ...b, is_on: action === 'on' })),
      }));
    }
    api.setPower(action).then(onAction);
  };

  return (
    <div className="master-controls">
      <button className="master-btn master-on" onClick={() => handlePower('on')}>
        <Power size={18} /> Encender Todo
      </button>
      <button className="master-btn master-off" onClick={() => handlePower('off')}>
        <PowerOff size={18} /> Apagar Todo
      </button>
    </div>
  );
}
