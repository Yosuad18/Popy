import TypingIndicator from './TypingIndicator';

const PROMPTS = [
  { label: '🎧 Electrónica', prompt: 'Muéstrame productos de electrónica' },
  { label: '🔄 Política devolución', prompt: '¿Cuáles son sus políticas de devolución?' },
  { label: '🛒 Añadir al carrito', prompt: 'Añade el producto 1 al carrito' },
  { label: '🛒 Ver carrito', prompt: 'Ver mi carrito de compras' },
];

export default function QuickPrompts({ onSelect, disabled }) {
  return (
    <div className="bg-[#fdfaf6] px-4 py-2.5 border-b border-[#ece7e0] flex items-center gap-2 overflow-x-auto chat-scroll">
      <span className="font-display font-semibold text-xs text-[#b0a99b] uppercase tracking-wider shrink-0">
        Prueba rápida
      </span>
      {PROMPTS.map((item, i) => (
        <button
          key={item.label}
          className={`chip animate-fade-up stagger-${i + 1} ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
          onClick={() => onSelect(item.prompt)}
          disabled={disabled}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}