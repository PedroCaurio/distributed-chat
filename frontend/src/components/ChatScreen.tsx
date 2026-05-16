import { FormEvent, useMemo, useState } from 'react';
import { Search, Send, Settings, Smile } from 'lucide-react';
import { sendMessage } from '../services/chatService';
import type { ChatMessage, Conversation, UserProfile } from '../types';
import { GLOBAL_CONVERSATION_ID } from '../utils/chatMappers';

type ChatScreenProps = {
  currentUser: UserProfile;
  messages: ChatMessage[];
  conversationId: string;
};

function MessageBubble({ message }: { message: ChatMessage }) {
  const isOutgoing = message.direction === 'outgoing';

  return (
    <article className={`message-row ${isOutgoing ? 'message-row-outgoing' : ''}`}>
      <div className="avatar avatar-message" aria-hidden="true">
        {message.authorInitials}
      </div>
      <div className="message-stack">
        <div className="message-meta">
          <strong>{message.authorName}</strong>
          <span>{message.sentAt}</span>
        </div>
        <div className="message-bubble">
          <p>{message.content}</p>
        </div>
      </div>
    </article>
  );
}

export default function ChatScreen({ currentUser, messages, conversationId }: ChatScreenProps) {
  const [messageDraft, setMessageDraft] = useState('');
  const [notice, setNotice] = useState('');
  const [query, setQuery] = useState('');
  const [sending, setSending] = useState(false);

  const globalConversation: Conversation = useMemo(() => {
    const last = messages.at(-1);
    return {
      id: GLOBAL_CONVERSATION_ID,
      title: 'Sala global',
      initials: 'SG',
      lastMessage: last?.content ?? 'Nenhuma mensagem ainda.',
      lastActivity: last?.sentAt ?? '--:--',
      status: 'online',
    };
  }, [messages]);

  const filteredMessages = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const roomMessages = messages.filter((m) => m.conversationId === conversationId);
    if (!normalizedQuery) {
      return roomMessages;
    }
    return roomMessages.filter((message) =>
      [message.authorName, message.content].join(' ').toLowerCase().includes(normalizedQuery),
    );
  }, [conversationId, messages, query]);

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = messageDraft.trim();
    if (!content || sending) {
      return;
    }

    setNotice('');
    setSending(true);
    try {
      await sendMessage(content);
      setMessageDraft('');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha ao enviar mensagem.';
      setNotice(message);
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="chat-page">
      <header className="top-bar">
        <div className="top-bar-identity">
          <span className="app-name">DS Chat</span>
          <span className="user-pill">{currentUser.username}</span>
        </div>

        <div className="top-bar-actions">
          <button className="icon-action" type="button" aria-label="Configurações" title="Configurações">
            <Settings size={19} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="chat-layout">
        <aside className="conversation-panel" aria-label="Conversas">
          <div className="search-field">
            <Search size={18} aria-hidden="true" />
            <input
              type="search"
              placeholder="Buscar na sala..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <nav className="conversation-list">
            <button className="conversation-item conversation-item-active" type="button">
              <span className="avatar">
                {globalConversation.initials}
                <i aria-hidden="true" />
              </span>
              <span className="conversation-copy">
                <span className="conversation-title">
                  <strong>{globalConversation.title}</strong>
                  <small>{globalConversation.lastActivity}</small>
                </span>
                <span className="conversation-last-message">{globalConversation.lastMessage}</span>
              </span>
            </button>
          </nav>
        </aside>

        <section className="chat-surface" aria-label="Sala global do chat">
          <div className="message-list">
            <div className="date-chip">Ao vivo</div>
            {filteredMessages.length === 0 ? (
              <p className="empty-chat">Nenhuma mensagem ainda. Envie a primeira!</p>
            ) : (
              filteredMessages.map((message) => <MessageBubble key={message.id} message={message} />)
            )}
          </div>

          {notice ? (
            <div className="backend-notice" role="alert">
              {notice}
            </div>
          ) : null}

          <form className="composer" onSubmit={handleSendMessage}>
            <textarea
              rows={1}
              placeholder={`Mensagem como ${currentUser.username}...`}
              value={messageDraft}
              onChange={(event) => setMessageDraft(event.target.value)}
              disabled={sending}
            />
            <button className="icon-action" type="button" aria-label="Inserir emoji" title="Inserir emoji">
              <Smile size={20} aria-hidden="true" />
            </button>
            <button
              className="send-action"
              type="submit"
              aria-label="Enviar mensagem"
              title="Enviar mensagem"
              disabled={sending}
            >
              <Send size={20} aria-hidden="true" />
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
