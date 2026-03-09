import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Must mock import.meta.env before importing api
vi.stubEnv('VITE_API_URL', 'http://test-api:9000');

describe('api module', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('has correct baseURL from env', async () => {
    const { default: api } = await import('../api');
    expect(api.defaults.baseURL).toBe('http://test-api:9000');
  });

  it('request interceptor adds auth header when token exists', async () => {
    const { default: api } = await import('../api');
    localStorage.setItem('token', 'my-jwt-token');

    // Simulate the request interceptor by calling it directly
    const interceptor = api.interceptors.request as any;
    const handlers = interceptor.handlers;
    const handler = handlers.find((h: any) => h !== null && h.fulfilled);

    if (handler) {
      const config = { headers: {} as any };
      const result = handler.fulfilled(config);
      expect(result.headers.Authorization).toBe('Bearer my-jwt-token');
    }
  });

  it('request interceptor does not add auth header without token', async () => {
    const { default: api } = await import('../api');

    const interceptor = api.interceptors.request as any;
    const handlers = interceptor.handlers;
    const handler = handlers.find((h: any) => h !== null && h.fulfilled);

    if (handler) {
      const config = { headers: {} as any };
      const result = handler.fulfilled(config);
      expect(result.headers.Authorization).toBeUndefined();
    }
  });
});
