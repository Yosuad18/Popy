import { useEffect, useState } from 'react';

const STATUS_CONFIG = {
  connected: { color: 'bg-emerald-400', text: 'OpenAI Conectado', pulse: true },
  demo: { color: 'bg-amber-400', text: 'Modo Demo Activo', pulse: true },
  offline: { color: 'bg-red-400', text: 'Desconectado', pulse: false },
};

export default function Header({ health, onReset }) {
  const [statusKey, setStatusKey] = useState('offline');

  useEffect(() => {
    if (!health) {
      setStatusKey('offline');
    } else if (health.openai_configured) {
      setStatusKey('connected');
    } else {
      setStatusKey('demo');
    }
  }, [health]);

  const status = STATUS_CONFIG[statusKey];

  return (
    <header className="relative overflow-hidden bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-600 text-white py-4 px-5 shadow-md">
      <div
        className="pointer-events-none absolute -top-16 -right-16 w-56 h-56 rounded-full opacity-20 blur-3xl"
        style={{ background: 'radial-gradient(circle, #a7f3d0 0%, transparent 70%)' }}
      />
      <div className="relative flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-full bg-white/15 ring-1 ring-white/25 backdrop-blur-sm shrink-0">
            <span aria-hidden="true" className="text-lg leading-none">🛍️</span>
          </div>
          <div className="min-w-0">
            <h1 className="font-display font-bold text-[15px] leading-tight truncate">
              Tienda Online — Asistente de Compras
            </h1>
            <p className="status-pill text-emerald-100">
              <span
                className={`status-dot ${status.color} ${status.pulse ? 'animate-pulse' : ''}`}
              />
              <span>{status.text}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <a
            href="/chat/graph?format=html"
            target="_blank"
            rel="noreferrer"
            className="header-btn bg-white/15 hover:bg-white/25"
          >
            📊 Grafo
          </a>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="header-btn bg-white/15 hover:bg-white/25"
          >
            📖 Docs
          </a>
          <button
            onClick={onReset}
            title="Nueva Conversación"
            className="header-btn bg-red-500/80 hover:bg-red-500"
          >
            🔄 Reiniciar
          </button>
        </div>
      </div>
    </header>
  );
}