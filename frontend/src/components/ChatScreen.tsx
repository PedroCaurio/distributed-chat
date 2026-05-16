import { FormEvent, ReactNode, useMemo, useState } from 'react';
import {
  Download,
  Image,
  Plus,
  Power,
  Search,
  Send,
  Settings,
  Smile,
} from 'lucide-react';
import { conversations } from '../data/chatFixtures';
import {
  createConversation,
  downloadAttachment,
  sendMessage,
  shutdownServerNode,
} from '../services/chatService';
import type { Attachment, ChatMessage, Conversation, UserProfile } from '../types';

type ChatScreenProps = {
  currentUser: UserProfile;
};

function getActionError(error: unknown): string {
  if (error instanceof Error) {
    return `${error.message} Funcionalidade aguardando backend.`;
  }

  return 'Funcionalidade aguardando backend.';
}

function MessageBubble({
  message,
  onDownloadAttachment,
}: {
  message: ChatMessage;
  onDownloadAttachment: (attachmentId: Attachment['id']) => Promise<void>;
}) {
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
        {message.attachment ? (
          <AttachmentPreview
            attachment={message.attachment}
            onDownloadAttachment={onDownloadAttachment}
          />
        ) : null}
      </div>
    </article>
  );
}

function AttachmentPreview({
  attachment,
  onDownloadAttachment,
}: {
  attachment: Attachment;
  onDownloadAttachment: (attachmentId: Attachment['id']) => Promise<void>;
}) {
  async function handleDownload() {
    await onDownloadAttachment(attachment.id);
  }

  return (
    <div className="attachment-card">
      <div className="attachment-preview" role="img" aria-label={attachment.description}>
        <div className="server-rack">
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="attachment-footer">
        <div className="attachment-name">
          <Image size={18} aria-hidden="true" />
          <strong>{attachment.fileName}</strong>
        </div>
        <AsyncActionButton
          className="ghost-action"
          onAction={handleDownload}
          label="Baixar anexo"
        >
          <Download size={15} aria-hidden="true" />
          <span>Baixar</span>
        </AsyncActionButton>
      </div>
    </div>
  );
}

type AsyncActionButtonProps = {
  children: ReactNode;
  className: string;
  label: string;
  onAction: () => Promise<unknown>;
};

function AsyncActionButton({
  children,
  className,
  label,
  onAction,
}: AsyncActionButtonProps) {
  const [busy, setBusy] = useState(false);

  async function handleClick() {
    setBusy(true);
    try {
      await onAction();
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      className={className}
      type="button"
      onClick={handleClick}
      disabled={busy}
      aria-label={label}
      title={label}
    >
      {children}
    </button>
  );
}

export default function ChatScreen({ currentUser }: ChatScreenProps) {
  const [selectedConversationId, setSelectedConversationId] = useState(conversations[0].id);
  const [query, setQuery] = useState('');
  const [messageDraft, setMessageDraft] = useState('');
  const [notice, setNotice] = useState('');

  const filteredConversations = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return conversations;
    }

    return conversations.filter((conversation) =>
      [conversation.title, conversation.lastMessage]
        .join(' ')
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query]);

  const selectedConversation =
    conversations.find((conversation) => conversation.id === selectedConversationId) ??
    conversations[0];
  const selectedStatus = selectedConversation.status === 'online' ? 'Online' : 'Offline';

  async function runPlaceholder(action: () => Promise<unknown>) {
    setNotice('');
    try {
      await action();
    } catch (error) {
      setNotice(getActionError(error));
    }
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = messageDraft.trim();

    if (!content) {
      return;
    }

    await runPlaceholder(() => sendMessage(selectedConversation.id, content));
  }

  function handleSelectConversation(conversation: Conversation) {
    setSelectedConversationId(conversation.id);
    setNotice('');
  }

  return (
    <main className="chat-page">
      <header className="top-bar">
        <div className="top-bar-identity">
          <span className="app-name">DS Chat</span>
        </div>

        <div className="top-bar-actions">
          <button
            className="danger-action"
            type="button"
            onClick={() => runPlaceholder(shutdownServerNode)}
          >
            <Power size={15} aria-hidden="true" />
            <span>Derrubar servidor</span>
          </button>
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
              placeholder="Buscar conversas..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <nav className="conversation-list">
            {filteredConversations.map((conversation) => (
              <button
                className={`conversation-item ${
                  conversation.id === selectedConversation.id ? 'conversation-item-active' : ''
                }`}
                key={conversation.id}
                type="button"
                onClick={() => handleSelectConversation(conversation)}
              >
                <span className="avatar">
                  {conversation.initials}
                  {conversation.status === 'online' ? <i aria-hidden="true" /> : null}
                </span>
                <span className="conversation-copy">
                  <span className="conversation-title">
                    <strong>{conversation.title}</strong>
                    <small>{conversation.lastActivity}</small>
                  </span>
                  <span className="conversation-last-message">{conversation.lastMessage}</span>
                </span>
              </button>
            ))}
          </nav>

          <button
            className="new-chat-action"
            type="button"
            onClick={() => runPlaceholder(createConversation)}
          >
            <Plus size={18} aria-hidden="true" />
            <span>Nova conversa</span>
          </button>
        </aside>

        <section className="chat-surface" aria-label={`Conversa com ${selectedConversation.title}`}>
          <div className="message-list">
            <div className="date-chip">Hoje</div>
            {selectedConversation.messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onDownloadAttachment={(attachmentId) =>
                  runPlaceholder(() => downloadAttachment(attachmentId))
                }
              />
            ))}
          </div>

          {notice ? (
            <div className="backend-notice" role="status">
              {notice}
            </div>
          ) : null}

          <form className="composer" onSubmit={handleSendMessage}>
            <textarea
              rows={1}
              placeholder={`Mensagem como ${currentUser.username}...`}
              value={messageDraft}
              onChange={(event) => setMessageDraft(event.target.value)}
            />
            <button className="icon-action" type="button" aria-label="Inserir emoji" title="Inserir emoji">
              <Smile size={20} aria-hidden="true" />
            </button>
            <button className="send-action" type="submit" aria-label="Enviar mensagem" title="Enviar mensagem">
              <Send size={20} aria-hidden="true" />
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
