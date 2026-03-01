# PROMPT: Strimlabs Landing Page

Lee primero el archivo CLAUDE.md en la raíz para entender el contexto completo del proyecto.

## Tu tarea
Implementar la landing page corporativa de Strimlabs en:
`landing/src/pages/Landing.jsx`

## Identidad visual (obligatorio)
- Paleta: ver CLAUDE.md o shared/theme.css
- Logo: usar el SVG de shared/components/StrimlabsLogo.jsx
- Tipografía: Space Mono + DM Sans (Google Fonts)
- Tono: minimalista moderno, dark theme, tech/streaming

## Secciones en orden

### 1. Nav
- Logo (StrimlabsWordmark) + links: Productos, Precios, Discord
- CTA: "Empezar gratis" → /api/auth/twitch

### 2. Hero — Plataforma
- Headline: "Tools built for streamers"
- Sub: ModBot es el primer producto disponible hoy
- CTA primario: "Ver ModBot →" | CTA secundario: "Ver productos"
- Visual: grid de productos donde ModBot es el único activo,
  el resto muestra "Próximamente" en gris

### 3. Productos (cards)
- ModBot (activo): badge "Disponible", "Ver ModBot →"
- Alerts & Overlays (inactivo): "Próximamente"
- Stream Analytics (inactivo): "Próximamente"
- Chat Interact (inactivo): "Próximamente"
- Hover en inactivos: tooltip + input waitlist email

### 4. Spotlight ModBot
- Demo animado del chat siendo moderado en tiempo real
  (mensajes aparecen, algunos se tachan con badge de razón)
- Features: Blacklist, IA Perspective API, Dashboard, Multi-canal
- Planes: Free vs Pro ($9.99 USD / $199 MXN)
- CTA: "Conectar con Twitch" → /api/auth/twitch

### 5. Stats (IntersectionObserver + CountUp)
- 2,400,000+ mensajes moderados
- 98% precisión, 340+ streamers, 0ms latencia blacklist

### 6. Por qué Strimlabs (3 columnas)
- Construido para streamers | Crece contigo | Más herramientas en camino

### 7. Waitlist
- Votación: ¿qué producto quieres primero?
- Input email + botón "Notifícame"
- Guardar en localStorage, mostrar confirmación

### 8. Footer
- Logo + tagline | Links legales | Copyright Strimlabs 2025

## Requerimientos técnicos
- Single file JSX
- Animaciones CSS puras, sin librerías externas
- Totalmente responsive
- Las rutas de API apuntan a /api/auth/twitch (proxy via Vite)
