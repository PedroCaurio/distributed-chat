import { FormEvent, useState } from 'react';
import { LogIn, User } from 'lucide-react';

type IdentityScreenProps = {
  onLogin: (username: string) => Promise<void>;
  notice?: string;
  onDismissNotice?: () => void;
};

export default function IdentityScreen({ onLogin, notice, onDismissNotice }: IdentityScreenProps) {
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedUsername = username.trim();

    if (!trimmedUsername) {
      setError('Informe um nome de usuário para entrar.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await onLogin(trimmedUsername);
    } catch (loginError) {
      const message =
        loginError instanceof Error
          ? loginError.message
          : 'Não foi possível conectar ao chat. Verifique se o servidor está online.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="identity-page">
      <div className="identity-shell" aria-labelledby="app-title">
        <div className="brand-block">
          <h1 id="app-title">Zenith Chat</h1>
          <p>Comunicação simples para sistemas distribuídos.</p>
        </div>

        <section className="identity-card" aria-label="Identificação do usuário">
          {notice ? (
            <p className="field-error" role="status">
              {notice}
              {onDismissNotice ? (
                <button type="button" className="notice-dismiss" onClick={onDismissNotice}>
                  Ok
                </button>
              ) : null}
            </p>
          ) : null}
          <form className="identity-form" onSubmit={handleSubmit} noValidate>
            <label htmlFor="username">Usuário</label>
            <div className="input-with-icon">
              <User size={18} aria-hidden="true" />
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                placeholder="Digite seu usuário"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'username-error' : undefined}
                disabled={loading}
              />
            </div>
            {error ? (
              <p className="field-error" id="username-error" role="alert">
                {error}
              </p>
            ) : null}

            <button className="primary-action" type="submit" disabled={loading}>
              <span>{loading ? 'Conectando...' : 'Entrar'}</span>
              <LogIn size={18} aria-hidden="true" />
            </button>
          </form>
          <p className="identity-hint">
            Use o link público do chat (Fly.io). Nenhuma instalação no computador é necessária.
          </p>
        </section>
      </div>
    </main>
  );
}