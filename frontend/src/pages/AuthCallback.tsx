import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code) {
      setError('No authorization code received');
      return;
    }

    (async () => {
      try {
        const { data } = await api.get(`/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state || '')}`);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('characterName', data.character_name);
        if (data.wallet_address) {
          localStorage.setItem('walletAddress', data.wallet_address);
        }
        navigate('/dashboard');
      } catch (err: any) {
        setError(err.response?.data?.detail || 'SSO authentication failed');
      }
    })();
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full mx-4 text-center space-y-4">
          <h2 className="text-xl font-bold text-[var(--color-danger)]">Authentication Failed</h2>
          <p className="text-[var(--color-text-dim)]">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 rounded bg-[var(--color-primary)] text-black font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-[var(--color-text-dim)]">Authenticating...</p>
      </div>
    </div>
  );
}
