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
        Participant selection : Role-filtered dropdown, creator exclusion
        Datetime picker       : Select-based date / hour / minute — no typing required
        Event creation        : 3-step flow, DM invitations, vote view
        Voting & confirmation : Doodle-style voting, auto-confirm on last reply, best-slot algorithm
        Creator controls      : Status DM, cancel button, 7-day auto-delete

    section Phase 3 · Polish
        Multi-panel support   : Multiple panels across channels, per-panel appointment types
        iCal export           : .ics file sent to all participants on confirmation
        Reminders             : /timely remind re-notifies pending participants
        Localisation          : All strings centralised in bot/strings.py
        Docs & Legal          : README, ROADMAP, EUPL-1.2 license, Code of Conduct

    section Future
        Auto-delete on restart  : Persist message IDs in DB, background cleanup task
        Auto-translation        : Automatic string translation via external API
```

## Status

| Feature | Status | Priority |
|---|---|---|
| Bot foundation & database | ✅ Done | P1 |
| Admin panel commands | ✅ Done | P1 |
| Docker + CI/CD | ✅ Done | P1 |
| Role-based access control | ✅ Done | P1 |
| 3-step event creation flow | ✅ Done | P2 |
| Select-based datetime picker | ✅ Done | P2 |
| Doodle-style voting | ✅ Done | P2 |
| Auto-confirmation & best-slot | ✅ Done | P2 |
| iCal export | ✅ Done | P3 |
| Multi-panel support | ✅ Done | P2 |
| Reminders | ✅ Done | P4 |
| Localisation (strings.py) | ✅ Done | P2 |
| Auto-delete persistence on restart | 🔲 Planned | P4 |
| Auto-translation | 🔲 Planned | P4 |
