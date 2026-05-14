# Timely

![Timely Banner](assets/banner.png)

A Discord bot for scheduling appointments and coordinating availability across your server.

## Features

- **Multi-panel support** — Admins create multiple panels in different channels, each with its own set of appointment type buttons.
- **Role-based access** — Each button can restrict who may create a request and who can be invited, based on Discord roles.
- **Select-based time picker** — Organisers choose time slots using dropdown menus (date, hour, minute) — no manual typing required.
- **Doodle-style voting** — Participants receive a DM and vote on which slots work for them. The organiser is automatically counted as available for all slots.
- **Auto-confirmation** — Once every participant has replied, the bot picks the slot with the most availability and confirms automatically. Ties are broken by earliest date.
- **iCal export** — All participants (including the organiser) receive a `.ics` file upon confirmation, ready to import into any calendar app.
- **Cancellation** — Organisers can cancel a pending request at any time; all participants are notified via DM.
- **Reminders** — `/timely remind` sends a follow-up DM to anyone who has not yet replied.

## Requirements

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- **Server Members Intent** enabled in the Developer Portal (Bot → Privileged Gateway Intents)

## Setup

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
# Add your DISCORD_TOKEN to .env

# 4. Run
python -m bot.main
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

The SQLite database is persisted in a named Docker volume (`db_data`).

### Dev Container (VS Code)

Open the project in VS Code and select **Reopen in Container**. The workspace is mounted automatically with Pylance and Ruff pre-configured.

## Admin Setup

### 1. Create a panel

Run this command in the channel where the panel should appear:

```
/timely create_panel name:Team
```

### 2. Add appointment type buttons

```
/timely add_type panel:Team label:1-on-1
/timely add_type panel:Team label:Team Meeting nur_diese_rolle_einladen:@TeamMember
```

| Parameter | Description |
|---|---|
| `panel` | Which panel to add the button to |
| `label` | Button label shown in Discord |
| `nur_ersteller_mit_rolle` | Only users with this role may use the button *(optional)* |
| `nur_diese_rolle_einladen` | Only users with this role can be invited *(optional)* |

### 3. Post the panel

```
/timely post_panel panel:Team
```

### Panel management

| Command | Description |
|---|---|
| `/timely list_panels` | Show all configured panels |
| `/timely refresh_panel panel:…` | Delete and re-post a panel |
| `/timely delete_panel panel:…` | Delete a panel and all its buttons |
| `/timely list_types panel:…` | Show all buttons in a panel |
| `/timely remove_type panel:… label:…` | Remove a button from a panel |

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
| `/timely status` | View the status of your open appointment requests |
| `/timely remind` | Re-send a reminder DM to participants who have not yet replied |

## Localisation

All user-facing text is stored in [`bot/strings.py`](bot/strings.py) in the `S` class. To change the language, edit the string values in that file — no other files need to be touched.

## Project Structure

```
Timely/
├── bot/
│   ├── main.py                  # Entry point
│   ├── config.py                # Environment config
│   ├── strings.py               # All user-facing text
│   ├── ical.py                  # iCal (.ics) file generator
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── db.py                # Async DB engine & session
│   ├── cogs/
│   │   └── admin.py             # All slash commands
│   └── views/
│       ├── panel_view.py        # Panel embed & appointment type buttons
│       ├── participant_picker.py # Step 1: participant selection
│       ├── slot_picker.py       # Step 2: date/time slot selection
│       ├── event_modal.py       # Step 3: title & description modal
│       ├── vote_view.py         # Participant DM: slot voting
│       └── creator_view.py      # Organiser DM: status, cancel, auto-confirm
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── .devcontainer/
│   └── devcontainer.json
└── assets/
    ├── banner.png
    └── avatar.png
```

## CI / CD

A GitHub Actions workflow (`.github/workflows/docker.yml`) builds and pushes a multi-platform Docker image (`linux/amd64` + `linux/arm64`) to the GitHub Container Registry on every version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```
