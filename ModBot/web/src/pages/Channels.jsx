import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Plus, Trash2 } from 'lucide-react'

export default function Channels() {
  const [channels, setChannels] = useState([])
  const [filter, setFilter] = useState('all')
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ platform: 'twitch', channel_name: '', discord_guild_id: '' })

  useEffect(() => { load() }, [])

  async function load() {
    const data = await api.get('/channels/me')
    setChannels(data)
  }

  const filtered = filter === 'all' ? channels : channels.filter(c => c.platform === filter)

  async function addChannel(e) {
    e.preventDefault()
    try {
      const body = { platform: form.platform }
      if (form.platform === 'twitch') body.channel_name = form.channel_name
      else body.discord_guild_id = form.discord_guild_id
      await api.post('/channels/me', body)
      setShowAdd(false)
      setForm({ platform: 'twitch', channel_name: '', discord_guild_id: '' })
      load()
    } catch (err) {
      alert(err.message)
    }
  }

  async function deleteChannel(id) {
    if (!confirm('¿Eliminar este canal?')) return
    await api.delete(`/channels/me/${id}`)
    load()
  }

  async function toggleActive(ch) {
    await api.patch(`/channels/me/${ch.id}`, { is_active: !ch.is_active })
    load()
  }

  async function updateChannel(id, field, value) {
    await api.patch(`/channels/me/${id}`, { [field]: value })
    load()
  }

  return (
    <>
      <div className="flex items-center justify-between mb-24">
        <h1 className="page-title" style={{ marginBottom: 0 }}>Channels</h1>
        <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(!showAdd)}>
          <Plus size={16} /> Agregar
        </button>
      </div>

      <div className="filter-tabs">
        {['all', 'twitch', 'discord'].map(f => (
          <button key={f} className={`filter-tab ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
            {f === 'all' ? 'Todos' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {showAdd && (
        <div className="card mb-24">
          <form onSubmit={addChannel}>
            <div className="form-group">
              <label className="form-label">Plataforma</label>
              <select className="input" value={form.platform} onChange={e => setForm({ ...form, platform: e.target.value })}>
                <option value="twitch">Twitch</option>
                <option value="discord">Discord</option>
              </select>
            </div>
            {form.platform === 'twitch' ? (
              <div className="form-group">
                <label className="form-label">Nombre del canal</label>
                <input className="input" value={form.channel_name} onChange={e => setForm({ ...form, channel_name: e.target.value })} placeholder="mi_canal" required />
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label">Guild ID de Discord</label>
                <input className="input" value={form.discord_guild_id} onChange={e => setForm({ ...form, discord_guild_id: e.target.value })} placeholder="123456789..." required />
              </div>
            )}
            <button className="btn btn-primary btn-sm" type="submit">Crear canal</button>
          </form>
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="empty"><p>No hay canales configurados</p></div>
      ) : (
        <div className="card-grid">
          {filtered.map(ch => (
            <div className="card" key={ch.id}>
              <div className="flex items-center justify-between mb-16">
                <span className={`badge badge-${ch.platform}`}>{ch.platform}</span>
                <button className="btn btn-danger btn-sm" onClick={() => deleteChannel(ch.id)} style={{ padding: '4px 8px' }}>
                  <Trash2 size={14} />
                </button>
              </div>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>{ch.channel_name || ch.discord_guild_id}</div>

              <div className="form-group" style={{ marginBottom: 12 }}>
                <label className="form-label text-sm">Acción de moderación</label>
                <select className="input" value={ch.mod_action} onChange={e => updateChannel(ch.id, 'mod_action', e.target.value)}>
                  <option value="timeout">Timeout</option>
                  <option value="ban">Ban</option>
                  <option value="delete">Eliminar mensaje</option>
                </select>
              </div>

              {ch.mod_action === 'timeout' && (
                <div className="form-group" style={{ marginBottom: 12 }}>
                  <label className="form-label text-sm">Duración timeout (segundos)</label>
                  <input className="input" type="number" min="1" max="604800" value={ch.timeout_seconds}
                    onChange={e => updateChannel(ch.id, 'timeout_seconds', parseInt(e.target.value) || 60)} />
                </div>
              )}

              <div className="form-group" style={{ marginBottom: 12 }}>
                <label className="form-label text-sm">Umbral de toxicidad IA ({ch.toxicity_threshold})</label>
                <input type="range" min="0.1" max="1" step="0.05" value={ch.toxicity_threshold}
                  onChange={e => updateChannel(ch.id, 'toxicity_threshold', parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--cyan)' }} />
                <div className="flex justify-between text-sm text-muted" style={{ fontSize: 11 }}>
                  <span>Sensible (0.1)</span><span>Permisivo (1.0)</span>
                </div>
              </div>

              <button className={`btn btn-sm ${ch.is_active ? 'btn-outline' : 'btn-primary'}`} onClick={() => toggleActive(ch)}>
                {ch.is_active ? 'Desactivar' : 'Activar'}
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
