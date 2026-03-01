# Strimlabs — Monorepo

Plataforma SaaS de herramientas para streamers.

## Estructura

```
strimlabs/
├── landing/        Landing page corporativa (React + Vite)
├── ModBot/         Bot de moderación para Twitch (FastAPI + twitchio + React)
└── shared/         Componentes, tema y assets compartidos
```

## Proyectos

| Proyecto | Tech | Puerto local |
|---|---|---|
| landing | React + Vite | :5173 |
| ModBot/web | React + Vite | :5174 |
| ModBot/api | FastAPI | :8000 |
| ModBot/bot | twitchio | — |
| PostgreSQL | Docker | :5432 |

## Arranque rápido

### Landing
```bash
cd landing
npm install
npm run dev
```

### ModBot completo
```bash
cd ModBot
cp .env.example .env   # llenar variables
docker compose up -d --build
```

## Paleta de colores
- Purple: `#8B2BE2`
- Cyan:   `#00E5FF`
- BG:     `#0D0F14`
- Gradiente: `linear-gradient(90deg, #8B2BE2, #00E5FF)`

## Repositorio
`https://github.com/joserzgz/strimlabs`
