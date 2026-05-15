# Timely — Roadmap

```mermaid
timeline
    title Timely Development Roadmap

    section Phase 1 · Core
        Bot foundation        : Bot entry point, config, cog loading
        Database              : SQLAlchemy models — Panel, AppointmentType, Event, Slot, Participant, Vote
        Admin commands        : create_panel, add_type, post_panel, list_panels, refresh_panel, delete_panel
        Infrastructure        : Docker, DevContainer, GitHub Actions CI/CD (amd64 + arm64)

    section Phase 2 · Event Flow
        Participant selection : Role-filtered dropdown, creator exclusion, rate limiting
        Datetime picker       : Select-based date / hour / minute — no typing required
        Event creation        : 3-step flow, DM invitations, vote view
        Voting & confirmation : Doodle-style voting, auto-confirm on last reply, best-slot algorithm
        Creator controls      : Status DM, cancel button, iCal export

    section Phase 3 · Polish & Management
        Multi-panel support   : Multiple panels across channels, per-panel appointment types
        Panel management      : edit_type, disable/enable, announce command
        Reminders             : /timely remind re-notifies pending participants
        Localisation          : All strings centralised in bot/strings.py (English)
        Multi-instance        : COMMAND_GROUP env var for prod/dev separation

    section Phase 4 · Persistence & Reliability
        PostgreSQL + Alembic  : Production DB, schema migrations, entrypoint.sh
        Persistent views      : bot.add_view() on restart — buttons survive reboots
        DM auto-delete        : Message IDs in DB, hourly background cleanup task
        Backup & Restore      : /timely backup exports JSON.gz, /timely restore reimports

    section Phase 5 · Participant Controls
        Status for all        : /timely status shows own + invited events with filter
        Withdrawal            : Participants can withdraw acceptance (open + confirmed)
        Auto-cancel           : All decline/withdraw → event cancelled automatically
        Cancel confirmed      : Requester can cancel confirmed appointments too

    section Phase 6 · Calendar & UX
        Google Calendar       : Pre-filled URL button in confirmation DM (no OAuth required)
        .ics on demand        : Download .ics button in confirmation DM
        Title prefix          : Configurable prefix per appointment type prepended to event titles
        Bot status            : Rotating fun status messages every 3 hours
        Legal                 : Terms of Service + Privacy Policy (GDPR, Germany/EU)

    section Future
        Google Calendar OAuth : Full OAuth2 flow — auto-create events without user action
```

## Status

| Feature | Status | Priority |
|---|---|---|
| Bot foundation & database | ✅ Done | P1 |
| Admin panel commands | ✅ Done | P1 |
| Docker + CI/CD | ✅ Done | P1 |
| PostgreSQL + Alembic | ✅ Done | P1 |
| Persistent views on restart | ✅ Done | P1 |
| Role-based access control | ✅ Done | P1 |
| Rate limiting per button | ✅ Done | P2 |
| Configurable title prefix | ✅ Done | P2 |
| 3-step event creation flow | ✅ Done | P2 |
| Select-based datetime picker | ✅ Done | P2 |
| Doodle-style voting | ✅ Done | P2 |
| Auto-confirmation & best-slot | ✅ Done | P2 |
| Google Calendar URL button | ✅ Done | P2 |
| .ics download button | ✅ Done | P2 |
| Multi-panel support | ✅ Done | P2 |
| edit_type / disable / enable | ✅ Done | P2 |
| /timely announce | ✅ Done | P2 |
| /timely status with filter | ✅ Done | P2 |
| Multi-instance (COMMAND_GROUP) | ✅ Done | P2 |
| Backup & Restore | ✅ Done | P2 |
| Auto-cancel when all decline | ✅ Done | P1 |
| Cancel confirmed appointments | ✅ Done | P3 |
| Participant withdrawal | ✅ Done | P3 |
| Reminders | ✅ Done | P3 |
| Localisation (strings.py) | ✅ Done | P3 |
| DM auto-delete persistence | ✅ Done | P4 |
| Rotating bot status | ✅ Done | P3 |
| Terms of Service & Privacy Policy | ✅ Done | P3 |
| Google Calendar OAuth2 (full) | 🔲 Planned | P4 |
