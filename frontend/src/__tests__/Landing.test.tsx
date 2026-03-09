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

  it('renders title "Frontier Tribe OS"', () => {
    renderLanding();
    expect(screen.getByText('Frontier Tribe OS')).toBeInTheDocument();
  });

  it('has dev login input and button', () => {
    renderLanding();
    expect(screen.getByPlaceholderText('Character name')).toBeInTheDocument();
    expect(screen.getByText('Dev Login')).toBeInTheDocument();
  });

  it('has SSO button', () => {
    renderLanding();
    expect(screen.getByText('Login with EVE Frontier')).toBeInTheDocument();
  });

  it('shows error when submitting empty name', async () => {
    const user = userEvent.setup();
    renderLanding();

    await user.click(screen.getByText('Dev Login'));
    expect(screen.getByText('Enter a character name')).toBeInTheDocument();
  });
});
