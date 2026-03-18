import { Cpu } from 'lucide-react';

export default function Header({ connected }) {
  return (
    <header className="header">
      <div className="header-title">
        <Cpu size={28} className="header-icon" />
        <h1>TapoBeats</h1>
        <span className={`status-dot ${connected ? 'online' : 'offline'}`} />
      </div>
      <p className="header-subtitle">Smart Home Dashboard</p>
    </header>
  );
}
