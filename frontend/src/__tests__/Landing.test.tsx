import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import Landing from '../pages/Landing';

vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

function renderLanding() {
  return render(
    <MemoryRouter>
      <Landing />
    </MemoryRouter>,
  );
}

describe('Landing', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders title', () => {
    renderLanding();
    expect(screen.getByText('FRONTIER TRIBE OS')).toBeInTheDocument();
  });

  it('has Enter Dashboard button', () => {
    renderLanding();
    expect(screen.getByText('Enter Dashboard')).toBeInTheDocument();
  });

  it('shows feature modules', () => {
    renderLanding();
    expect(screen.getByText('Census')).toBeInTheDocument();
    expect(screen.getByText('Forge')).toBeInTheDocument();
    expect(screen.getByText('Ledger')).toBeInTheDocument();
  });

  it('calls dev-login on Enter Dashboard click', async () => {
    const api = await import('../api');
    const mockPost = vi.fn().mockResolvedValue({
      data: {
        access_token: 'test-token',
        character_name: 'Commander',
        wallet_address: '0x123',
      },
    });
    (api.default.post as ReturnType<typeof vi.fn>).mockImplementation(mockPost);

    const user = userEvent.setup();
    renderLanding();

    await user.click(screen.getByText('Enter Dashboard'));
    expect(mockPost).toHaveBeenCalledWith('/auth/dev-login?name=Commander');
  });
});
