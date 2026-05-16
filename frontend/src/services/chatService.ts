import type { Attachment, ChatMessage, Conversation, UserProfile } from '../types';

function todoBackendError(action: string): Error {
  return new Error(`TODO backend: ${action} ainda não foi implementado.`);
}

export async function joinChat(username: string): Promise<UserProfile> {
  void username;
  throw todoBackendError('joinChat');
}

export async function sendMessage(
  conversationId: string,
  content: string,
): Promise<ChatMessage> {
  void conversationId;
  void content;
  throw todoBackendError('sendMessage');
}

export async function createConversation(): Promise<Conversation> {
  throw todoBackendError('createConversation');
}

export async function shutdownServerNode(): Promise<void> {
  throw todoBackendError('shutdownServerNode');
}

export async function downloadAttachment(attachmentId: Attachment['id']): Promise<void> {
  void attachmentId;
  throw todoBackendError('downloadAttachment');
}
