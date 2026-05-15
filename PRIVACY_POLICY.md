# Privacy Policy

**Last updated:** 2026-05-15

## 1. Overview

This Privacy Policy describes how Timely ("the bot", "we") collects, uses, and stores data when you interact with it on Discord. We are committed to handling your data responsibly and only collecting what is strictly necessary for the bot to function.

## 2. Data We Collect

When you use Timely, the following data is stored in a self-hosted database:

| Data | Purpose |
|---|---|
| Discord User ID | Identifying appointment requesters and participants |
| Discord Guild (Server) ID | Associating panels and appointments with a server |
| Discord Channel ID | Storing the channel a panel is posted in |
| Discord Message ID | Tracking DMs sent by the bot for automatic deletion after 7 days |
| Appointment title & description | Provided by the user when creating an appointment request |
| Proposed time slots | Provided by the user during the scheduling process |
| Availability votes | Submitted by participants to indicate which time slots work for them |

We do **not** collect:

- Real names, email addresses, or contact information
- Message content outside of appointment titles and descriptions submitted via bot commands
- Any data beyond what is listed above

## 3. How We Use Your Data

Data is used exclusively to provide the scheduling functionality of Timely:

- Creating and managing appointment requests
- Sending Direct Messages to invited participants
- Determining the best available time slot
- Automatically deleting bot DMs after 7 days

## 4. Data Retention

- Appointment data is retained until explicitly deleted via the `/timely restore` command (which replaces all data) or a server-level database reset.
- Direct Message IDs are automatically cleared from the database after 7 days, following the deletion of the corresponding messages.

## 5. Data Sharing

We do not sell, trade, or share your data with any third parties. Data is stored exclusively in a self-hosted database controlled by the server administrator.

## 6. Data Security & Hosting

Timely stores data in a PostgreSQL database hosted in **Germany, European Union**. All data processing takes place within the EU and is subject to the General Data Protection Regulation (GDPR).

Security practices include strong access controls, encrypted connections, and regular backups. We recommend that any self-hosted instances follow the same standards.

## 7. Your Rights

Depending on your jurisdiction, you may have the right to:

- Request access to the data stored about you
- Request deletion of your data
- Object to data processing

To exercise these rights, please contact the administrator of the Discord server you are using Timely on, or open an issue on the [GitHub repository](https://github.com/SirQuacksALot/Timely).

## 8. Children's Privacy

Timely is not directed at children under the age of 13. We do not knowingly collect data from children. If you believe a child has submitted data through the bot, please contact us so it can be removed.

## 9. Changes to This Policy

This Privacy Policy may be updated at any time. The date at the top of this document reflects the most recent revision. Continued use of the bot after changes are published constitutes acceptance of the updated policy.

## 10. Contact

For privacy-related questions or requests, please open an issue on the [GitHub repository](https://github.com/SirQuacksALot/Timely).
