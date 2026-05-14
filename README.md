# Timely

![Timely Banner](assets/banner.png)

A Discord bot for scheduling events and coordinating availability between users.

## Features

- **Admin-configured panels** — Admins define appointment types as buttons in a Discord channel. Each button can restrict who can create events and who can be invited (based on Discord roles).
- **Doodle-style voting** — Event creators propose multiple time slots. Invited participants vote on which slots work for them.
- **DM-based invitations** — All participants are notified via DM and can accept (by selecting available slots) or decline.
- **iCal export** *(planned)* — Once a final time is confirmed, participants receive an `.ics` file for their calendar.

## Setup

### Requirements

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

### Local

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate    # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your DISCORD_TOKEN

# 4. Run
python -m bot.main
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

The SQLite database is persisted in a named Docker volume (`db_data`).

### Dev Container (VS Code)

Open the project in VS Code and select **Reopen in Container**. The container mounts the workspace, installs all dependencies, and has Pylance + Ruff pre-configured.

## Admin Usage

Once the bot is running and invited to your server:

1. `/timely setup` — Set the current channel as the panel channel.
2. `/timely add_type` — Add an appointment type (button). Optionally restrict by role.
3. `/timely post_panel` — Post the panel embed with all configured buttons.

## User Flow

1. Click a button on the panel.
2. Fill in title, description, and proposed time slots in the modal.
3. Select participants (filtered by role if configured).
4. Confirm — the bot DMs all participants.
5. Participants select their available time slots (or decline) via DM.

## Project Structure

```
Timely/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Environment config
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── db.py            # DB engine & session
│   ├── cogs/
│   │   ├── admin.py         # Admin slash commands
│   │   ├── events.py        # Event creation flow
│   │   └── voting.py        # Voting handling
│   └── views/
│       ├── panel_view.py    # Panel embed & buttons
│       ├── event_modal.py   # Event creation modal
│       ├── participant_picker.py  # Participant selection
│       └── vote_view.py     # DM voting view
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── .devcontainer/
│   └── devcontainer.json
└── assets/
    ├── banner.png           # Repo banner
    └── avatar.png           # Bot avatar
```
