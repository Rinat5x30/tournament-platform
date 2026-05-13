<div align="center">

# Tournament Platform

**A production-ready web platform for running competitive esports leagues — from team registration to grand final.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?logo=railway)](https://tournament-platform-production.up.railway.app)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#license)

</div>

---

## Overview

Tournament Platform is a full-stack Django application for organizing and managing competitive seasons. Organizers create seasons, configure tournaments with different stage formats, schedule matches, and track results — all in one place. Players register via Discord, form teams, and follow their stats across seasons in real time.

---

## Features

### Tournaments & Brackets
- **5 stage formats** — Round Robin, Swiss (Standard / Dutch / Accelerated), Single Elimination, Double Elimination, Group Stage
- Configurable tiebreakers per stage: head-to-head, goal difference, goals scored, Buchholz, Sonneborn-Berger, and more
- Colored table zones — promotion, playoff, tiebreaker, relegation, safe
- Automatic playoff bracket generation and round-by-round progression
- Multi-stage tournaments with configurable advancement counts between stages

### Match Management
- Match scheduling with round numbers and time slots
- Live score updates, actual start/end times, stream links
- Per-match statistics: possession, shots, saves
- Per-player statistics per match: goals, assists, saves, shots, passes
- Result confirmation by both team captains
- Match protocols (file upload) and tech-win handling

### Ratings & Awards
- ELO-based rating system (1500 base) for both players and teams
- Per-season and all-time leaderboards
- Tournament awards: Champion, Runner-up, 3rd Place, Top Scorer, Best Player, Best GK
- Full career page per player — stats and awards across every season
- Full team history page — results, roster, and standings per season

### Accounts & Roles
- Discord OAuth2 — one-click sign-in, avatar and username synced automatically
- Four-tier role system: **Player → Captain → Moderator → Admin**
- Automatic permission sync: admin role sets `is_superuser`, moderator sets `is_staff`

### Platform
- Custom moderator back-office (appeals, match results, team management)
- In-platform shop with Stripe payment integration
- Telegram bot for match notifications and updates
- Global search across tournaments, teams, and players
- Cloudinary media storage for avatars and team logos

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Django REST Framework |
| Auth | django-allauth, Discord OAuth2 |
| Database | SQLite (dev) · PostgreSQL (prod) |
| Media | Cloudinary |
| Static files | Whitenoise |
| Payments | Stripe |
| Bot | python-telegram-bot |
| Server | Gunicorn |
| Deployment | Railway |

---

## Project Structure

```
tournament_platform/
├── accounts/           # Custom user model, Discord OAuth, role system
├── tournaments/        # Seasons, tournaments, stages, brackets, career pages
├── teams/              # Team profiles, rosters, history
├── players/            # Player profiles and statistics
├── matches/            # Scheduling, results, per-player/team stats
├── ratings/            # ELO ratings, leaderboards, awards
├── admin_panel/        # Moderator back-office, appeals
├── shop/               # Item store, Stripe checkout
├── templates/          # Global HTML templates
├── static/             # CSS, JS, images
└── tournament_platform/  # Settings, URLs, WSGI/ASGI
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# 1. Clone
git clone https://github.com/Rinat5x30/tournament-platform.git
cd tournament-platform

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Environment variables
cp .env.example .env
# Fill in .env — see the table below

# 5. Database
python manage.py migrate

# 6. Superuser
python manage.py createsuperuser

# 7. Dev server
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key |
| `DEBUG` | ✅ | `True` in dev, `False` in production |
| `ALLOWED_HOSTS` | ✅ | Comma-separated hostnames, e.g. `localhost,yourdomain.com` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Comma-separated origins, e.g. `https://yourdomain.com` |
| `DISCORD_CLIENT_ID` | ✅ | From [Discord Developer Portal](https://discord.com/developers/applications) |
| `DISCORD_CLIENT_SECRET` | ✅ | From [Discord Developer Portal](https://discord.com/developers/applications) |

> **Discord OAuth redirect URI** — add `http://localhost:8000/accounts/discord/login/callback/` in your Discord app settings for local development.

---

## Deployment

The project ships ready for Railway:

1. Push to GitHub
2. Create a new Railway project → **Deploy from GitHub repo**
3. Set all variables from the table above in **Variables** tab
4. Railway picks up `Procfile` and runs `gunicorn tournament_platform.wsgi` automatically

For static files, Whitenoise serves them without a CDN. For media (avatars, logos), configure Cloudinary credentials when needed.

---

## License

This project is proprietary. All rights reserved.
