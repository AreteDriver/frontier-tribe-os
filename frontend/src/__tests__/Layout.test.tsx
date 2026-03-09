import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import Layout from '../components/Layout';

function renderLayout() {
  return render(
    <MemoryRouter>
      <Layout />
    </MemoryRouter>,
  );
}

describe('Layout', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders nav links (Dashboard, Census, Forge, Ledger)', () => {
    renderLayout();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Census')).toBeInTheDocument();
    expect(screen.getByText('Forge')).toBeInTheDocument();
    expect(screen.getByText('Ledger')).toBeInTheDocument();
  });

  it('shows character name from localStorage', () => {
    localStorage.setItem('characterName', 'TestPilot');
    renderLayout();
    expect(screen.getByText('TestPilot')).toBeInTheDocument();
  });

  it('shows default "Pilot" when no characterName in localStorage', () => {
    renderLayout();
    expect(screen.getByText('Pilot')).toBeInTheDocument();
  });

  it('logout clears localStorage', async () => {
    const user = userEvent.setup();
    localStorage.setItem('token', 'fake-token');
    localStorage.setItem('characterName', 'TestPilot');
    localStorage.setItem('walletAddress', '0x123');
    localStorage.setItem('tribeId', '1');

    renderLayout();
    await user.click(screen.getByText('Logout'));

    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('characterName')).toBeNull();
    expect(localStorage.getItem('walletAddress')).toBeNull();
    expect(localStorage.getItem('tribeId')).toBeNull();
  });
});
