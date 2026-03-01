import React from 'react'
import { api } from '../api/client'

export default function Login() {
  async function loginWith(platform) {
    try {
      const data = await api.get(`/auth/${platform}`)
      window.location.href = data.url
    } catch (err) {
      console.error('Login error:', err)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1><span>ModBot</span></h1>
        <p>Bot de moderación multi-plataforma para tu comunidad</p>
        <div className="login-buttons">
          <button className="btn btn-discord" onClick={() => loginWith('discord')}>
            Entrar con Discord
          </button>
          <button className="btn btn-twitch" onClick={() => loginWith('twitch')}>
            Entrar con Twitch
          </button>
        </div>
      </div>
    </div>
  )
}
