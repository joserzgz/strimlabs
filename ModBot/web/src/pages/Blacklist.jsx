import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Plus, Trash2 } from 'lucide-react'

export default function Blacklist() {
  const [channels, setChannels] = useState([])
  const [selectedChannel, setSelectedChannel] = useState(null)
  const [entries, setEntries] = useState([])
  const [newPattern, setNewPattern] = useState('')

  useEffect(() => {
    api.get('/channels/me').then(chs => {
      setChannels(chs)
      if (chs.length > 0) setSelectedChannel(chs[0].id)
    })
  }, [])

  useEffect(() => {
    if (selectedChannel) loadEntries()
  }, [selectedChannel])

  async function loadEntries() {
    const data = await api.get(`/blacklist?channel_id=${selectedChannel}`)
    setEntries(data)
  }

  async function addEntry(e) {
    e.preventDefault()
    if (!newPattern.trim() || !selectedChannel) return
    await api.post('/blacklist', { channel_id: selectedChannel, pattern: newPattern.trim() })
    setNewPattern('')
    loadEntries()
  }

  async function removeEntry(id) {
    await api.delete(`/blacklist/${id}`)
    loadEntries()
  }

  return (
    <>
      <h1 className="page-title">Blacklist</h1>

      <div className="form-group">
        <label className="form-label">Canal</label>
        <select className="input" value={selectedChannel || ''} onChange={e => setSelectedChannel(Number(e.target.value))}>
          {channels.map(ch => (
            <option key={ch.id} value={ch.id}>
              [{ch.platform}] {ch.channel_name || ch.discord_guild_id}
            </option>
          ))}
        </select>
      </div>

      <form onSubmit={addEntry} className="flex gap-8 mb-24">
        <input className="input" value={newPattern} onChange={e => setNewPattern(e.target.value)} placeholder="Regex o palabra clave..." style={{ flex: 1 }} />
        <button className="btn btn-primary btn-sm" type="submit"><Plus size={16} /> Agregar</button>
      </form>

      {entries.length === 0 ? (
        <div className="empty"><p>Sin entradas en la blacklist</p></div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Patrón</th><th>Agregado por</th><th>Fecha</th><th></th></tr></thead>
              <tbody>
                {entries.map(e => (
                  <tr key={e.id}>
                    <td><code>{e.pattern}</code></td>
                    <td className="text-sm text-muted">{e.added_by}</td>
                    <td className="text-sm text-muted">{e.created_at ? new Date(e.created_at).toLocaleDateString() : '-'}</td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => removeEntry(e.id)} style={{ padding: '4px 8px' }}>
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
