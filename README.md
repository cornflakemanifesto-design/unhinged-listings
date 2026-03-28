# Unhinged Listings — Project Instructions

## What this is

A deployed Craigslist parody site at **unhingedlistings.com** where real Facebook Marketplace items are described through absurdist, stream-of-consciousness prose. The genre is "Quasi-Autofictional Absurdist Marketplace." It serves as both a live creative product and a freelance comedy writing portfolio.

## Tech stack

- **Backend:** Python / FastAPI (`server.py`)
- **Frontend:** Single-page app (`static/index.html`) — plain HTML/CSS/JS, hash-based routing, Times New Roman, Craigslist aesthetic
- **Database:** MongoDB Atlas
- **Hosting:** Render (auto-deploy from GitHub on push)
- **Repo:** github.com/cornflakemanifesto-design/unhinged-listings

## Files you touch

Only two files matter:

- `server.py` — FastAPI backend, API routes, Pydantic models, admin auth, seed data
- `static/index.html` — Complete frontend SPA (~1,634 lines) — all pages, styles, routing, admin panel

Do not create additional files unless explicitly asked. Everything lives in these two files.

## Architecture patterns

Every content section follows the same pattern:

1. **MongoDB collection** (e.g., `db.listings`, `db.missed_connections`)
2. **Pydantic models** for create/update
3. **FastAPI CRUD endpoints** (public GET, admin POST/PUT/DELETE with password query param)
4. **Admin panel tab** in the frontend with drag-and-drop reorder
5. **Frontend render function** with hash-based routing

Admin auth: password passed as query parameter `?password=`, verified against `ADMIN_PASSWORD` env var.

## Current site pages and routes

| Route | Description |
|-------|-------------|
| `#/` | Home — listings with category filter, list/gallery toggle |
| `#/listing/{id}` | Individual listing detail |
| `#/missed-connections` | Fictional absurdist personals |
| `#/missed-connections/{id}` | Individual missed connection |
| `#/about` | Project philosophy |
| `#/contact` | Contact / void-yelling placeholder |
| `#/darkweb` | Prank page — green terminal aesthetic |
| `#/admin` | Password-protected admin panel |

## Current content

- 30 listings across categories: household (20), tools (8), vintage (2)
- 2 missed connections
- No custom site settings in DB — runs on defaults in `server.py`

## API structure

Public endpoints:
- `GET /api/listings` — optional `?category=` filter
- `GET /api/listings/{id}`
- `GET /api/missed-connections`
- `GET /api/missed-connections/{id}`
- `GET /api/settings`
- `GET /api/categories`

Admin endpoints (all require `?password=`):
- `POST/PUT/DELETE /api/admin/listings/{id}`
- `POST/PUT/DELETE /api/admin/missed-connections/{id}`
- `PUT /api/admin/reorder` — accepts `{order: [id1, id2, ...]}`
- `PUT /api/admin/reorder-mc`
- `PUT /api/admin/settings`
- `GET /api/admin/export`

## Deploy process

```
git add .
git commit -m "describe what changed"
git push
```

Render auto-deploys after push. Live in ~60 seconds.

## Environment variables (on Render)

- `MONGO_URL` — MongoDB Atlas connection string
- `DB_NAME` — `unhinged_listings`
- `ADMIN_PASSWORD` — admin panel password

## Voice and tone

The writing style is absurdist, stream-of-consciousness, fourth-wall-breaking. Product descriptions start normal and spiral into existential tangents. The humor comes from the contrast between mundane commerce and philosophical meltdown. Never mean-spirited, never punching down. The comedy is self-aware and self-deprecating.

## Important conventions

- Craigslist visual aesthetic: Times New Roman, blue links, gray boxes, minimal styling
- All frontend state managed via hash routing (`location.hash`)
- Settings loaded once globally into `S` variable, used everywhere
- HTML escaped via `esc()` helper function — always use it for user-facing text
- Mobile responsive via `@media (max-width: 700px)` breakpoints
- Admin panel supports drag-and-drop reorder for all content types

## What NOT to do

- Don't add React, npm, or any build tools — this is vanilla JS
- Don't create separate CSS or JS files — everything is inline in index.html
- Don't change the deploy process or add Docker/containers
- Don't modify the MongoDB connection logic or lifespan handler unless necessary
- Don't break existing routes or endpoints — additive changes only
