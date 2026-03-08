import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function Landing() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDevLogin = async () => {
    if (!name.trim()) {
      setError('Enter a character name');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post(`/auth/dev-login?name=${encodeURIComponent(name)}`);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('characterName', data.character_name);
      localStorage.setItem('characterId', data.character_id);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSSOLogin = async () => {
    try {
      const { data } = await api.get('/auth/login');
      window.location.href = data.authorize_url;
    } catch {
      setError('SSO not available yet — use Dev Login');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-[var(--color-primary)] mb-2">
            Frontier Tribe OS
          </h1>
          <p className="text-[var(--color-text-dim)]">
            Operations platform for EVE Frontier Tribes
          </p>
        </div>

        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-4">
          <button
            onClick={handleSSOLogin}
            className="w-full py-3 rounded-lg bg-[var(--color-primary)] text-black font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer"
          >
            Login with EVE Frontier
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[var(--color-border)]" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-[var(--color-surface)] text-[var(--color-text-dim)]">
                or dev mode
              </span>
            </div>
          </div>

          <div className="space-y-3">
            <input
              type="text"
              placeholder="Character name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleDevLogin()}
              className="w-full px-4 py-2 rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
            />
            <button
              onClick={handleDevLogin}
              disabled={loading}
              className="w-full py-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-colors cursor-pointer disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Dev Login'}
            </button>
          </div>

          {error && (
            <p className="text-sm text-[var(--color-danger)] text-center">{error}</p>
          )}
        </div>
      </div>
    </div>
  );
}
