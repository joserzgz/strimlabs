import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function History({ user }) {
  const [logs, setLogs] = useState([])
  const [channels, setChannels] = useState([])
  const [selectedChannel, setSelectedChannel] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    api.get('/channels/me').then(setChannels).catch(() => {})
  }, [])

  useEffect(() => { load() }, [selectedChannel, page])

  async function load() {
    if (user.plan !== 'pro') return
    let url = `/history?page=${page}`
    if (selectedChannel) url += `&channel_id=${selectedChannel}`
    try {
      const data = await api.get(url)
      setLogs(data)
    } catch {
      setLogs([])
    }
  }

  if (user.plan !== 'pro') {
    return (
      <>
        <h1 className="page-title">History</h1>
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <p style={{ color: 'var(--muted)', marginBottom: 16 }}>El historial de moderación requiere plan Pro</p>
          <span className="badge badge-pro">PRO</span>
        </div>
      </>
    )
  }

  function channelPlatform(channelId) {
    const ch = channels.find(c => c.id === channelId)
    return ch?.platform || 'unknown'
  }

  return (
    <>
      <h1 className="page-title">History</h1>

      <div className="flex gap-8 mb-24">
        <select className="input" value={selectedChannel} onChange={e => { setSelectedChannel(e.target.value); setPage(1) }} style={{ maxWidth: 300 }}>
          <option value="">Todos los canales</option>
          {channels.map(ch => (
            <option key={ch.id} value={ch.id}>[{ch.platform}] {ch.channel_name || ch.discord_guild_id}</option>
          ))}
        </select>
      </div>

      {logs.length === 0 ? (
        <div className="empty"><p>Sin acciones registradas</p></div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Plataforma</th><th>Usuario</th><th>Mensaje</th><th>Acción</th><th>Razón</th><th>Score</th><th>Fecha</th></tr>
              </thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.id}>
                    <td><span className={`badge badge-${channelPlatform(log.channel_id)}`}>{channelPlatform(log.channel_id)}</span></td>
                    <td>{log.username}</td>
                    <td className="truncate">{log.message}</td>
                    <td>{log.action}</td>
                    <td className="text-sm text-muted">{log.reason}</td>
                    <td>{log.score ? log.score.toFixed(2) : '-'}</td>
                    <td className="text-sm text-muted">{log.created_at ? new Date(log.created_at).toLocaleString() : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex justify-between items-center" style={{ marginTop: 16 }}>
            <button className="btn btn-outline btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Anterior</button>
            <span className="text-sm text-muted">Página {page}</span>
            <button className="btn btn-outline btn-sm" disabled={logs.length < 50} onClick={() => setPage(p => p + 1)}>Siguiente</button>
          </div>
        </div>
      )}
    </>
  )
}
