import {
  Monitor, Power, RotateCcw, Moon, Lock, XCircle,
  Volume2, VolumeX, Volume1,
  Music, Youtube, Gamepad2, Tv, MessageCircle, Mail, Image
} from 'lucide-react';
import { api } from '../api';
import InfoTip from './InfoTip';

const SYSTEM_CMDS = [
  { action: 'shutdown', label: 'Apagar', icon: Power, color: '#e74c3c' },
  { action: 'restart', label: 'Reiniciar', icon: RotateCcw, color: '#f39c12' },
  { action: 'sleep', label: 'Suspender', icon: Moon, color: '#9b59b6' },
  { action: 'lock', label: 'Bloquear', icon: Lock, color: '#3498db' },
  { action: 'cancel_shutdown', label: 'Cancelar', icon: XCircle, color: '#2ecc71' },
];

const VOLUME_CMDS = [
  { action: 'volume_up', label: 'Subir', icon: Volume2 },
  { action: 'volume_down', label: 'Bajar', icon: Volume1 },
  { action: 'mute', label: 'Mute', icon: VolumeX },
];

const APP_CMDS = [
  { action: 'spotify', label: 'Spotify', icon: Music, color: '#1DB954' },
  { action: 'youtube', label: 'YouTube', icon: Youtube, color: '#FF0000' },
  { action: 'steam', label: 'Steam', icon: Gamepad2, color: '#1b2838' },
  { action: 'crunchyroll', label: 'Crunchyroll', icon: Tv, color: '#F47521' },
  { action: 'whatsapp', label: 'WhatsApp', icon: MessageCircle, color: '#25D366' },
  { action: 'outlook', label: 'Outlook', icon: Mail, color: '#0078D4' },
  { action: 'wallpaper', label: 'Wallpaper', icon: Image, color: '#e91e63' },
];

export default function PcControlPanel({ onAction }) {
  const handleCmd = (action) => {
    api.pcCommand(action).then(onAction);
  };

  return (
    <section className="panel">
      <h2 className="panel-title"><Monitor size={20} /> Control PC <InfoTip text="Controla tu PC remotamente: apagar, reiniciar, suspender, bloquear, ajustar volumen o abrir apps. Funciona por voz con Jarvis tambien." /></h2>

      <h3 className="panel-subtitle">Sistema</h3>
      <div className="pc-grid">
        {SYSTEM_CMDS.map(({ action, label, icon: Icon, color }) => (
          <button key={action} className="pc-btn" onClick={() => handleCmd(action)}>
            <Icon size={22} style={{ color }} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      <h3 className="panel-subtitle">Volumen</h3>
      <div className="pc-grid">
        {VOLUME_CMDS.map(({ action, label, icon: Icon }) => (
          <button key={action} className="pc-btn" onClick={() => handleCmd(action)}>
            <Icon size={22} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      <h3 className="panel-subtitle">Apps</h3>
      <div className="pc-grid">
        {APP_CMDS.map(({ action, label, icon: Icon, color }) => (
          <button key={action} className="pc-btn" onClick={() => handleCmd(action)}>
            <Icon size={22} style={{ color }} />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
