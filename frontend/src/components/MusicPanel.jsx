import { Music, Play, Square } from 'lucide-react';
import { api } from '../api';

const MODES = ['spectrum', 'energy', 'pulse', 'dual', 'complementary', 'chase', 'sync'];

export default function MusicPanel({ music, onAction }) {
  const handleStart = (mode) => {
    api.musicStart(mode).then(onAction);
  };

  const handleStop = () => {
    api.musicStop().then(onAction);
  };

  return (
    <section className="panel">
      <h2 className="panel-title"><Music size={20} /> Musica</h2>
      <div className="music-modes">
        {MODES.map((mode) => (
          <button
            key={mode}
            className={`pill ${music?.active && music?.mode === mode ? 'pill-active' : ''}`}
            onClick={() => handleStart(mode)}
          >
            {mode}
          </button>
        ))}
      </div>
      <div className="music-controls">
        <button className="btn btn-stop" onClick={handleStop} disabled={!music?.active}>
          <Square size={16} /> Stop
        </button>
      </div>
    </section>
  );
}
