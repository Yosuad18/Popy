const BASE = '';

export async function checkHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function sendMessage(message, threadId, systemPrompt = null) {
  const body = { message, thread_id: threadId };
  if (systemPrompt) body.system_prompt = systemPrompt;

  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Error en la respuesta');
  }

  return res.json();
}

export async function streamMessage(message, threadId, onEvent) {
  const body = { message, thread_id: threadId };

  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Error en la respuesta');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith('event:')) {
        var eventType = trimmed.slice(6).trim();
      } else if (trimmed.startsWith('data:') && eventType) {
        const raw = trimmed.slice(5).trim();
        try {
          const data = JSON.parse(raw);
          onEvent(eventType, data);
        } catch {}
        eventType = null;
      }
    }
  }
}

export async function deleteHistory(threadId) {
  const res = await fetch(`${BASE}/chat/history/${threadId}`, {
    method: 'DELETE',
  });
  return res.json();
}
