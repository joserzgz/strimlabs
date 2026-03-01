import React, { useState, useEffect } from 'react'
import { setToken, clearToken, api } from './api/client'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Channels from './pages/Channels'
import Blacklist from './pages/Blacklist'
import History from './pages/History'
import Stats from './pages/Stats'
import Settings from './pages/Settings'
import { LayoutDashboard, Radio, ShieldBan, Clock, BarChart3, Settings as SettingsIcon, LogOut } from 'lucide-react'

const PAGES = {
  dashboard: { label: 'Dashboard', icon: LayoutDashboard, component: Dashboard },
  channels:  { label: 'Channels',  icon: Radio,           component: Channels },
  blacklist: { label: 'Blacklist',  icon: ShieldBan,       component: Blacklist },
  history:   { label: 'History',    icon: Clock,           component: History },
  stats:     { label: 'Stats',      icon: BarChart3,       component: Stats },
  settings:  { label: 'Settings',   icon: SettingsIcon,    component: Settings },
}

export default function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('dashboard')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for token in URL (OAuth callback)
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      setToken(urlToken)
      window.history.replaceState({}, '', window.location.pathname)
    }

    // Check path
    const path = window.location.pathname.replace('/', '')
    if (path && PAGES[path]) setPage(path)

    // Fetch user
    const token = localStorage.getItem('token')
    if (token) {
      api.get('/auth/me')
        .then(u => { setUser(u); setLoading(false) })
        .catch(() => { clearToken(); setLoading(false) })
    } else {
      setLoading(false)
    }
  }, [])

  function navigate(p) {
    setPage(p)
    window.history.pushState({}, '', `/${p}`)
  }

  function logout() {
    clearToken()
    setUser(null)
  }

  if (loading) return null
  if (!user) return <Login />

  const PageComponent = PAGES[page]?.component || Dashboard

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-logo"><span>ModBot</span></div>
        {Object.entries(PAGES).map(([key, { label, icon: Icon }]) => (
          <a
            key={key}
            href={`/${key}`}
            className={page === key ? 'active' : ''}
            onClick={e => { e.preventDefault(); navigate(key) }}
          >
            <Icon size={18} />
            {label}
          </a>
        ))}
        <div className="sidebar-bottom">
          <a href="#" onClick={e => { e.preventDefault(); logout() }}>
            <LogOut size={18} /> Logout
          </a>
        </div>
      </nav>
      <main className="main">
        <PageComponent user={user} setUser={setUser} navigate={navigate} />
      </main>
    </div>
  )
}
