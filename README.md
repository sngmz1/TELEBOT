# Order Taker Bot

A Telegram order-management bot built with Python and [aiogram](https://docs.aiogram.dev/). Customers pick a service, add requested information, place an order, and admins manage/verify each order from an in-app admin panel.

## Features

- Services & packages selection
- Order creation with information collection
- Channel join gate via `/start`
- Order history & profile
- Inline admin panel (verify / reject / process / complete / cancel)
- SQLite persistence (SQLAlchemy async)

## Requirements

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/sngmz1/TELEBOT.git
cd TELEBOT
```

### 2. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate    # Linux / macOS

pip install -r requirements.txt
```

### 3. Create your `.env` file

Copy the template and fill in your own values:

```bash
cp .env.example .env
```

Then open `.env` and replace every placeholder with your real values:

| Variable                   | Description                                        |
| -------------------------- | -------------------------------------------------- |
| `BOT_TOKEN`                | Your bot token from @BotFather                     |
| `REQUIRED_CHANNEL_USERNAME`| Channel users must join (without `@`)              |
| `SUPPORT_USERNAME`         | Support contact username (without `@`)             |
| `ADMIN_IDS`                | Comma-separated Telegram user IDs of admins        |
| `UPI_ID`                   | Optional — your UPI payment ID                     |

> Never commit your `.env` file. It is already ignored by `.gitignore` and contains your private credentials.

### 4. Run the bot

```bash
python main.py
```

The bot creates its SQLite database automatically on first launch.

## Project structure

```
main.py                 # entry point
app/
  config.py             # loads configuration from .env
  database/db.py        # SQLAlchemy models & initialization
  handlers/             # telegram routes (start, services, orders, profile, more, admin)
  keyboards/buttons.py  # inline keyboards
  services/catalog.py   # services & packages catalogue
  utils.py              # menu rendering helpers
IMAGE/                  # welcome image used by the bot
```

## Security

- All credentials are read from `.env` only.
- `.env`, databases, logs, caches, and virtual environments are git-ignored.
- Never share your `BOT_TOKEN` or paste it into any file that gets committed.