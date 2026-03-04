import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Link2 } from 'lucide-react'

export default function Settings({ user, setUser }) {
  const [settings, setSettings] = useState(null)
  const [billing, setBilling] = useState(null)

  useEffect(() => {
    api.get('/settings').then(setSettings).catch(() => {})
    api.get('/billing/status').then(setBilling).catch(() => {})
  }, [])

  function linkAccount(platform) {
    window.location.href = `/api/auth/${platform}`
  }

  async function addDiscordServer() {
    const data = await api.get('/auth/discord/bot')
    window.location.href = data.url
  }

  async function upgradePlan(provider) {
    const data = await api.post(`/billing/${provider}/checkout`)
    window.location.href = data.url
  }

  async function manageSubscription() {
    const data = await api.get('/billing/stripe/portal')
    window.location.href = data.url
  }

  const linkedPlatforms = (settings?.linked_accounts || []).map(a => a.platform)
  const hasTwitch = linkedPlatforms.includes('twitch')
  const hasDiscord = linkedPlatforms.includes('discord')

  return (
    <>
      <h1 className="page-title">Settings</h1>

      {/* Plan */}
      <div className="card mb-24">
        <h3 style={{ marginBottom: 16, fontSize: 14, color: 'var(--muted)' }}>Plan</h3>
        <div className="flex items-center gap-16 mb-16">
          <span className={`badge ${user.plan === 'pro' ? 'badge-pro' : 'badge-free'}`}>
            {user.plan.toUpperCase()}
          </span>
          {billing && <span className="text-sm text-muted">Estado: {billing.subscription_status}</span>}
        </div>
        {user.plan === 'free' ? (
          <div className="flex gap-8">
            <button className="btn btn-primary btn-sm" onClick={() => upgradePlan('stripe')}>
              Upgrade Pro — $9.99 USD
            </button>
            <button className="btn btn-outline btn-sm" onClick={() => upgradePlan('mp')}>
              Upgrade Pro — $199 MXN
            </button>
          </div>
        ) : (
          billing?.payment_provider === 'stripe' && (
            <button className="btn btn-outline btn-sm" onClick={manageSubscription}>
              Gestionar suscripción
            </button>
          )
        )}
      </div>

      {/* Linked Accounts */}
      <div className="card mb-24">
        <h3 style={{ marginBottom: 16, fontSize: 14, color: 'var(--muted)' }}>Cuentas vinculadas</h3>
        {settings?.linked_accounts?.map(acc => (
          <div key={acc.platform} className="flex items-center gap-12 mb-16">
            <span className={`badge badge-${acc.platform}`}>{acc.platform}</span>
            <span>{acc.display_name || acc.username}</span>
            {acc.avatar_url && <img src={acc.avatar_url} alt="" style={{ width: 24, height: 24, borderRadius: '50%' }} />}
          </div>
        ))}
        <div className="flex gap-8" style={{ marginTop: 16 }}>
          {!hasTwitch && (
            <button className="btn btn-twitch btn-sm" onClick={() => linkAccount('twitch')}>
              <Link2 size={14} /> Vincular Twitch
            </button>
          )}
          {!hasDiscord && (
            <button className="btn btn-discord btn-sm" onClick={() => linkAccount('discord')}>
              <Link2 size={14} /> Vincular Discord
            </button>
          )}
        </div>
      </div>

      {/* Discord Bot */}
      {hasDiscord && (
        <div className="card mb-24">
          <h3 style={{ marginBottom: 16, fontSize: 14, color: 'var(--muted)' }}>Servidor Discord</h3>
          <p className="text-sm text-muted mb-16">Agrega el bot de moderación a tu servidor de Discord</p>
          <button className="btn btn-discord btn-sm" onClick={addDiscordServer}>
            Agregar bot a servidor
          </button>
        </div>
      )}
    </>
  )
}
