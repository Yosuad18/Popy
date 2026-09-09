export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bubble-bot !py-3.5">
        <div className="flex items-center gap-1.5">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}