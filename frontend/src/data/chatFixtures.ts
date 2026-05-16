import type { Conversation } from '../types';

export const conversations: Conversation[] = [
  {
    id: 'Dummy',
    title: 'Dummy',
    initials: 'D',
    lastMessage: 'Sincronização iniciada. Conclusão prevista...',
    lastActivity: '10:48',
    status: 'online',
    messages: [
      {
        id: 'msg-1',
        conversationId: 'Dummy',
        authorId: 'Dummy',
        authorName: 'Dummy',
        authorInitials: 'D',
        content:
          'Oi, boa tarde.',
        sentAt: '10:42',
        direction: 'incoming',
      },
    ],
  },
];
