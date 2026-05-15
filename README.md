
![Timely Banner](assets/banner.png)

![Python](https://img.shields.io/badge/python-3670A0?style=flat-square&logo=python&logoColor=white&labelColor=161923&color=1b1e2b)
[![DOCKER](https://img.shields.io/badge/containerized-white?style=flat-square&logo=docker&logoColor=white&labelColor=161923&color=1b1e2b)](#)
[![CodeFactor](https://img.shields.io/codefactor/grade/github/sirquacksalot/timely?style=flat-square&logo=devbox&label=%C2%A0&labelColor=161923&color=1b1e2b)](https://www.codefactor.io/repository/github/sirquacksalot/timely)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/SirQuacksAlot/timely/.github/workflows/docker.yml?style=flat-square&logo=github&label=build&labelColor=161923&color=1b1e2b)](#)
[![License: EUPL-1.2](https://img.shields.io/badge/License-EUPL_1.2-blue.svg?style=flat-square&logo=opensourceinitiative&logoColor=white&labelColor=161923&color=1b1e2b)](LICENSE)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg?style=flat-square&logo=contributorcovenant&logoColor=white&labelColor=161923&color=1b1e2b)](CODE_OF_CONDUCT.md)

<br clear="left" />

<img src="assets/avatar.png" width="120" alt="Timely mascot" align="left" />


### Hi, I'm Timely!

I'm a Discord bot for scheduling appointments and coordinating availability across your server — without the endless back-and-forth.

<br clear="left" />

## Features

- **Multi-panel support** — Admins create multiple panels in different channels, each with its own set of appointment type buttons.
- **Role-based access** — Each button can restrict who may create a request and who can be invited, based on Discord roles.
- **Select-based time picker** — Organisers choose time slots using dropdown menus (date, hour, minute) — no manual typing required.
- **Doodle-style voting** — Participants receive a DM and vote on which slots work for them. The organiser is automatically counted as available for all slots.
- **Auto-confirmation** — Once every participant has replied, the bot picks the slot with the most availability and confirms automatically. Ties are broken by earliest date.
- **iCal export** — All participants (including the organiser) receive a `.ics` file upon confirmation, ready to import into any calendar app.
- **Cancellation** — Organisers can cancel a pending request at any time; all participants are notified via DM. If all invited participants decline, the request is cancelled automatically.
- **Rate limiting** — Each button can be configured with a maximum number of simultaneous open requests per user.
- **Reminders** — `/timely remind` sends a follow-up DM to anyone who has not yet replied.
- **Persistent buttons** — Panel buttons and vote views survive bot restarts.
- **Announcements** — `/timely announce` posts a formatted info embed in any channel.

## Requirements

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- **Server Members Intent** enabled in the Developer Portal (Bot → Privileged Gateway Intents)

## Setup

### Docker (recommended)

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

`.env` must contain:

```
DISCORD_TOKEN=your_bot_token
POSTGRES_PASSWORD=a_secure_password
DATABASE_URL=postgresql+asyncpg://timely:a_secure_password@db/timely
```

Then start:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

On first start, Alembic automatically runs `upgrade head` to create all database tables.

### Local (SQLite, no Docker)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate    # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Set DISCORD_TOKEN and DATABASE_URL=sqlite+aiosqlite:///timely.db

# 4. Run
python -m bot.main
```

### Dev Container (VS Code)

Open the project in VS Code and select **Reopen in Container**. The workspace is mounted automatically with Pylance and Ruff pre-configured. Uses SQLite by default.

## Admin Setup

### 1. Create a panel

Run this command in the channel where the panel should appear:

```
/timely create_panel name:Team
```

### 2. Add appointment type buttons

```
/timely add_type panel:Team label:1-on-1
/timely add_type panel:Team label:Team Meeting invitee_role:@TeamMember max_requests:2
```

| Parameter | Description |
|---|---|
| `panel` | Which panel to add the button to |
| `label` | Button label shown in Discord |
| `creator_role` | Only users with this role may use the button *(optional)* |
| `invitee_role` | Only users with this role can be invited *(optional)* |
| `max_requests` | Max simultaneous open requests per user *(optional, default: 1)* |

### 3. Post the panel

```
/timely post_panel panel:Team
```

### Panel management

| Command | Description |
|---|---|
| `/timely list_panels` | Show all configured panels and their status |
| `/timely refresh_panel panel:…` | Delete and re-post a panel |
| `/timely delete_panel panel:…` | Delete a panel and all its buttons |
| `/timely disable panel:…` | Pause a panel — buttons show "unavailable" |
| `/timely enable panel:…` | Re-enable a paused panel |
| `/timely list_types panel:…` | Show all buttons in a panel |
| `/timely edit_type panel:… label:…` | Edit an existing button (label, roles) |
| `/timely remove_type panel:… label:…` | Remove a button from a panel |
| `/timely announce` | Post a formatted info embed in the current channel |

## User Flow

1. Click an appointment type button on a panel.
2. **Step 1/3** — Select participants from a dropdown (filtered by role if configured).
3. **Step 2/3** — Add one or more time slots using the date, hour and minute selectors.
4. **Step 3/3** — Fill in a title and optional description in the modal.
5. The bot sends a DM to each participant with the proposed slots and an **Accept** / **Decline** option.
6. Once all participants have replied, the bot automatically confirms the best slot and sends everyone a confirmation DM with an `.ics` calendar file.

### User commands

| Command | Description |
|---|---|
| `/timely status` | View your appointment requests — filter by `All`, `Open`, `Confirmed` or `Cancelled` |
| `/timely remind` | Re-send a reminder DM to participants who have not yet replied |

## Localisation

All user-facing text is stored in [`bot/strings.py`](bot/strings.py) in the `S` class. To change the language, edit the string values in that file — no other files need to be touched.

## Project Structure

```
Timely/
├── bot/
│   ├── main.py                  # Entry point, restores persistent views on startup
│   ├── config.py                # Environment config
│   ├── strings.py               # All user-facing text (edit to change language)
│   ├── ical.py                  # iCal (.ics) file generator
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── db.py                # Async DB engine & session
│   ├── cogs/
│   │   ├── admin.py             # All slash commands
│   │   └── voting.py            # Background task: DM cleanup after 7 days
│   └── views/
│       ├── panel_view.py        # Panel embed & appointment type buttons
│       ├── participant_picker.py # Step 1: participant selection
│       ├── slot_picker.py       # Step 2: date/time slot selection
│       ├── event_modal.py       # Step 3: title & description modal
│       ├── vote_view.py         # Participant DM: slot voting (persistent)
│       └── creator_view.py      # Organiser DM: status, cancel, auto-confirm (persistent)
├── alembic/
│   ├── env.py                   # Async Alembic environment
│   └── versions/                # Schema migrations
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml       # PostgreSQL + bot
│   ├── entrypoint.sh            # Runs migrations then starts bot
│   └── .dockerignore
├── .devcontainer/
│   └── devcontainer.json
└── assets/
    ├── banner.png
    └── avatar.png
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development timeline and planned features.

## CI / CD

A GitHub Actions workflow (`.github/workflows/docker.yml`) builds and pushes a multi-platform Docker image (`linux/amd64` + `linux/arm64`) to the GitHub Container Registry on every version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```
