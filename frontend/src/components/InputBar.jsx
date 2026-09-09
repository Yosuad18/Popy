import { useEffect, useRef, useState } from 'react';

export default function InputBar({
  isStreaming,
  isBusy,
  threadId,
  onStreamingChange,
  onSend,
}) {
  const [text, setText] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!isBusy) inputRef.current?.focus();
  }, [isBusy]);

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isBusy) return;
    onSend(trimmed);
    setText('');
  }

  return (
    <footer className="px-4 pt-2.5 pb-3.5 bg-white border-t border-[#ece7e0] space-y-2">
      <div className="flex items-center justify-between text-[11px] text-[#9ca3af] px-1">
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={isStreaming}
            onChange={e => onStreamingChange(e.target.checked)}
            className="rounded border-[#d1d5db] text-emerald-600 focus:ring-emerald-500 accent-emerald-600"
          />
          <span>Modo Streaming (SSE)</span>
        </label>
        <span className="font-mono text-[10px] text-[#b0a99b] truncate ml-auto">
          Sesión: {threadId}
        </span>
      </div>

      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <input
          ref={inputRef}
          value={text}
          onChange={e => setText(e.target.value)}
          type="text"
          placeholder="Escribe tu mensaje o pregunta aquí..."
          className="input-chat"
          disabled={isBusy}
          autoComplete="off"
          aria-label="Mensaje"
        />
        <button
          type="submit"
          className="btn-send"
          disabled={isBusy || !text.trim()}
        >
          <span>Enviar</span>
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
          </svg>
        </button>
      </form>
    </footer>
  );
}