import { useState, useCallback, useRef } from 'react';
import { sendMessage, streamMessage, deleteHistory } from '../lib/api';

function generateThreadId() {
  return 'session-' + Math.random().toString(36).substring(2, 9);
}

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'bot',
  content: `html:<strong>Tienda Online</strong> — Asistente de Compras. Puedo ayudarte con:`,
  items: [
    'Buscar productos por nombre o categoría',
    'Ver detalles de un producto por su ID',
    'Añadir productos al carrito',
    'Ver y gestionar tu carrito',
    'Realizar un pedido',
    'Consultar estado de pedidos',
    'Consultar políticas de envío, devoluciones, pagos y más',
  ],
};

export function useChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [isStreaming, setIsStreaming] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [threadId, setThreadId] = useState(() => {
    const saved = localStorage.getItem('chat_thread_id');
    if (saved) return saved;
    const id = generateThreadId();
    localStorage.setItem('chat_thread_id', id);
    return id;
  });

  const abortRef = useRef(null);

  const addMessage = useCallback((role, content, extra = {}) => {
    const msg = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      role,
      content,
      timestamp: Date.now(),
      ...extra,
    };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, []);

  const updateMessage = useCallback((id, updates) => {
    setMessages(prev =>
      prev.map(m => (m.id === id ? { ...m, ...updates } : m))
    );
  }, []);

  const sendMessageToChat = useCallback(async (text) => {
    addMessage('user', text);
    setIsTyping(true);

    const botId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    setMessages(prev => [
      ...prev,
      { id: botId, role: 'bot', content: '', tools: [], timestamp: Date.now() },
    ]);

    if (isStreaming) {
      let gotToken = false;
      try {
        await streamMessage(text, threadId, (eventType, data) => {
          if (eventType === 'thread' && data.thread_id) {
            setThreadId(data.thread_id);
            localStorage.setItem('chat_thread_id', data.thread_id);
          } else if (eventType === 'token' && data.token) {
            gotToken = true;
            setMessages(prev =>
              prev.map(m =>
                m.id === botId
                  ? { ...m, content: m.content + data.token }
                  : m
              )
            );
          } else if (eventType === 'tool_start' && data.tool) {
            setMessages(prev =>
              prev.map(m =>
                m.id === botId
                  ? { ...m, tools: [...(m.tools || []), { name: data.tool, status: 'running' }] }
                  : m
              )
            );
          } else if (eventType === 'tool_end') {
            setMessages(prev =>
              prev.map(m => {
                if (m.id !== botId) return m;
                const tools = [...(m.tools || [])];
                for (let i = tools.length - 1; i >= 0; i--) {
                  if (tools[i].status === 'running') {
                    tools[i] = { ...tools[i], status: 'done' };
                    break;
                  }
                }
                return { ...m, tools };
              })
            );
          } else if (eventType === 'error' && data.error) {
            setMessages(prev =>
              prev.map(m =>
                m.id === botId
                  ? { ...m, content: 'Error: ' + data.error }
                  : m
              )
            );
          }
        });

        if (!gotToken) {
          const res = await sendMessage(text, threadId);
          setMessages(prev =>
            prev.map(m =>
              m.id === botId ? { ...m, content: res.response } : m
            )
          );
        }
      } catch (err) {
        setMessages(prev =>
          prev.map(m =>
            m.id === botId
              ? { ...m, content: 'Error de conexión: ' + err.message }
              : m
          )
        );
      }
    } else {
      try {
        const res = await sendMessage(text, threadId);
        setMessages(prev =>
          prev.map(m =>
            m.id === botId ? { ...m, content: res.response } : m
          )
        );
      } catch (err) {
        setMessages(prev =>
          prev.map(m =>
            m.id === botId
              ? { ...m, content: 'Error de red: ' + err.message }
              : m
          )
        );
      }
    }

    setIsTyping(false);
  }, [threadId, isStreaming, addMessage]);

  const resetConversation = useCallback(async () => {
    try {
      await deleteHistory(threadId);
    } catch {}
    const newId = generateThreadId();
    setThreadId(newId);
    localStorage.setItem('chat_thread_id', newId);
    setMessages([WELCOME_MESSAGE]);
  }, [threadId]);

  return {
    messages,
    isStreaming,
    isTyping,
    threadId,
    setIsStreaming,
    sendMessage: sendMessageToChat,
    resetConversation,
  };
}
