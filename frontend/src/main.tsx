import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { initDemoLogsFromServer } from './lib/demoLog';
import { clearStoredSessionId } from './lib/sessionStorage';
import './styles.css';

// Sessão em sessionStorage de deploy/login antigo não deve reativar SSE fantasma.
clearStoredSessionId();

const root = createRoot(document.getElementById('root')!);

void initDemoLogsFromServer().finally(() => {
  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
