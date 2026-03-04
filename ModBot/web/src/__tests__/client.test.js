import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setToken, clearToken, apiFetch, api } from '../api/client'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const storage = {}
global.localStorage = {
  getItem: vi.fn((key) => storage[key] || null),
  setItem: vi.fn((key, val) => { storage[key] = val }),
  removeItem: vi.fn((key) => { delete storage[key] }),
}

describe('Token management', () => {
  beforeEach(() => {
    Object.keys(storage).forEach(k => delete storage[k])
    vi.clearAllMocks()
  })

  it('setToken stores token in localStorage', () => {
    setToken('mytoken')
    expect(localStorage.setItem).toHaveBeenCalledWith('token', 'mytoken')
  })

  it('clearToken removes token from localStorage', () => {
    clearToken()
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
  })
})

describe('apiFetch', () => {
  beforeEach(() => {
    Object.keys(storage).forEach(k => delete storage[k])
    vi.clearAllMocks()
    // Reset location mock
    delete global.window.location
    global.window.location = { href: '' }
  })

  it('includes Authorization header when token exists', async () => {
    storage.token = 'test-jwt'
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'ok' }),
    })

    await apiFetch('/test')

    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.headers.Authorization).toBe('Bearer test-jwt')
  })

  it('does not include Authorization when no token', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })

    await apiFetch('/test')

    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.headers.Authorization).toBeUndefined()
  })

  it('clears token and redirects on 401', async () => {
    storage.token = 'expired'
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({}),
    })

    await expect(apiFetch('/test')).rejects.toThrow('Unauthorized')
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
    expect(window.location.href).toBe('/login')
  })

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: () => Promise.resolve({ detail: 'Forbidden' }),
    })

    await expect(apiFetch('/test')).rejects.toThrow('Forbidden')
  })
})

describe('api methods', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('api.get calls fetch with GET', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    })

    await api.get('/channels/me')

    const [url] = mockFetch.mock.calls[0]
    expect(url).toBe('/api/channels/me')
  })

  it('api.post sends JSON body', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    })

    await api.post('/channels/me', { platform: 'twitch', channel_name: 'test' })

    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ platform: 'twitch', channel_name: 'test' })
  })

  it('api.patch sends PATCH method', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    })

    await api.patch('/channels/me/1', { ai_enabled: false })

    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.method).toBe('PATCH')
  })

  it('api.delete sends DELETE method', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    })

    await api.delete('/channels/me/1')

    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.method).toBe('DELETE')
  })
})
