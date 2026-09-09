const EMOJIS = {
  search_catalog: '🔍',
  filter_products: '🔍',
  get_product_details: '📦',
  add_to_cart: '🛒',
  view_cart: '🛒',
  remove_from_cart: '🗑️',
  place_order: '🛍️',
  get_order_status: '📦',
  search_knowledge: '📚',
};

function getToolEmoji(name) {
  return EMOJIS[name] || '🛠️';
}

function BotContent({ message }) {
  if (message.items) {
    return (
      <div>
        <div>{message.content.replace('html:', '')}</div>
        <ul className="list-disc ml-5 mt-1.5 space-y-0.5 text-[#4b5563]">
          {message.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
        <br />
        ¿Qué estás buscando hoy?
      </div>
    );
  }

  if (message.content.startsWith('html:')) {
    return (
      <div
        dangerouslySetInnerHTML={{ __html: message.content.slice(5) }}
      />
    );
  }

  return <span>{message.content || '…'}</span>;
}

export default function Message({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bubble-user whitespace-pre-wrap shadow-glow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-start gap-1.5 animate-fade-up">
      <div className="bubble-bot shadow-card whitespace-pre-wrap">
        {message.tools && message.tools.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {message.tools.map((tool, i) => (
              <span key={i} className="tool-badge">
                <span aria-hidden="true">{getToolEmoji(tool.name)}</span>
                <span>
                  {tool.name}
                  {tool.status === 'running' ? '…' : ' ✓'}
                </span>
              </span>
            ))}
          </div>
        )}
        <BotContent message={message} />
      </div>
    </div>
  );
}