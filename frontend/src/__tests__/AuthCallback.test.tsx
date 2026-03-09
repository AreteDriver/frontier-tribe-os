import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import AuthCallback from '../pages/AuthCallback';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

describe('AuthCallback', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('shows "Authenticating..." spinner when code param is present', () => {
    render(
      <MemoryRouter initialEntries={['/auth/callback?code=test123']}>
        <AuthCallback />
      </MemoryRouter>,
    );
    expect(screen.getByText('Authenticating...')).toBeInTheDocument();
  });

  it('shows error when no code param is provided', async () => {
    render(
      <MemoryRouter initialEntries={['/auth/callback']}>
        <AuthCallback />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText('No authorization code received')).toBeInTheDocument();
    });
  });
});
