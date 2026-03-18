import { useAppState } from './hooks/useAppState';
import Header from './components/Header';
import BulbsPanel from './components/BulbsPanel';
import ScenesPanel from './components/ScenesPanel';
import MusicPanel from './components/MusicPanel';
import PcControlPanel from './components/PcControlPanel';
import VoicePanel from './components/VoicePanel';
import CommandsCard from './components/CommandsCard';
import MasterControls from './components/MasterControls';
import FeaturesPanel from './components/FeaturesPanel';

export default function App() {
  const { state, error, refresh, useMock, optimistic } = useAppState(2000);

  if (!state && !error) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Conectando...</p>
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="loading">
        <p className="error-text">Error de conexion: {error}</p>
        <button className="btn" onClick={refresh}>Reintentar</button>
      </div>
    );
  }

  return (
    <div className="app">
      <Header connected={!error && !useMock} />
      <main className="dashboard">
        <MasterControls onAction={refresh} optimistic={optimistic} bulbs={state.bulbs} />
        <BulbsPanel bulbs={state.bulbs} onAction={refresh} optimistic={optimistic} />
        <ScenesPanel scenes={state.scenes} onAction={refresh} optimistic={optimistic} />
        <MusicPanel music={state.music} onAction={refresh} optimistic={optimistic} />
        <PcControlPanel onAction={refresh} />
        <FeaturesPanel
          ambilight={state.ambilight}
          clap={state.clap}
          routine={state.routine}
          notify={state.notify}
          onAction={refresh}
        />
        <VoicePanel voice={state.voice} onAction={refresh} />
        <CommandsCard />
      </main>
    </div>
  );
}
