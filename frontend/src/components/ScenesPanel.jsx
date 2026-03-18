import { useState } from 'react';
import { Palette, PartyPopper, Coffee, Gamepad2, Film, Sunset, Brain, Heart } from 'lucide-react';
import { api } from '../api';
import InfoTip from './InfoTip';

const SCENE_ICONS = {
  Party: PartyPopper,
  Chill: Coffee,
  Gaming: Gamepad2,
  Movie: Film,
  Sunset: Sunset,
  Focus: Brain,
  Sex: Heart,
};

export default function ScenesPanel({ scenes, onAction }) {
  const [active, setActive] = useState(null);

  const handleScene = (scene) => {
    setActive(scene);
    api.applyScene(scene).then(onAction);
  };

  return (
    <section className="panel">
      <h2 className="panel-title"><Palette size={20} /> Escenas <InfoTip text="Ambientes predefinidos que cambian el color y brillo de todos los bombillos a la vez. Cada escena tiene colores unicos." /></h2>
      <div className="scenes-grid">
        {scenes.map((scene) => {
          const Icon = SCENE_ICONS[scene] || Palette;
          return (
            <button
              key={scene}
              className={`scene-btn ${active === scene ? 'scene-active' : ''}`}
              onClick={() => handleScene(scene)}
            >
              <Icon size={24} />
              <span>{scene}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
