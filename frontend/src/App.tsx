import { useState } from 'react';
import ChatScreen from './components/ChatScreen';
import IdentityScreen from './components/IdentityScreen';
import type { AppSession } from './types';

function getInitials(username: string): string {
  return username
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('');
}

export default function App() {
  const [session, setSession] = useState<AppSession>({ status: 'anonymous' });

  function handlePreviewLogin(username: string) {
    const trimmedUsername = username.trim();

    setSession({
      status: 'preview',
      user: {
        id: 'current-user',
        username: trimmedUsername,
        initials: getInitials(trimmedUsername) || 'V',
        status: 'online',
      },
    });
  }

  if (session.status === 'preview') {
    return <ChatScreen currentUser={session.user} />;
  }

  return <IdentityScreen onLogin={handlePreviewLogin} />;
}
