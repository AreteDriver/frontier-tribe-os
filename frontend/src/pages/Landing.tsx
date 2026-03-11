import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const features = [
  {
    name: 'Census',
    desc: 'Identity & roster management. Role hierarchy, invite codes, join approval.',
  },
  {
    name: 'Forge',
    desc: 'Production planning with gap analysis. Blueprint picker, material tracking, Kanban jobs.',
  },
  {
    name: 'Ledger',
    desc: 'Non-custodial Sui treasury. Real wallet balances via JSON-RPC.',
  },
  {
    name: 'Watch',
    desc: 'C5 orbital zone monitoring. Signature Resolution System, feral AI tracking, blind spot detection.',
  },
  {
    name: 'Intel',
    desc: 'Kill feed, pilot profiles, corp intelligence, battle reports, LLM-powered FC briefings.',
  },
  {
    name: 'Alerts',
    desc: 'Discord webhook notifications. 6 alert types with per-entity cooldowns.',
  },
];

const stats = [
  '190+ Tests',
  '7 Modules',
  'Live on Fly.io + Vercel',
  'Cycle 5: Shroud of Fear',
];

export default function Landing() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (localStorage.getItem('token')) {
    navigate('/dashboard');
    return null;
  }

  const handleDevLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/dev-login?name=Commander');
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('characterName', data.character_name);
      localStorage.setItem('walletAddress', data.wallet_address);
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Login failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{ backgroundColor: '#0a0a0a' }}
      className="min-h-screen text-zinc-100"
    >
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-4 pt-20 pb-16 sm:pt-28 sm:pb-20 text-center">
        <h1
          className="text-4xl sm:text-6xl font-extrabold tracking-tight"
          style={{ color: '#f59e0b' }}
        >
          FRONTIER TRIBE OS
        </h1>
        <p className="mt-4 text-lg sm:text-xl text-zinc-300 max-w-xl">
          The operating system for EVE Frontier tribes
        </p>
        <p
          className="mt-2 text-sm sm:text-base font-mono tracking-widest"
          style={{ color: '#f59e0b' }}
        >
          Census &middot; Forge &middot; Ledger &middot; Watch &middot; Intel
          &middot; Alerts
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 items-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="px-8 py-3 rounded-lg font-semibold text-black text-lg transition-colors cursor-pointer"
            style={{ backgroundColor: '#f59e0b' }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.backgroundColor = '#d97706')
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.backgroundColor = '#f59e0b')
            }
          >
            Enter Dashboard
          </button>
          <button
            onClick={handleDevLogin}
            disabled={loading}
            className="px-6 py-2 rounded-lg text-sm border transition-colors cursor-pointer disabled:opacity-50"
            style={{ borderColor: '#3f3f46', color: '#a1a1aa' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#f59e0b';
              e.currentTarget.style.color = '#f5f5f4';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#3f3f46';
              e.currentTarget.style.color = '#a1a1aa';
            }}
          >
            {loading ? 'Logging in...' : 'Dev Login'}
          </button>
        </div>
        {error && (
          <p className="mt-3 text-sm" style={{ color: '#ef4444' }}>
            {error}
          </p>
        )}
      </section>

      {/* Feature grid */}
      <section className="max-w-5xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => (
            <div
              key={f.name}
              className="rounded-lg p-5"
              style={{
                backgroundColor: '#18181b',
                border: '1px solid #27272a',
              }}
            >
              <h3
                className="text-base font-bold tracking-wide mb-1"
                style={{ color: '#f59e0b' }}
              >
                {f.name}
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: '#a1a1aa' }}>
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats bar */}
      <section
        className="py-5"
        style={{ backgroundColor: '#18181b', borderTop: '1px solid #27272a', borderBottom: '1px solid #27272a' }}
      >
        <div className="max-w-5xl mx-auto px-4 flex flex-wrap justify-center gap-x-8 gap-y-2 text-sm font-mono tracking-wide">
          {stats.map((s, i) => (
            <span key={i}>
              <span style={{ color: '#f59e0b' }}>{s}</span>
              {i < stats.length - 1 && (
                <span className="ml-8 hidden sm:inline" style={{ color: '#3f3f46' }}>
                  |
                </span>
              )}
            </span>
          ))}
        </div>
      </section>

      {/* Tech stack strip */}
      <section className="py-6 text-center px-4">
        <p
          className="text-xs sm:text-sm font-mono tracking-wider"
          style={{ color: '#71717a' }}
        >
          FastAPI &middot; React 19 &middot; SQLAlchemy &middot; Sui JSON-RPC
          &middot; Claude Haiku &middot; Discord Webhooks
        </p>
      </section>

      {/* Footer */}
      <footer className="pb-10 pt-4 text-center px-4">
        <p className="text-sm" style={{ color: '#a1a1aa' }}>
          Built by{' '}
          <span className="font-semibold" style={{ color: '#f59e0b' }}>
            AreteDriver
          </span>{' '}
          for EVE Frontier x Sui Hackathon 2026
        </p>
        <a
          href="https://github.com/AreteDriver/frontier-tribe-os"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-2 text-xs underline"
          style={{ color: '#71717a' }}
        >
          github.com/AreteDriver/frontier-tribe-os
        </a>
      </footer>
    </div>
  );
}
