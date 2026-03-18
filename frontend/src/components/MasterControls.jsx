import { Power, PowerOff } from 'lucide-react';
import { api } from '../api';

export default function MasterControls({ onAction }) {
  return (
    <div className="master-controls">
      <button className="master-btn master-on" onClick={() => api.setPower('on').then(onAction)}>
        <Power size={18} /> Encender Todo
      </button>
      <button className="master-btn master-off" onClick={() => api.setPower('off').then(onAction)}>
        <PowerOff size={18} /> Apagar Todo
      </button>
    </div>
  );
}
