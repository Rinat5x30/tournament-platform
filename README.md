# Tournament Platform

A full-featured web platform for organizing and managing competitive tournaments. Teams register, matches are scheduled and tracked, standings update in real time, and players can follow every season from registration to grand final.

---

## Features

- **Tournament Management** — create seasons and tournaments with configurable formats: Round Robin, Swiss, Single/Double Elimination, Group Stage
- **Team & Player Profiles** — team pages with logos, rosters, and per-player stats
- **Smart Bracket & Standings** — automatic match generation, live standings tables with configurable tiebreakers
- **Discord OAuth** — one-click sign-in via Discord; Discord username/avatar synced automatically
- **Role System** — Player → Captain → Moderator → Admin with automatic permission sync
- **Admin Panel** — custom back-office for moderators (appeals, match results, team management)
- **Shop** — in-platform item store with Stripe payment integration
- **Telegram Bot** — notifications and match updates via Telegram
- **Media Storage** — avatar/logo uploads via Cloudinary
- **Deployment-ready** — Whitenoise static files, Gunicorn WSGI, Railway-compatible

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6, Django REST Framework |
| Auth | django-allauth, Discord OAuth2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Storage | Cloudinary (media), Whitenoise (static) |
| Payments | Stripe |
| Bot | python-telegram-bot |
| Server | Gunicorn |
| Deployment | Railway |

---

## Project Structure

```
tournament_platform/
├── accounts/          # Custom user model, Discord OAuth
├── tournaments/       # Seasons, tournaments, stages, brackets
├── teams/             # Team profiles and rosters
├── players/           # Player profiles and statistics
├── matches/           # Match scheduling and results
├── ratings/           # ELO / season ratings
├── admin_panel/       # Moderator back-office, appeals
├── shop/              # Item store, Stripe checkout
├── templates/         # Global HTML templates
├── static/            # CSS, JS, images
└── tournament_platform/  # Project settings, URLs
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/Rinat5x30/tournament-platform.git
cd tournament-platform

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your values (see Environment Variables below)

# 5. Apply migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins for CSRF |
| `DISCORD_CLIENT_ID` | Discord OAuth application client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth application client secret |

> **Discord OAuth setup:** go to [discord.com/developers/applications](https://discord.com/developers/applications), create an app, and add `http://localhost:8000/accounts/discord/login/callback/` as a redirect URI.

---

## Deployment (Railway)

The project is configured for Railway out of the box:

1. Push to GitHub
2. Create a new Railway project from the repo
3. Add all environment variables from `.env.example` in the Railway dashboard
4. Railway auto-detects the `Procfile` and runs `gunicorn tournament_platform.wsgi`

---

## License

This project is proprietary. All rights reserved.
