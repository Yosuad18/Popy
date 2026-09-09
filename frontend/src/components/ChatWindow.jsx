import { useEffect, useRef } from 'react';
import Message from './Message';
import TypingIndicator from './TypingIndicator';

export default function ChatWindow({ messages, isTyping }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <main className="flex-1 overflow-y-auto chat-scroll px-4 py-4 space-y-4 bg-[#fbfaf8]">
      {messages.map(message => (
        <Message key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </main>
  );
}