import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Login from '../pages/Login'

describe('Login', () => {
  beforeEach(() => {
    delete global.window.location
    global.window.location = { href: '' }
  })

  it('renders Twitch login button', () => {
    render(<Login />)
    expect(screen.getByText(/twitch/i)).toBeInTheDocument()
  })

  it('renders Discord login button', () => {
    render(<Login />)
    expect(screen.getByText(/discord/i)).toBeInTheDocument()
  })

  it('Twitch button redirects to /api/auth/twitch', () => {
    render(<Login />)
    const btn = screen.getByText(/twitch/i)
    fireEvent.click(btn)
    expect(window.location.href).toBe('/api/auth/twitch')
  })

  it('Discord button redirects to /api/auth/discord', () => {
    render(<Login />)
    const btn = screen.getByText(/discord/i)
    fireEvent.click(btn)
    expect(window.location.href).toBe('/api/auth/discord')
  })
})
