import { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp } from 'lucide-react';

const COMMANDS = [
  { category: 'Escenas', color: '#9b59b6', items: ['party', 'chill', 'gaming', 'movie', 'sunset', 'focus', 'sex'] },
  { category: 'Musica', color: '#1abc9c', items: ['sync', 'spectrum', 'energy', 'pulse', 'dual', 'chase', 'stop'] },
  { category: 'Luces', color: '#2ecc71', items: ['encender', 'apagar'] },
  { category: 'PC', color: '#e67e22', items: ['apagar pc', 'reiniciar', 'suspender', 'bloquear', 'cancelar apagado'] },
  { category: 'Volumen', color: '#3498db', items: ['subir volumen', 'bajar volumen', 'mutear'] },
  { category: 'Apps', color: '#e91e63', items: ['spotify', 'youtube', 'steam', 'crunchyroll', 'whatsapp', 'outlook', 'wallpaper'] },
];

export default function CommandsCard() {
  const [open, setOpen] = useState(false);

  return (
    <section className="panel commands-panel">
      <h2 className="panel-title clickable" onClick={() => setOpen(!open)}>
        <Terminal size={20} /> Comandos Jarvis
        {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </h2>
      {open && (
        <div className="commands-grid">
          {COMMANDS.map(({ category, color, items }) => (
            <div key={category} className="command-group">
              <h4 style={{ color }}>{category}</h4>
              <div className="command-tags">
                {items.map((item) => (
                  <span key={item} className="tag" style={{ borderColor: color, color }}>{item}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
