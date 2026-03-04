import { useState, useEffect, useRef } from 'react'
import '@shared/theme.css'

/* ═══════════════════════════════════════════
   STRIMLABS LANDING PAGE
   Single-file JSX — CSS puro, sin librerías
   ═══════════════════════════════════════════ */

/* ─── Data ──────────────────────────────── */

const CHAT_MSGS = [
  { user: 'viewer_23', msg: 'Buen stream hoy!', safe: true },
  { user: 'gamer_pro', msg: 'A que hora es el torneo?', safe: true },
  { user: 'troll_101', msg: 'Eres un asco, deja de streamear', safe: false, reason: 'Toxicidad: 94%', action: 'Timeout 60s' },
  { user: 'fan_clips', msg: 'Me encanta tu contenido', safe: true },
  { user: 'spam_bot3', msg: 'Compra followers en spam.xyz', safe: false, reason: 'Blacklist match', action: 'Eliminado' },
  { user: 'gg_master', msg: 'GG buena partida', safe: true },
  { user: 'hater_99', msg: 'Nadie te ve, rindete ya', safe: false, reason: 'Toxicidad: 87%', action: 'Timeout 60s' },
  { user: 'chill_guy', msg: 'Que buen ModBot tienen aqui', safe: true },
]

const PRODUCTS = [
  { name: 'ModBot', desc: 'Moderacion inteligente para tu chat con IA y blacklist en tiempo real.', active: true, icon: 'shield' },
  { name: 'Alerts & Overlays', desc: 'Alertas personalizadas y overlays animados para tu stream.', active: false, icon: 'bell' },
  { name: 'Stream Analytics', desc: 'Estadisticas avanzadas y metricas de crecimiento de tu canal.', active: false, icon: 'chart' },
  { name: 'Chat Interact', desc: 'Mini-juegos y herramientas de interaccion para tu audiencia.', active: false, icon: 'gamepad' },
]

const STATS = [
  { value: 2400000, label: 'Mensajes moderados', suffix: '+', format: true },
  { value: 98, label: 'Precision', suffix: '%' },
  { value: 340, label: 'Streamers activos', suffix: '+' },
  { value: 0, label: 'Latencia blacklist', suffix: 'ms' },
]

const WHY_ITEMS = [
  { title: 'Construido para streamers', desc: 'No somos una herramienta generica adaptada. Cada feature esta diseñada para las necesidades del streaming en vivo.', icon: 'target' },
  { title: 'Crece contigo', desc: 'Desde tu primer stream hasta miles de viewers. Plan gratuito para empezar, Pro cuando lo necesites. Sin contratos.', icon: 'rocket' },
  { title: 'Mas herramientas en camino', desc: 'ModBot es solo el principio. Alerts, Analytics y Chat Interact estan en desarrollo. Una plataforma, todas tus herramientas.', icon: 'layers' },
]

/* ─── SVG Icons ─────────────────────────── */

const ICON_PATHS = {
  shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>,
  bell: <><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></>,
  chart: <><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></>,
  gamepad: <><line x1="6" y1="12" x2="10" y2="12"/><line x1="8" y1="10" x2="8" y2="14"/><line x1="15" y1="13" x2="15.01" y2="13"/><line x1="18" y1="11" x2="18.01" y2="11"/><rect x="2" y="6" width="20" height="12" rx="2"/></>,
  target: <><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></>,
  rocket: <><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></>,
  layers: <><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></>,
  check: <polyline points="20 6 9 17 4 12"/>,
  x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
  menu: <><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>,
  close: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
  mail: <><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,7 12,13 2,7"/></>,
  arrowRight: <><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>,
  twitch: null,
  discord: null,
}

function Icon({ name, size = 24 }) {
  if (name === 'twitch') {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" style={{ display: 'block' }}>
        <path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714z"/>
      </svg>
    )
  }
  if (name === 'discord') {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" style={{ display: 'block' }}>
        <path d="M20.317 4.37a19.79 19.79 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.865-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.74 19.74 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.11 13.11 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.078-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.3 12.3 0 01-1.873.892.076.076 0 00-.041.107c.36.698.772 1.363 1.225 1.993a.076.076 0 00.084.028 19.84 19.84 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.086-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.332-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.086-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.332-.946 2.418-2.157 2.418z"/>
      </svg>
    )
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block' }}>
      {ICON_PATHS[name]}
    </svg>
  )
}

