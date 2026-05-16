export type SessionStatus = 'anonymous' | 'preview';

export type UserProfile = {
  id: string;
  username: string;
  initials: string;
  status: 'online' | 'offline';
};

export type Attachment = {
  id: string;
  fileName: string;
  kind: 'image';
  description: string;
};

export type ChatMessage = {
  id: string;
  conversationId: string;
  authorId: string;
  authorName: string;
  authorInitials: string;
  content: string;
  sentAt: string;
  direction: 'incoming' | 'outgoing';
  attachment?: Attachment;
};

export type Conversation = {
  id: string;
  title: string;
  initials: string;
  lastMessage: string;
  lastActivity: string;
  status?: 'online' | 'offline';
  messages: ChatMessage[];
};

export type AppSession =
  | {
      status: 'anonymous';
    }
  | {
      status: 'preview';
      user: UserProfile;
    };
