export type SessionStatus = 'anonymous' | 'authenticated';

export type UserProfile = {
  id: string;
  username: string;
  initials: string;
  status: 'online' | 'offline';
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
};

export type Conversation = {
  id: string;
  title: string;
  initials: string;
  lastMessage: string;
  lastActivity: string;
  status?: 'online' | 'offline';
};

export type AppSession =
  | {
      status: 'anonymous';
    }
  | {
      status: 'authenticated';
      user: UserProfile;
    };
