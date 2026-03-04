import React from 'react'
import { api } from '../api/client'

export default function Login() {
  function loginWith(platform) {
    window.location.href = `/api/auth/${platform}`
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
