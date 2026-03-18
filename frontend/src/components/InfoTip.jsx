import { useState } from 'react';
import { Info } from 'lucide-react';

export default function InfoTip({ text }) {
  const [show, setShow] = useState(false);

  return (
    <span className="info-tip-wrapper">
      <button
        className="info-tip-btn"
        onClick={(e) => { e.stopPropagation(); setShow(!show); }}
        onBlur={() => setShow(false)}
        aria-label="Info"
      >
        <Info size={14} />
      </button>
      {show && (
        <div className="info-tip-popup">
          {text}
        </div>
      )}
    </span>
  );
}
