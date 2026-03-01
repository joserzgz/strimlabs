import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Stats() {
  const [stats, setStats] = useState(null)
  const [channels, setChannels] = useState([])
  const [selectedChannel, setSelectedChannel] = useState('')

  useEffect(() => {
    api.get('/channels/me').then(setChannels).catch(() => {})
  }, [])

  useEffect(() => { load() }, [selectedChannel])

  async function load() {
    let url = '/stats'
    if (selectedChannel) url += `?channel_id=${selectedChannel}`
    const data = await api.get(url)
    setStats(data)
  }

  return (
    <>
      <h1 className="page-title">Stats</h1>

      <div className="form-group" style={{ maxWidth: 300 }}>
        <select className="input" value={selectedChannel} onChange={e => setSelectedChannel(e.target.value)}>
          <option value="">Todos los canales</option>
          {channels.map(ch => (
            <option key={ch.id} value={ch.id}>[{ch.platform}] {ch.channel_name || ch.discord_guild_id}</option>
          ))}
        </select>
      </div>

      {stats && (
        <>
          <div className="card-grid mb-24">
            <div className="card stat-card">
              <div className="stat-value">{stats.total_actions}</div>
              <div className="stat-label">Total acciones</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{stats.messages_this_month}</div>
              <div className="stat-label">Mensajes este mes</div>
            </div>
          </div>

          {Object.keys(stats.breakdown || {}).length > 0 && (
            <div className="card mb-24">
              <h3 style={{ marginBottom: 16, fontSize: 14, color: 'var(--muted)' }}>Desglose por acción</h3>
              <div className="flex gap-16">
                {Object.entries(stats.breakdown).map(([action, count]) => (
                  <div key={action} style={{ textAlign: 'center' }}>
                    <div className="stat-value" style={{ fontSize: 24 }}>{count}</div>
                    <div className="stat-label">{action}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stats.top_offenders?.length > 0 && (
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
      )}
    </>
  )
}
