import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Dashboard({ user }) {
  const [stats, setStats] = useState(null)
  const [channels, setChannels] = useState([])

  useEffect(() => {
    api.get('/stats').then(setStats).catch(() => {})
    api.get('/channels/me').then(setChannels).catch(() => {})
  }, [])

  const twitchCount = channels.filter(c => c.platform === 'twitch').length
  const discordCount = channels.filter(c => c.platform === 'discord').length

  return (
    <>
      <h1 className="page-title">Dashboard</h1>

      <div className="card-grid mb-24">
        <div className="card stat-card">
          <div className="stat-value">{channels.length}</div>
          <div className="stat-label">Canales activos</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{stats?.total_actions ?? 0}</div>
          <div className="stat-label">Acciones de moderación</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{user.messages_this_month ?? 0}</div>
          <div className="stat-label">Mensajes este mes</div>
        </div>
      </div>

      <div className="card-grid mb-24">
        <div className="card">
          <div className="flex items-center gap-8 mb-16">
            <span className="badge badge-twitch">Twitch</span>
            <span className="text-sm text-muted">{twitchCount} canal(es)</span>
          </div>
          <div className="flex items-center gap-8">
            <span className="badge badge-discord">Discord</span>
            <span className="text-sm text-muted">{discordCount} servidor(es)</span>
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-muted mb-16">Plan actual</div>
          <span className={`badge ${user.plan === 'pro' ? 'badge-pro' : 'badge-free'}`}>
            {user.plan.toUpperCase()}
          </span>
        </div>
      </div>

      {stats?.top_offenders?.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: 16, fontSize: 14, color: 'var(--muted)' }}>Top ofensores</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Usuario</th><th>Acciones</th></tr></thead>
              <tbody>
                {stats.top_offenders.map((o, i) => (
                  <tr key={i}><td>{o.username}</td><td>{o.count}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
