"""FastAPI application entrypoint for LangGraph Chatbot."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from app.config import settings
from app.routers import health_router, chat_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready Chatbot API built with FastAPI, LangChain, and LangGraph. "
        "Supports multi-turn memory checkpointer, tool-calling agent, streaming SSE, and fallback demo mode."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(chat_router)


@app.get("/", response_class=JSONResponse, tags=["Root"])
async def root():
    """Root endpoint providing quick links and service status."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": "/docs",
        "health_url": "/health",
        "chat_url": "/chat",
        "chat_stream_url": "/chat/stream",
        "tools_url": "/chat/tools",
        "graph_diagram_url": "/chat/graph?format=html",
        "demo_ui_url": "/demo",
    }


@app.get("/demo", response_class=HTMLResponse, tags=["UI"])
async def demo_ui():
    """Interactive Web UI with SSE streaming, quick actions, and tool execution badges."""
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tienda Online - Asistente de Compras</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .message-user { background: linear-gradient(135deg, #059669, #10b981); color: white; border-radius: 18px 18px 4px 18px; }
    .message-bot { background-color: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 18px 18px 18px 4px; }
  </style>
</head>
<body class="bg-slate-100 min-h-screen flex flex-col items-center justify-center p-3 font-sans">
  <div class="w-full max-w-3xl bg-white rounded-2xl shadow-2xl flex flex-col h-[94vh] overflow-hidden border border-slate-200">
    
    <!-- Header -->
    <header class="bg-emerald-600 text-white p-4 flex items-center justify-between shadow-md">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl font-bold">
          🛍️
        </div>
        <div>
          <h1 class="font-bold text-base leading-tight">Tienda Online - Asistente de Compras</h1>
          <p class="text-xs text-emerald-200 flex items-center gap-1.5" id="status-container">
            <span id="status-indicator" class="inline-block w-2 h-2 rounded-full bg-yellow-400"></span>
            <span id="status-text">Conectando...</span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <a href="/chat/graph?format=html" target="_blank" class="text-xs bg-emerald-500/80 hover:bg-emerald-500 px-2.5 py-1.5 rounded-lg text-white font-medium transition">
          📊 Grafo
        </a>
        <a href="/docs" target="_blank" class="text-xs bg-emerald-500/80 hover:bg-emerald-500 px-2.5 py-1.5 rounded-lg text-white font-medium transition">
          📖 Docs
        </a>
        <button id="reset-btn" title="Nueva Conversación" class="text-xs bg-red-500/80 hover:bg-red-500 px-2.5 py-1.5 rounded-lg text-white font-medium transition">
          🔄 Reiniciar
        </button>
      </div>
    </header>

    <!-- Quick Prompts bar -->
    <div class="bg-slate-50 px-4 py-2 border-b border-slate-200 flex items-center gap-2 overflow-x-auto text-xs text-slate-600">
      <span class="font-semibold text-slate-400 shrink-0">Prueba rápida:</span>
      <button class="quick-chip bg-white hover:bg-emerald-50 hover:text-emerald-600 border border-slate-200 px-2.5 py-1 rounded-full shrink-0 transition" data-prompt="Muéstrame productos de electrónica">
        🎧 Electrónica
      </button>
      <button class="quick-chip bg-white hover:bg-emerald-50 hover:text-emerald-600 border border-slate-200 px-2.5 py-1 rounded-full shrink-0 transition" data-prompt="¿Cuáles son sus políticas de devolución?">
        🔄 Política devolución
      </button>
      <button class="quick-chip bg-white hover:bg-emerald-50 hover:text-emerald-600 border border-slate-200 px-2.5 py-1 rounded-full shrink-0 transition" data-prompt="Añade el producto 1 al carrito">
        🛒 Añadir al carrito
      </button>
      <button class="quick-chip bg-white hover:bg-emerald-50 hover:text-emerald-600 border border-slate-200 px-2.5 py-1 rounded-full shrink-0 transition" data-prompt="Ver mi carrito de compras">
        🛒 Ver carrito
      </button>
    </div>

    <!-- Chat Messages Box -->
    <main id="chat-box" class="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/60">
      <div class="flex justify-start">
        <div class="message-bot p-3.5 max-w-[85%] text-sm shadow-sm whitespace-pre-wrap">
          👋 ¡Bienvenido a <strong>Tienda Online</strong>! Soy tu asistente de compras.<br/><br/>
          Puedo ayudarte con:
          <ul class="list-disc ml-5 mt-1 text-slate-600">
            <li>Buscar productos por nombre o categoría (<code>search_catalog</code>)</li>
            <li>Ver detalles de un producto por su ID (<code>get_product_details</code>)</li>
            <li>Añadir productos al carrito (<code>add_to_cart</code>)</li>
            <li>Ver y gestionar tu carrito (<code>view_cart</code>, <code>remove_from_cart</code>)</li>
            <li>Realizar un pedido (<code>place_order</code>)</li>
            <li>Consultar estado de pedidos (<code>get_order_status</code>)</li>
            <li>Consultar políticas de envío, devoluciones, pagos y más (<code>search_knowledge</code>)</li>
          </ul>
          <br/>¿Qué estás buscando hoy?
        </div>
      </div>
    </main>

    <!-- Controls & Form -->
    <footer class="p-3.5 bg-white border-t border-slate-200 space-y-2">
      <div class="flex items-center justify-between text-xs text-slate-500 px-1">
        <label class="flex items-center gap-1.5 cursor-pointer select-none">
          <input type="checkbox" id="stream-toggle" checked class="rounded text-indigo-600 focus:ring-indigo-500" />
          <span>Modo Streaming (SSE)</span>
        </label>
        <span id="thread-display" class="font-mono text-[11px] text-slate-400"></span>
      </div>
      <form id="chat-form" class="flex gap-2">
        <input 
          id="user-input" 
          type="text" 
          placeholder="Escribe tu mensaje o pregunta aquí..." 
          class="flex-1 border border-slate-300 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition" 
          required 
          autocomplete="off"
        />
        <button 
          id="send-btn"
          type="submit" 
          class="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-6 py-2.5 rounded-full transition shadow-sm hover:shadow disabled:opacity-50 flex items-center gap-1.5"
        >
          <span>Enviar</span>
        </button>
      </form>
    </footer>
  </div>

  <script>
    let threadId = localStorage.getItem('chat_thread_id') || 'session-' + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('chat_thread_id', threadId);
    document.getElementById('thread-display').textContent = 'Sesión: ' + threadId;

    const chatBox = document.getElementById('chat-box');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.getElementById('status-indicator');
    const streamToggle = document.getElementById('stream-toggle');
    const resetBtn = document.getElementById('reset-btn');

    async function checkHealth() {
      try {
        const res = await fetch('/health');
        const data = await res.json();
        if (data.openai_configured) {
          statusIndicator.className = "inline-block w-2 h-2 rounded-full bg-emerald-400";
          statusText.textContent = "OpenAI Conectado";
        } else {
          statusIndicator.className = "inline-block w-2 h-2 rounded-full bg-yellow-400";
          statusText.textContent = "Modo Demo Activo";
        }
      } catch (e) {
        statusIndicator.className = "inline-block w-2 h-2 rounded-full bg-red-400";
        statusText.textContent = "Desconectado";
      }
    }
    checkHealth();

    resetBtn.addEventListener('click', async () => {
      if (confirm('¿Deseas iniciar una nueva conversación y reiniciar el historial?')) {
        try {
          await fetch('/chat/history/' + threadId, { method: 'DELETE' });
        } catch (e) {}
        threadId = 'session-' + Math.random().toString(36).substring(2, 9);
        localStorage.setItem('chat_thread_id', threadId);
        document.getElementById('thread-display').textContent = 'Sesión: ' + threadId;
        chatBox.innerHTML = '';
        appendMessage('bot', 'Conversación reiniciada. ¿En qué te puedo ayudar hoy?');
      }
    });

    document.querySelectorAll('.quick-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        input.value = chip.dataset.prompt;
        form.dispatchEvent(new Event('submit'));
      });
    });

    function appendMessage(role, text) {
      const wrapper = document.createElement('div');
      wrapper.className = role === 'user' ? 'flex justify-end' : 'flex justify-start';
      const bubble = document.createElement('div');
      bubble.className = (role === 'user' ? 'message-user' : 'message-bot') + ' p-3.5 max-w-[85%] text-sm shadow-sm whitespace-pre-wrap';
      bubble.textContent = text;
      wrapper.appendChild(bubble);
      chatBox.appendChild(wrapper);
      chatBox.scrollTop = chatBox.scrollHeight;
      return bubble;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      appendMessage('user', message);
      input.value = '';
      sendBtn.disabled = true;

      const botBubble = appendMessage('bot', 'Pensando...');

      if (streamToggle.checked) {
        // SSE Streaming Mode
        try {
          const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, thread_id: threadId })
          });

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let fullText = '';
          let firstToken = true;

          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split('\\n');

            for (let i = 0; i < lines.length; i++) {
              const line = lines[i].trim();
              if (line.startsWith('data:')) {
                try {
                  const data = JSON.parse(line.substring(5).trim());
                  if (data.token) {
                    if (firstToken) {
                      botBubble.textContent = '';
                      firstToken = false;
                    }
                    fullText += data.token;
                    botBubble.textContent = fullText;
                  } else if (data.tool) {
                    botBubble.textContent = '🛠️ Ejecutando herramienta: ' + data.tool + '...';
                  } else if (data.error) {
                    botBubble.textContent = '❌ Error: ' + data.error;
                  }
                } catch (parseErr) {}
              }
            }
            chatBox.scrollTop = chatBox.scrollHeight;
          }

          if (firstToken) {
            // If no stream tokens were yielded (e.g. demo mode fallback)
            // fetch normal invoke
            const fallbackRes = await fetch('/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ message: message, thread_id: threadId })
            });
            const fbData = await fallbackRes.json();
            botBubble.textContent = fbData.response;
          }
        } catch (err) {
          botBubble.textContent = '❌ Error de conexión: ' + err.message;
        } finally {
          sendBtn.disabled = false;
          chatBox.scrollTop = chatBox.scrollHeight;
        }

      } else {
        // Standard REST POST Mode
        try {
          const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, thread_id: threadId })
          });
          const data = await response.json();
          if (response.ok) {
            botBubble.textContent = data.response;
          } else {
            botBubble.textContent = '❌ Error: ' + (data.detail || 'Fallo en la respuesta');
          }
        } catch (err) {
          botBubble.textContent = '❌ Error de red: ' + err.message;
        } finally {
          sendBtn.disabled = false;
          chatBox.scrollTop = chatBox.scrollHeight;
        }
      }
    });
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
