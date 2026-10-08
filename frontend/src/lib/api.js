async function parseResponse(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Error de API (${response.status})`);
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch('/health');
  return parseResponse(response);
}

export async function sendMessage(message, threadId) {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  return parseResponse(response);
}

export async function streamMessage(message, threadId, onEvent) {
  const response = await fetch('/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Error de API (${response.status})`);
  }
  if (!response.body) {
    throw new Error('El navegador no puede leer la respuesta SSE.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  function dispatchEvents() {
    const events = buffer.split(/\r?\n\r?\n/);
    buffer = events.pop() || '';

    for (const event of events) {
      let eventType = 'message';
      const data = [];

      for (const line of event.split(/\r?\n/)) {
        if (line.startsWith('event:')) eventType = line.slice(6).trim();
        if (line.startsWith('data:')) data.push(line.slice(5).trim());
      }

      if (data.length) onEvent(eventType, JSON.parse(data.join('\n')));
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      dispatchEvents();
      if (done) break;
    }
  } finally {
    reader.releaseLock();
  }
}
