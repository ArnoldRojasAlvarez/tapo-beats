import { useState } from 'react';
import {
  MonitorPlay, Hand, Moon, Sun, Bell, BellOff,
  Zap, XCircle, Tv2
} from 'lucide-react';
import { api } from '../api';
import InfoTip from './InfoTip';

export default function FeaturesPanel({ ambilight, clap, routine, notify, onAction }) {
  const [sleepMin, setSleepMin] = useState(15);
  const [wakeMin, setWakeMin] = useState(5);

  return (
    <section className="panel">
      <h2 className="panel-title"><Zap size={20} /> Features <InfoTip text="Funciones avanzadas: Ambilight sincroniza luces con tu pantalla, aplausos detectan palmadas, rutinas automatizan el encendido/apagado, y notificaciones hacen flash al recibir alertas." /></h2>

      {/* Ambilight */}
      <h3 className="panel-subtitle">Ambilight</h3>
      <p className="feature-desc">Sincroniza los bombillos con los colores de tu pantalla</p>
      <div className="feature-row">
        <button
          className={`btn ${ambilight?.running ? 'btn-active' : ''}`}
          onClick={() => (ambilight?.running
            ? api.ambilightStop()
            : api.ambilightStart('split')
          ).then(onAction)}
        >
          <MonitorPlay size={16} />
          {ambilight?.running ? 'Detener' : 'Iniciar'}
        </button>
        {ambilight?.running && (
          <div className="zone-toggle">
            <button
              className={`pill-sm ${ambilight?.zones === 'split' ? 'pill-active' : ''}`}
              onClick={() => api.ambilightStart('split').then(onAction)}
            >
              <Tv2 size={14} /> Split
            </button>
            <button
              className={`pill-sm ${ambilight?.zones === 'average' ? 'pill-active' : ''}`}
              onClick={() => api.ambilightStart('average').then(onAction)}
            >
              Uniforme
            </button>
          </div>
        )}
      </div>

      {/* Clap Detection */}
      <h3 className="panel-subtitle">Deteccion de Aplausos</h3>
      <p className="feature-desc">Aplaude 2 veces para encender/apagar las luces</p>
      <div className="feature-row">
        <button
          className={`btn ${clap?.running ? 'btn-active' : ''}`}
          onClick={() => (clap?.running
            ? api.clapStop()
            : api.clapStart()
          ).then(onAction)}
        >
          <Hand size={16} />
          {clap?.running ? 'Desactivar' : 'Activar'}
        </button>
        {clap?.running && (
          <span className="voice-indicator listening">ESCUCHANDO</span>
        )}
      </div>

      {/* Routines */}
      <h3 className="panel-subtitle">Rutinas</h3>
      <div className="routine-grid">
        <div className="routine-card">
          <Moon size={24} className="routine-icon sleep" />
          <span className="routine-label">Buenas Noches</span>
          <div className="routine-config">
            <input
              type="range" min="5" max="30" value={sleepMin}
              onChange={(e) => setSleepMin(parseInt(e.target.value))}
              className="slider"
            />
            <span className="routine-time">{sleepMin} min</span>
          </div>
          <button
            className="btn btn-sleep"
            onClick={() => api.routineSleep(sleepMin, true).then(onAction)}
            disabled={!!routine?.active}
          >
            <Moon size={14} /> Iniciar
          </button>
        </div>
        <div className="routine-card">
          <Sun size={24} className="routine-icon wake" />
          <span className="routine-label">Buenos Dias</span>
          <div className="routine-config">
            <input
              type="range" min="1" max="15" value={wakeMin}
              onChange={(e) => setWakeMin(parseInt(e.target.value))}
              className="slider"
            />
            <span className="routine-time">{wakeMin} min</span>
          </div>
          <button
            className="btn btn-wake"
            onClick={() => api.routineWake(wakeMin).then(onAction)}
            disabled={!!routine?.active}
          >
            <Sun size={14} /> Iniciar
          </button>
        </div>
      </div>
      {routine?.active && (
        <button className="btn btn-stop" style={{ marginTop: 10 }}
          onClick={() => api.routineCancel().then(onAction)}
        >
          <XCircle size={14} /> Cancelar rutina ({routine.active})
        </button>
      )}

      {/* Notification Lights */}
      <h3 className="panel-subtitle">Notificaciones con Luz</h3>
      <p className="feature-desc">Flash en los bombillos al recibir notificaciones</p>
      <div className="feature-row">
        <button
          className={`btn ${notify?.running ? 'btn-active' : ''}`}
          onClick={() => (notify?.running
            ? api.notifyStop()
            : api.notifyStart()
          ).then(onAction)}
        >
          {notify?.running ? <BellOff size={16} /> : <Bell size={16} />}
          {notify?.running ? 'Desactivar' : 'Activar'}
        </button>
        {notify?.running && (
          <button className="btn" onClick={() => api.notifyFlash('whatsapp').then(onAction)}>
            Test Flash
          </button>
        )}
      </div>
    </section>
  );
}
