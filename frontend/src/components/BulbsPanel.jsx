import BulbCard from './BulbCard';
import InfoTip from './InfoTip';
import { Lightbulb } from 'lucide-react';

export default function BulbsPanel({ bulbs, onAction }) {
  if (!bulbs || bulbs.length === 0) return null;

  return (
    <section className="panel">
      <h2 className="panel-title"><Lightbulb size={20} /> Bombillos <InfoTip text="Controla cada bombillo individualmente. Toca para expandir y usar el color picker o ajustar el brillo." /></h2>
      <div className="bulbs-list">
        {bulbs.map((bulb, i) => (
          <BulbCard key={i} bulb={bulb} index={i} onAction={onAction} />
        ))}
      </div>
    </section>
  );
}