/* ─── Chat Demo ─────────────────────────── */

function ChatDemo() {
  const [messages, setMessages] = useState([])
  const [moderated, setModerated] = useState(new Set())
  const chatRef = useRef(null)
  const indexRef = useRef(0)

  useEffect(() => {
    const addMessage = () => {
      const idx = indexRef.current % CHAT_MSGS.length
      const msg = { ...CHAT_MSGS[idx], id: Date.now() + Math.random() }
      indexRef.current++
      setMessages(prev => [...prev, msg].slice(-7))
      if (!msg.safe) {
        setTimeout(() => {
          setModerated(prev => new Set([...prev, msg.id]))
        }, 800)
      }
    }
    addMessage()
    const interval = setInterval(addMessage, 2200)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [messages])

  return (
    <div className="chat-demo">
      <div className="chat-header">
        <span className="chat-dot red"/><span className="chat-dot yellow"/><span className="chat-dot green"/>
        <span className="chat-title">Chat — tu_canal</span>
        <span className="chat-live">LIVE</span>
      </div>
      <div className="chat-body" ref={chatRef}>
        {messages.map(m => (
          <div key={m.id} className={`chat-msg ${moderated.has(m.id) ? 'chat-msg--mod' : ''}`}>
            <span className="chat-user" style={{ color: m.safe ? 'var(--cyan)' : 'var(--red)' }}>{m.user}:</span>
            <span className={`chat-text ${moderated.has(m.id) ? 'chat-text--strike' : ''}`}>{m.msg}</span>
            {moderated.has(m.id) && (
              <span className="chat-mod-badge">
                <Icon name="shield" size={11}/> {m.reason} — {m.action}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── CountUp Hook ──────────────────────── */

function useCountUp(target, duration = 2000, format = false) {
  const [count, setCount] = useState(0)
  const [started, setStarted] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !started) setStarted(true)
    }, { threshold: 0.3 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [started])

  useEffect(() => {
    if (!started) return
    if (target === 0) { setCount(0); return }
    const t0 = performance.now()
    const tick = (now) => {
      const p = Math.min((now - t0) / duration, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setCount(Math.floor(eased * target))
      if (p < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [started, target, duration])

  return { ref, display: format ? count.toLocaleString('en-US') : String(count) }
}

function StatCard({ value, label, suffix, format }) {
  const { ref, display } = useCountUp(value, 2000, format)
  return (
    <div className="stat-card" ref={ref}>
      <span className="stat-value">{display}{suffix}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

/* ─── Main Landing ──────────────────────── */

export default function Landing() {
  const [mobileNav, setMobileNav] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [waitlistVote, setWaitlistVote] = useState(() => localStorage.getItem('sl-vote') || '')
  const [waitlistEmail, setWaitlistEmail] = useState('')
  const [waitlistDone, setWaitlistDone] = useState(() => !!localStorage.getItem('sl-waitlist-done'))
  const [hoveredProduct, setHoveredProduct] = useState(null)
  const [hoverEmail, setHoverEmail] = useState('')

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    document.body.style.overflow = mobileNav ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileNav])

  const handleWaitlist = (e) => {
    e.preventDefault()
    if (!waitlistEmail || !waitlistVote) return
    localStorage.setItem('sl-vote', waitlistVote)
    localStorage.setItem('sl-waitlist-email', waitlistEmail)
    localStorage.setItem('sl-waitlist-done', '1')
    setWaitlistDone(true)
  }

  const handleHoverWaitlist = (name) => {
    if (!hoverEmail) return
    localStorage.setItem(`sl-waitlist-${name}`, hoverEmail)
    setHoverEmail('')
    setHoveredProduct(null)
  }

  return (
    <>
      <style>{CSS}</style>

      {/* ─── NAV ─── */}
      <nav className={`nav ${scrolled ? 'nav--scrolled' : ''}`}>
        <div className="nav-inner">
          <a href="/" className="nav-logo">
            <img src="/strimlabs-logo.png" alt="Strimlabs" height="36"/>
          </a>
          <div className={`nav-links ${mobileNav ? 'nav-links--open' : ''}`}>
            <a href="#productos" onClick={() => setMobileNav(false)}>Productos</a>
            <a href="#precios" onClick={() => setMobileNav(false)}>Precios</a>
            <a href="https://discord.gg/strimlabs" target="_blank" rel="noopener noreferrer"
               onClick={() => setMobileNav(false)}>
              <Icon name="discord" size={16}/> Discord
            </a>
          </div>
          <a href="https://app.strimlabs.com/api/auth/twitch" className="btn btn--primary nav-cta">Empezar gratis</a>
          <button className="nav-burger" onClick={() => setMobileNav(!mobileNav)} aria-label="Menu">
            <Icon name={mobileNav ? 'close' : 'menu'} size={24}/>
          </button>
        </div>
      </nav>

      {/* ─── HERO ─── */}
      <section className="hero">
        <video className="hero-video" autoPlay muted loop playsInline>
          <source src="/strimlabs-hero.mp4" type="video/mp4"/>
        </video>
        <div className="hero-overlay"/>
        <div className="container hero-container">
          <div className="hero-content">
            <span className="hero-badge">Plataforma para streamers</span>
            <h1 className="hero-title">
              Tools built<br/>for <span className="gradient-text">streamers</span>
            </h1>
            <p className="hero-sub">
              ModBot es nuestro primer producto: moderacion inteligente para tu chat de Twitch
              con IA y blacklist en tiempo real. Mas herramientas en camino.
            </p>
            <div className="hero-ctas">
              <a href="#spotlight" className="btn btn--primary btn--lg">
                Ver ModBot <Icon name="arrowRight" size={18}/>
              </a>
              <a href="#productos" className="btn btn--ghost btn--lg">Ver productos</a>
            </div>
          </div>
          <div className="hero-grid">
            {PRODUCTS.map(p => (
              <div key={p.name} className={`hero-card ${p.active ? 'hero-card--active' : 'hero-card--inactive'}`}>
                <div className={`hero-card-icon ${p.active ? '' : 'hero-card-icon--muted'}`}>
                  <Icon name={p.icon} size={28}/>
                </div>
                <span className="hero-card-name">{p.name}</span>
                {p.active
                  ? <span className="badge badge--green">Disponible</span>
                  : <span className="badge badge--muted">Proximamente</span>
                }
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PRODUCTS ─── */}
      <section className="section" id="productos">
        <div className="container">
          <h2 className="section-title">Nuestros <span className="gradient-text">productos</span></h2>
          <p className="section-sub">Una plataforma, todas las herramientas que necesitas para tu stream.</p>
          <div className="products-grid">
            {PRODUCTS.map(p => (
              <div key={p.name}
                className={`product-card ${p.active ? 'product-card--active' : 'product-card--inactive'}`}
                onMouseEnter={() => !p.active && setHoveredProduct(p.name)}
                onMouseLeave={() => setHoveredProduct(null)}>
                <div className="product-card-top">
                  <div className={`product-icon ${p.active ? 'product-icon--active' : ''}`}>
                    <Icon name={p.icon} size={32}/>
                  </div>
                  {p.active
                    ? <span className="badge badge--green">Disponible</span>
                    : <span className="badge badge--muted">Proximamente</span>
                  }
                </div>
                <h3 className="product-card-name">{p.name}</h3>
                <p className="product-card-desc">{p.desc}</p>
                {p.active ? (
                  <a href="#spotlight" className="btn btn--primary btn--sm">Ver ModBot &rarr;</a>
                ) : (
                  <div className={`product-wl ${hoveredProduct === p.name ? 'product-wl--show' : ''}`}>
                    <div className="product-wl-row">
                      <input type="email" placeholder="tu@email.com" className="input input--sm"
                        value={hoveredProduct === p.name ? hoverEmail : ''}
                        onChange={e => setHoverEmail(e.target.value)}
                        onClick={e => e.stopPropagation()}/>
                      <button className="btn btn--ghost btn--sm" onClick={() => handleHoverWaitlist(p.name)}>
                        Avisar
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── SPOTLIGHT MODBOT ─── */}
      <section className="section section--alt" id="spotlight">
        <div className="container">
          <h2 className="section-title"><span className="gradient-text">ModBot</span> en accion</h2>
          <p className="section-sub">Moderacion inteligente que protege tu chat en tiempo real.</p>

          <div className="spotlight-grid">
            <div className="spotlight-demo">
              <ChatDemo/>
            </div>
            <div className="spotlight-info">
              <div className="features-list">
                {[
                  { icon: 'shield', title: 'Blacklist + Regex', desc: 'Filtra palabras, frases y patrones con latencia cero.' },
                  { icon: 'target', title: 'IA Perspective API', desc: 'Deteccion de toxicidad con ML de Google (solo Pro).' },
                  { icon: 'chart', title: 'Dashboard completo', desc: 'Historial, estadisticas y configuracion desde tu navegador.' },
                  { icon: 'layers', title: 'Multi-canal', desc: 'Gestiona todos tus canales desde una sola cuenta.' },
                ].map(f => (
                  <div key={f.title} className="feature-item">
                    <div className="feature-icon"><Icon name={f.icon} size={20}/></div>
                    <div>
                      <strong>{f.title}</strong>
                      <p>{f.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="pricing" id="precios">
            <div className="pricing-card">
              <span className="pricing-name">Free</span>
              <span className="pricing-price">$0</span>
              <ul className="pricing-features">
                <li><Icon name="check" size={16}/> 1 canal</li>
                <li><Icon name="check" size={16}/> Blacklist + Regex</li>
                <li><Icon name="check" size={16}/> Dashboard</li>
                <li><Icon name="check" size={16}/> 1,000 msgs/mes</li>
                <li className="pricing-no"><Icon name="x" size={16}/> IA Perspective</li>
                <li className="pricing-no"><Icon name="x" size={16}/> Historial</li>
              </ul>
              <a href="https://app.strimlabs.com/api/auth/twitch" className="btn btn--ghost btn--full">Empezar gratis</a>
            </div>
            <div className="pricing-card pricing-card--pro">
              <span className="pricing-popular">Popular</span>
              <span className="pricing-name">Pro</span>
              <span className="pricing-price">$9.99 <small>USD/mes</small></span>
              <span className="pricing-alt">o $199 MXN/mes</span>
              <ul className="pricing-features">
                <li><Icon name="check" size={16}/> Canales ilimitados</li>
                <li><Icon name="check" size={16}/> Blacklist + Regex</li>
                <li><Icon name="check" size={16}/> Dashboard</li>
                <li><Icon name="check" size={16}/> Mensajes ilimitados</li>
                <li><Icon name="check" size={16}/> IA Perspective API</li>
                <li><Icon name="check" size={16}/> Historial completo</li>
              </ul>
              <a href="https://app.strimlabs.com/api/auth/twitch" className="btn btn--primary btn--full">
                <Icon name="twitch" size={18}/> Conectar con Twitch
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ─── STATS ─── */}
      <section className="section">
        <div className="container">
          <div className="stats-grid">
            {STATS.map(s => <StatCard key={s.label} {...s}/>)}
          </div>
        </div>
      </section>

      {/* ─── WHY STRIMLABS ─── */}
      <section className="section section--alt">
        <div className="container">
          <h2 className="section-title">Por que <span className="gradient-text">Strimlabs</span></h2>
          <div className="why-grid">
            {WHY_ITEMS.map(w => (
              <div key={w.title} className="why-card">
                <div className="why-icon"><Icon name={w.icon} size={32}/></div>
                <h3>{w.title}</h3>
                <p>{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── WAITLIST ─── */}
      <section className="section" id="waitlist">
        <div className="container wl-container">
          <h2 className="section-title">Proximos <span className="gradient-text">lanzamientos</span></h2>
          <p className="section-sub">Vota por el producto que quieres primero y te avisamos cuando este listo.</p>
          {waitlistDone ? (
            <div className="wl-done">
              <div className="wl-done-icon"><Icon name="check" size={40}/></div>
              <h3>Listo, te avisaremos</h3>
              <p>Tu voto por <strong>{waitlistVote}</strong> ha sido registrado.</p>
            </div>
          ) : (
            <form className="wl-form" onSubmit={handleWaitlist}>
              <div className="wl-vote">
                {PRODUCTS.filter(p => !p.active).map(p => (
                  <label key={p.name} className={`wl-option ${waitlistVote === p.name ? 'wl-option--sel' : ''}`}>
                    <input type="radio" name="vote" value={p.name}
                      checked={waitlistVote === p.name}
                      onChange={e => setWaitlistVote(e.target.value)}/>
                    <Icon name={p.icon} size={18}/>
                    <span>{p.name}</span>
                  </label>
                ))}
              </div>
              <div className="wl-input-row">
                <div className="input-wrap">
                  <span className="input-wrap-icon"><Icon name="mail" size={18}/></span>
                  <input type="email" placeholder="tu@email.com" className="input input--pl"
                    value={waitlistEmail} onChange={e => setWaitlistEmail(e.target.value)} required/>
                </div>
                <button type="submit" className="btn btn--primary"
                  disabled={!waitlistVote || !waitlistEmail}>
                  Notificame
                </button>
              </div>
            </form>
          )}
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="footer">
        <div className="container footer-inner">
          <div className="footer-brand">
            <img src="/strimlabs-logo.png" alt="Strimlabs" height="28"/>
            <p>Tools built for streamers.</p>
          </div>
          <div className="footer-links">
            <a href="#">Terminos</a>
            <a href="#">Privacidad</a>
            <a href="https://discord.gg/strimlabs" target="_blank" rel="noopener noreferrer">Discord</a>
          </div>
          <p className="footer-copy">&copy; 2025 Strimlabs. Todos los derechos reservados.</p>
        </div>
      </footer>
    </>
  )
}

/* ═══════════════════════════════════════════
   CSS
   ═══════════════════════════════════════════ */

const CSS = `
/* ─── Base ─── */
html { scroll-behavior: smooth; }
::selection { background: rgba(139,43,226,0.4); color: #fff; }

/* ─── Container ─── */
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

/* ─── Gradient text ─── */
.gradient-text {
  background: var(--gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ─── Buttons ─── */
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 22px; border-radius: 8px;
  font-size: 14px; font-weight: 600;
  text-decoration: none; cursor: pointer; border: none;
  font-family: var(--font-body); transition: all 0.25s;
  white-space: nowrap;
}
.btn--primary {
  background: var(--gradient); color: #fff;
}
.btn--primary:hover {
  opacity: 0.9; transform: translateY(-1px);
  box-shadow: 0 4px 24px rgba(139,43,226,0.35);
}
.btn--ghost {
  background: transparent; color: var(--text);
  border: 1px solid var(--border2);
}
.btn--ghost:hover { border-color: var(--cyan); color: var(--cyan); }
.btn--lg { padding: 14px 28px; font-size: 16px; border-radius: 10px; }
.btn--sm { padding: 8px 16px; font-size: 13px; }
.btn--full { width: 100%; justify-content: center; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; box-shadow: none !important; }

/* ─── Badges ─── */
.badge {
  display: inline-flex; align-items: center;
  padding: 4px 12px; border-radius: 100px;
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.badge--green { background: rgba(16,185,129,0.15); color: var(--green); }
.badge--muted { background: rgba(74,82,112,0.15); color: var(--muted); }

/* ─── Inputs ─── */
.input {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text); padding: 10px 16px; border-radius: 8px;
  font-size: 14px; font-family: var(--font-body);
  outline: none; transition: border-color 0.2s; width: 100%;
}
.input:focus { border-color: var(--cyan); }
.input--sm { padding: 8px 12px; font-size: 13px; }
.input--pl { padding-left: 42px; }

/* ─── Sections ─── */
.section { padding: 100px 0; }
.section--alt { background: var(--bg2); }
.section-title {
  font-family: var(--font-mono); font-size: 36px; font-weight: 700;
  text-align: center; margin-bottom: 16px;
}
.section-sub {
  text-align: center; color: var(--muted); font-size: 18px;
  max-width: 580px; margin: 0 auto 60px; line-height: 1.6;
}

/* ─── NAV ─── */
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  padding: 14px 0; transition: all 0.3s;
}
.nav--scrolled {
  background: rgba(13,15,20,0.92);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
}
.nav-inner {
  max-width: 1200px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.nav-logo { text-decoration: none; display: flex; align-items: center; }
.nav-logo img { height: 36px; }
.nav-links { display: flex; align-items: center; gap: 32px; }
.nav-links a {
  color: var(--muted); text-decoration: none; font-size: 14px;
  font-weight: 500; transition: color 0.2s;
  display: inline-flex; align-items: center; gap: 6px;
}
.nav-links a:hover { color: var(--text); }
.nav-cta-m { display: none; }
.nav-burger {
  display: none; background: none; border: none;
  color: var(--text); cursor: pointer; padding: 4px;
}

/* ─── HERO ─── */
.hero {
  position: relative; overflow: hidden;
  padding: 160px 0 80px; text-align: center;
}
.hero-video {
  position: absolute; top: 50%; left: 50%;
  min-width: 100%; min-height: 100%;
  width: auto; height: auto;
  transform: translate(-50%, -50%);
  object-fit: cover; z-index: 0;
}
.hero-overlay {
  position: absolute; inset: 0; z-index: 1;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(139,43,226,0.18) 0%, transparent 60%),
    linear-gradient(180deg, rgba(13,15,20,0.55) 0%, rgba(13,15,20,0.85) 60%, var(--bg) 100%);
}
.hero-container { position: relative; z-index: 2; }
.hero-badge {
  display: inline-block; padding: 6px 18px; border-radius: 100px;
  border: 1px solid var(--border2); color: var(--cyan);
  font-size: 12px; font-weight: 600; margin-bottom: 28px;
  letter-spacing: 1px; text-transform: uppercase;
  animation: fadeInDown 0.6s ease;
}
.hero-title {
  font-family: var(--font-mono); font-size: 68px; font-weight: 700;
  line-height: 1.08; margin-bottom: 24px;
  animation: fadeInUp 0.6s ease;
}
.hero-sub {
  color: var(--muted); font-size: 19px; max-width: 560px;
  margin: 0 auto 40px; line-height: 1.6;
  animation: fadeInUp 0.6s 0.12s ease both;
}
.hero-ctas {
  display: flex; align-items: center; justify-content: center; gap: 16px;
  animation: fadeInUp 0.6s 0.24s ease both;
}
.hero-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  margin-top: 80px; animation: fadeInUp 0.8s 0.36s ease both;
}
.hero-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 24px 16px;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  transition: all 0.3s;
}
.hero-card--active { border-color: var(--border2); }
.hero-card--active:hover {
  border-color: var(--cyan); transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0,229,255,0.08);
}
.hero-card--inactive { opacity: 0.45; }
.hero-card-icon { color: var(--cyan); }
.hero-card-icon--muted { color: var(--muted); }
.hero-card-name {
  font-family: var(--font-mono); font-weight: 700; font-size: 13px;
}

/* ─── PRODUCTS ─── */
.products-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }
.product-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 32px; transition: all 0.3s;
  position: relative; overflow: hidden;
}
.product-card--active { border-color: var(--border2); }
.product-card--active:hover {
  border-color: var(--cyan); transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0,229,255,0.08);
}
.product-card--inactive { opacity: 0.65; }
.product-card--inactive:hover { opacity: 1; }
.product-card-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px;
}
.product-icon {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(74,82,112,0.15); color: var(--muted);
}
.product-icon--active { background: rgba(139,43,226,0.12); color: var(--cyan); }
.product-card-name {
  font-family: var(--font-mono); font-size: 17px; font-weight: 700;
  margin-bottom: 8px;
}
.product-card-desc {
  color: var(--muted); font-size: 14px; line-height: 1.6; margin-bottom: 20px;
}
.product-wl {
  max-height: 0; opacity: 0; transition: all 0.3s ease; overflow: hidden;
}
.product-wl--show { max-height: 50px; opacity: 1; }
.product-wl-row { display: flex; gap: 8px; }

/* ─── CHAT DEMO ─── */
.chat-demo {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; overflow: hidden;
  height: 420px; display: flex; flex-direction: column;
}
.chat-header {
  display: flex; align-items: center; gap: 6px;
  padding: 12px 16px; border-bottom: 1px solid var(--border);
  background: var(--bg2);
}
.chat-dot { width: 10px; height: 10px; border-radius: 50%; }
.chat-dot.red { background: var(--red); }
.chat-dot.yellow { background: var(--yellow); }
.chat-dot.green { background: var(--green); }
.chat-title {
  font-family: var(--font-mono); font-size: 12px;
  color: var(--muted); margin-left: 8px; flex: 1;
}
.chat-live {
  background: var(--red); color: #fff; font-size: 10px;
  font-weight: 700; padding: 2px 8px; border-radius: 4px;
  animation: pulse 2s infinite;
}
.chat-body {
  flex: 1; overflow-y: auto; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.chat-body::-webkit-scrollbar { width: 4px; }
.chat-body::-webkit-scrollbar-track { background: transparent; }
.chat-body::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }
.chat-msg {
  padding: 8px 12px; border-radius: 8px;
  background: rgba(255,255,255,0.02); font-size: 14px;
  animation: msgIn 0.3s ease; transition: all 0.4s;
  line-height: 1.5;
}
.chat-msg--mod { background: rgba(239,68,68,0.06); }
.chat-text--strike { text-decoration: line-through; opacity: 0.35; }
.chat-user {
  font-family: var(--font-mono); font-weight: 700; font-size: 12px;
  margin-right: 8px;
}
.chat-text { color: var(--text); }
.chat-mod-badge {
  display: inline-flex; align-items: center; gap: 4px;
  background: rgba(239,68,68,0.12); color: var(--red);
  font-size: 10px; padding: 2px 8px; border-radius: 4px;
  margin-left: 8px; font-weight: 600; animation: fadeIn 0.3s;
  white-space: nowrap;
}

/* ─── SPOTLIGHT ─── */
.spotlight-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 48px; align-items: start; margin-bottom: 80px;
}
.features-list { display: flex; flex-direction: column; gap: 28px; }
.feature-item { display: flex; gap: 16px; }
.feature-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: rgba(139,43,226,0.12); color: var(--cyan);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.feature-item strong {
  display: block; font-family: var(--font-mono);
  font-size: 15px; margin-bottom: 4px;
}
.feature-item p { color: var(--muted); font-size: 14px; line-height: 1.5; }

/* ─── PRICING ─── */
.pricing {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 24px; max-width: 720px; margin: 0 auto;
}
.pricing-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 36px; text-align: center;
  position: relative; display: flex; flex-direction: column;
}
.pricing-card--pro { border-color: var(--cyan); background: var(--surface2); }
.pricing-popular {
  position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
  background: var(--gradient); color: #fff;
  font-size: 11px; font-weight: 700; padding: 4px 16px;
  border-radius: 100px; text-transform: uppercase; letter-spacing: 0.5px;
}
.pricing-name {
  display: block; font-family: var(--font-mono);
  font-size: 20px; font-weight: 700; margin-bottom: 8px;
}
.pricing-price {
  display: block; font-family: var(--font-mono);
  font-size: 44px; font-weight: 700; margin-bottom: 4px;
}
.pricing-price small { font-size: 14px; color: var(--muted); font-weight: 400; }
.pricing-alt {
  display: block; color: var(--muted); font-size: 13px; margin-bottom: 4px;
}
.pricing-features {
  list-style: none; text-align: left; margin: 24px 0;
  display: flex; flex-direction: column; gap: 10px; flex: 1;
}
.pricing-features li {
  display: flex; align-items: center; gap: 10px;
  font-size: 14px; color: var(--text);
}
.pricing-no { opacity: 0.35; }

/* ─── STATS ─── */
.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 24px; text-align: center;
}
.stat-card { padding: 40px 20px; }
.stat-value {
  display: block; font-family: var(--font-mono);
  font-size: 50px; font-weight: 700;
  background: var(--gradient);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 8px;
}
.stat-label { color: var(--muted); font-size: 14px; }

/* ─── WHY ─── */
.why-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; }
.why-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 36px; text-align: center;
  transition: all 0.3s;
}
.why-card:hover {
  border-color: var(--border2); transform: translateY(-4px);
}
.why-icon {
  width: 60px; height: 60px; border-radius: 16px;
  background: rgba(139,43,226,0.12); color: var(--cyan);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px;
}
.why-card h3 {
  font-family: var(--font-mono); font-size: 16px; margin-bottom: 12px;
}
.why-card p { color: var(--muted); font-size: 14px; line-height: 1.65; }

/* ─── WAITLIST ─── */
.wl-container { max-width: 600px; text-align: center; }
.wl-vote {
  display: flex; gap: 12px; justify-content: center;
  flex-wrap: wrap; margin-bottom: 28px;
}
.wl-option {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 100px;
  border: 1px solid var(--border); background: var(--surface);
  cursor: pointer; transition: all 0.2s;
  font-size: 14px; color: var(--muted);
}
.wl-option input { display: none; }
.wl-option:hover { border-color: var(--border2); }
.wl-option--sel {
  border-color: var(--cyan); color: var(--cyan);
  background: rgba(0,229,255,0.05);
}
.wl-input-row { display: flex; gap: 12px; }
.input-wrap {
  flex: 1; position: relative; display: flex; align-items: center;
}
.input-wrap-icon {
  position: absolute; left: 12px; color: var(--muted);
  display: flex; align-items: center;
}
.wl-done { padding: 48px 0; }
.wl-done-icon { color: var(--cyan); margin-bottom: 16px; }
.wl-done h3 {
  font-family: var(--font-mono); font-size: 20px;
  margin-bottom: 8px; color: var(--text);
}
.wl-done p { color: var(--muted); }

/* ─── FOOTER ─── */
.footer { border-top: 1px solid var(--border); padding: 48px 0; }
.footer-inner {
  display: flex; flex-direction: column; align-items: center;
  gap: 20px; text-align: center;
}
.footer-brand { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.footer-brand p { color: var(--muted); font-size: 14px; }
.footer-links { display: flex; gap: 24px; }
.footer-links a {
  color: var(--muted); text-decoration: none; font-size: 14px;
  transition: color 0.2s;
}
.footer-links a:hover { color: var(--text); }
.footer-copy { color: var(--muted); font-size: 12px; opacity: 0.7; }

/* ─── Animations ─── */
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes msgIn {
  from { opacity: 0; transform: translateX(-12px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.4; }
}

/* ─── Responsive ─── */
@media (max-width: 1024px) {
  .hero-grid { grid-template-columns: repeat(2, 1fr); }
  .products-grid { grid-template-columns: repeat(2, 1fr); }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-title { font-size: 52px; }
}

@media (max-width: 768px) {
  .nav-links {
    position: fixed; inset: 0; background: var(--bg);
    flex-direction: column; align-items: center; justify-content: center;
    gap: 28px; display: none; z-index: 99;
  }
  .nav-links--open { display: flex; }
  .nav-links a { font-size: 20px; }
  .nav-cta { display: none; }
  .nav-cta-m { display: inline-flex; }
  .nav-burger { display: flex; z-index: 101; }

  .hero { padding: 130px 0 60px; }
  .hero-title { font-size: 40px; }
  .hero-sub { font-size: 16px; }
  .hero-ctas { flex-direction: column; width: 100%; }
  .hero-ctas .btn { width: 100%; justify-content: center; }
  .hero-grid { grid-template-columns: 1fr 1fr; gap: 12px; }

  .section { padding: 72px 0; }
  .section-title { font-size: 28px; }
  .section-sub { font-size: 16px; margin-bottom: 40px; }

  .products-grid { grid-template-columns: 1fr; }
  .spotlight-grid { grid-template-columns: 1fr; gap: 32px; }
  .chat-demo { height: 350px; }

  .pricing { grid-template-columns: 1fr; max-width: 400px; }
  .why-grid { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .stat-value { font-size: 36px; }

  .wl-input-row { flex-direction: column; }
  .wl-vote { gap: 8px; }
  .wl-option { padding: 8px 14px; font-size: 13px; }
}

@media (max-width: 480px) {
  .hero-title { font-size: 32px; }
  .hero-grid { grid-template-columns: 1fr 1fr; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .stat-value { font-size: 28px; }
  .pricing-price { font-size: 36px; }
}
`
