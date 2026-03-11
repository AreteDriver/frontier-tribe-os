import { useEffect, useState } from 'react';
import { ConnectButton, useCurrentWallet } from '@mysten/dapp-kit';
import api from '../api';

interface Balance {
  coin_type: string;
  total_balance: string;
  coin_object_count: number;
}

interface WalletBalances {
  address: string;
  balances: Balance[];
}

interface MemberBalance {
  member_id: string;
  character_name: string | null;
  role: string;
  address: string;
  balances: Balance[];
}

interface TreasurySummary {
  tribe_name: string;
  treasury_address: string | null;
  treasury_balances: Balance[];
  member_count: number;
  total_transactions: number;
  members_with_balances: MemberBalance[];
}

interface Transaction {
  id: string;
  tx_digest: string;
  from_address: string;
  to_address: string;
  amount: string;
  coin_type: string;
  memo: string | null;
  status: string;
  created_at: string;
}

function formatSui(mist: string): string {
  const n = BigInt(mist);
  const whole = n / BigInt(1_000_000_000);
  const frac = n % BigInt(1_000_000_000);
  if (frac === BigInt(0)) return whole.toString();
  return `${whole}.${frac.toString().padStart(9, '0').replace(/0+$/, '')}`;
}

function truncateAddress(addr: string): string {
  if (addr.length <= 12) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

function formatBalance(b: Balance): string {
  return b.coin_type.includes('::sui::SUI') ? formatSui(b.total_balance) : b.total_balance;
}

function coinLabel(coinType: string): string {
  return coinType.includes('::sui::SUI') ? 'SUI' : truncateAddress(coinType);
}

export default function Treasury() {
  const tribeId = localStorage.getItem('tribeId');
  const { currentWallet } = useCurrentWallet();
  const [summary, setSummary] = useState<TreasurySummary | null>(null);
  const [myBalances, setMyBalances] = useState<WalletBalances | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!tribeId) return;
    loadData();
  }, [tribeId]);

  const loadData = async () => {
    if (!tribeId) return;
    setLoading(true);
    setError('');
    try {
      const [summaryRes, myRes, txRes] = await Promise.all([
        api.get(`/ledger/tribes/${tribeId}/summary`).catch(() => null),
        api.get('/ledger/members/me/balances').catch(() => null),
        api.get(`/ledger/tribes/${tribeId}/transactions`).catch(() => null),
      ]);
      if (summaryRes) setSummary(summaryRes.data);
      if (myRes) setMyBalances(myRes.data);
      if (txRes) setTransactions(txRes.data);
    } catch {
      setError('Failed to load ledger data');
    } finally {
      setLoading(false);
    }
  };

  if (!tribeId) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <h2 className="text-2xl font-bold">Ledger — Token Treasury</h2>
        <p className="text-[var(--color-text-dim)]">Join or create a tribe first.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Ledger — Token Treasury</h2>
        <ConnectButton />
      </div>

      {error && <p className="text-[var(--color-danger)] text-sm">{error}</p>}

      {currentWallet && (
        <p className="text-xs text-[var(--color-text-dim)]">
          Connected: {currentWallet.name}
        </p>
      )}

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-[var(--color-primary)]">{summary.member_count}</div>
            <div className="text-xs text-[var(--color-text-dim)]">Members</div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-[var(--color-primary)]">{summary.total_transactions}</div>
            <div className="text-xs text-[var(--color-text-dim)]">Transactions</div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-[var(--color-primary)]">
              {summary.treasury_balances.find((b) => b.coin_type.includes('::sui::SUI'))
                ? formatSui(summary.treasury_balances.find((b) => b.coin_type.includes('::sui::SUI'))!.total_balance)
                : '0'}
            </div>
            <div className="text-xs text-[var(--color-text-dim)]">Treasury SUI</div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-[var(--color-primary)]">{summary.members_with_balances.length}</div>
            <div className="text-xs text-[var(--color-text-dim)]">Wallets Tracked</div>
          </div>
        </div>
      )}

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Treasury Balance */}
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text-dim)] mb-3">Tribe Treasury</h3>
          {summary?.treasury_address ? (
            <>
              <p className="text-xs text-[var(--color-text-dim)] mb-2">
                {truncateAddress(summary.treasury_address)}
              </p>
              {summary.treasury_balances.length === 0 ? (
                <p className="text-[var(--color-text-dim)] text-sm">No balances</p>
              ) : (
                summary.treasury_balances.map((b, i) => (
                  <div key={i} className="flex justify-between items-baseline mb-1">
                    <span className="text-xs text-[var(--color-text-dim)]">{coinLabel(b.coin_type)}</span>
                    <span className="text-lg font-bold text-[var(--color-primary)]">{formatBalance(b)}</span>
                  </div>
                ))
              )}
            </>
          ) : loading ? (
            <p className="text-sm text-[var(--color-text-dim)]">Loading...</p>
          ) : (
            <p className="text-sm text-[var(--color-text-dim)]">No treasury configured</p>
          )}
        </div>

        {/* My Balance */}
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text-dim)] mb-3">My Wallet</h3>
          {myBalances ? (
            <>
              <p className="text-xs text-[var(--color-text-dim)] mb-2">
                {truncateAddress(myBalances.address)}
              </p>
              {myBalances.balances.length === 0 ? (
                <p className="text-[var(--color-text-dim)] text-sm">No balances</p>
              ) : (
                myBalances.balances.map((b, i) => (
                  <div key={i} className="flex justify-between items-baseline mb-1">
                    <span className="text-xs text-[var(--color-text-dim)]">{coinLabel(b.coin_type)}</span>
                    <span className="text-lg font-bold text-[var(--color-primary)]">{formatBalance(b)}</span>
                  </div>
                ))
              )}
            </>
          ) : loading ? (
            <p className="text-sm text-[var(--color-text-dim)]">Loading...</p>
          ) : (
            <p className="text-sm text-[var(--color-text-dim)]">—</p>
          )}
        </div>
      </div>

      {/* Member Balances */}
      {summary && summary.members_with_balances.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text-dim)] mb-4">Member Wallets</h3>
          <div className="space-y-2">
            {summary.members_with_balances.map((m) => (
              <div key={m.member_id} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                <div>
                  <span className="font-medium text-sm">{m.character_name || 'Unknown'}</span>
                  <span className="text-xs text-[var(--color-text-dim)] ml-2">{m.role}</span>
                </div>
                <div className="flex gap-3">
                  {m.balances.map((b, i) => (
                    <span key={i} className="text-sm text-[var(--color-primary)]">
                      {formatBalance(b)} {coinLabel(b.coin_type)}
                    </span>
                  ))}
                  {m.balances.length === 0 && (
                    <span className="text-xs text-[var(--color-text-dim)]">No balance</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transaction History */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
        <h3 className="text-sm font-semibold text-[var(--color-text-dim)] mb-4">Transaction History</h3>
        {transactions.length === 0 ? (
          <p className="text-sm text-[var(--color-text-dim)]">No transactions recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--color-text-dim)] border-b border-[var(--color-border)]">
                  <th className="pb-2">Date</th>
                  <th className="pb-2">From</th>
                  <th className="pb-2">To</th>
                  <th className="pb-2">Amount</th>
                  <th className="pb-2">Memo</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id} className="border-b border-[var(--color-border)]/30">
                    <td className="py-2 text-[var(--color-text-dim)]">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-2 font-mono text-xs">{truncateAddress(tx.from_address)}</td>
                    <td className="py-2 font-mono text-xs">{truncateAddress(tx.to_address)}</td>
                    <td className="py-2 text-[var(--color-primary)]">
                      {tx.coin_type.includes('::sui::SUI') ? formatSui(tx.amount) : tx.amount}
                    </td>
                    <td className="py-2 text-[var(--color-text-dim)]">{tx.memo || '—'}</td>
                    <td className="py-2">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        tx.status === 'confirmed'
                          ? 'bg-green-900/30 text-green-400'
                          : tx.status === 'pending'
                            ? 'bg-yellow-900/30 text-yellow-400'
                            : 'bg-red-900/30 text-red-400'
                      }`}>
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
