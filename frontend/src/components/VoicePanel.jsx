import { Mic, MicOff } from 'lucide-react';
import { api } from '../api';

export default function VoicePanel({ voice, onAction }) {
  const listening = voice?.listening || false;

  const toggle = () => {
    (listening ? api.voiceStop() : api.voiceStart()).then(onAction);
  };

  return (
    <section className="panel">
      <h2 className="panel-title">{listening ? <Mic size={20} /> : <MicOff size={20} />} Voz</h2>
      <div className="voice-row">
        <button className={`btn ${listening ? 'btn-active' : ''}`} onClick={toggle}>
          {listening ? <><Mic size={16} /> Escuchando...</> : <><MicOff size={16} /> Activar Voz</>}
        </button>
        <span className={`voice-indicator ${listening ? 'listening' : ''}`}>
          {listening ? 'ACTIVO' : 'INACTIVO'}
        </span>
      </div>
    </section>
  );
}
