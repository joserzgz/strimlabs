import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Channels from '../pages/Channels'

// Mock the api module
vi.mock('../api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '../api/client'

const mockChannels = [
  {
    id: 1,
    platform: 'twitch',
    channel_name: 'test_streamer',
    discord_guild_id: null,
    is_active: true,
    mod_action: 'timeout',
    timeout_seconds: 600,
    toxicity_threshold: 0.8,
    ai_enabled: true,
    created_at: '2024-01-01T00:00:00',
  },
  {
    id: 2,
    platform: 'discord',
    channel_name: 'MyServer',
    discord_guild_id: '123456',
    is_active: false,
    mod_action: 'ban',
    timeout_seconds: 600,
    toxicity_threshold: 0.5,
    ai_enabled: false,
    created_at: '2024-01-02T00:00:00',
  },
]

describe('Channels', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue(mockChannels)
    api.patch.mockResolvedValue({})
    api.post.mockResolvedValue({})
    api.delete.mockResolvedValue({})
    global.confirm = vi.fn(() => true)
  })

  it('renders channels from API', async () => {
    render(<Channels />)
    await waitFor(() => {
      expect(screen.getByText('test_streamer')).toBeInTheDocument()
      expect(screen.getByText('MyServer')).toBeInTheDocument()
    })
  })

  it('filter tabs work', async () => {
    render(<Channels />)
    await waitFor(() => expect(screen.getByText('test_streamer')).toBeInTheDocument())

    // Click Discord filter
    fireEvent.click(screen.getByText('Discord'))
    expect(screen.queryByText('test_streamer')).not.toBeInTheDocument()
    expect(screen.getByText('MyServer')).toBeInTheDocument()

    // Click Twitch filter
    fireEvent.click(screen.getByText('Twitch'))
    expect(screen.getByText('test_streamer')).toBeInTheDocument()
    expect(screen.queryByText('MyServer')).not.toBeInTheDocument()

    // Click All
    fireEvent.click(screen.getByText('Todos'))
    expect(screen.getByText('test_streamer')).toBeInTheDocument()
    expect(screen.getByText('MyServer')).toBeInTheDocument()
  })

  it('shows ai_enabled checkbox for each channel', async () => {
    render(<Channels />)
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('ai toggle calls patch with ai_enabled', async () => {
    render(<Channels />)
    await waitFor(() => expect(screen.getByText('test_streamer')).toBeInTheDocument())

    const checkboxes = screen.getAllByRole('checkbox')
    // First checkbox should be for the first channel (ai_enabled=true)
    fireEvent.click(checkboxes[0])

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/channels/me/1', { ai_enabled: false })
    })
  })

  it('shows toxicity slider when ai_enabled is true', async () => {
    render(<Channels />)
    await waitFor(() => {
      // Channel 1 has ai_enabled=true, should show slider
      expect(screen.getByText(/Umbral de toxicidad/)).toBeInTheDocument()
    })
  })

  it('hides toxicity slider when ai_enabled is false', async () => {
    // All channels with ai_enabled=false
    api.get.mockResolvedValue([mockChannels[1]]) // Discord channel with ai_enabled=false
    render(<Channels />)
    await waitFor(() => {
      expect(screen.getByText('MyServer')).toBeInTheDocument()
    })
    expect(screen.queryByText(/Umbral de toxicidad/)).not.toBeInTheDocument()
  })

  it('shows timeout input when mod_action is timeout', async () => {
    render(<Channels />)
    await waitFor(() => {
      expect(screen.getByText(/Duración timeout/)).toBeInTheDocument()
    })
  })

  it('shows empty state when no channels', async () => {
    api.get.mockResolvedValue([])
    render(<Channels />)
    await waitFor(() => {
      expect(screen.getByText('No hay canales configurados')).toBeInTheDocument()
    })
  })

  it('add channel form toggles', async () => {
    render(<Channels />)
    await waitFor(() => expect(api.get).toHaveBeenCalled())

    const addBtn = screen.getByText('Agregar')
    fireEvent.click(addBtn)
    expect(screen.getByText('Plataforma')).toBeInTheDocument()
    expect(screen.getByText('Crear canal')).toBeInTheDocument()
  })
})
