import { useEffect, useState } from 'react';
import { useChat } from './hooks/useChat';
import { checkHealth } from './lib/api';
import Header from './components/Header';
import QuickPrompts from './components/QuickPrompts';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';

export default function App() {
  const {
    messages,
    isStreaming,
    isTyping,
    threadId,
    setIsStreaming,
    sendMessage,
    resetConversation,
  } = useChat();

  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  function handleReset() {
    if (window.confirm('¿Deseas iniciar una nueva conversación y reiniciar el historial?')) {
      resetConversation();
    }
  }

  function handleQuickPrompt(prompt) {
    sendMessage(prompt);
  }

  return (
    <div className="w-full max-w-3xl bg-white rounded-2xl shadow-card flex flex-col h-[94vh] overflow-hidden border border-[#ece7e0]">
      <Header health={health} onReset={handleReset} />

      <QuickPrompts onSelect={handleQuickPrompt} disabled={isTyping} />

      <ChatWindow messages={messages} isTyping={isTyping} />

      <InputBar
        isStreaming={isStreaming}
        isBusy={isTyping}
        threadId={threadId}
        onStreamingChange={setIsStreaming}
        onSend={sendMessage}
      />
    </div>
  );
}