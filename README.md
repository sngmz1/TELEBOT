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
| `WEBHOOK_BASE_URL`         | Public HTTPS base URL (your app or tunnel)         |
| `PORT`                     | HTTP server port (defaults to `8080`)              |
| `WEBHOOK_HOST`             | Bind address (defaults to `0.0.0.0`)               |
| `WEBHOOK_PATH`             | Webhook endpoint path (defaults to `/webhook`)     |
| `WEBHOOK_SECRET`           | Optional random string for webhook request signing |

> Never commit your `.env` file. It is already ignored by `.gitignore` and contains your private credentials.

### 4. Run the bot

```bash
python main.py
```

The bot creates its SQLite database automatically on first launch.

## Local Development

The app runs an HTTP server that receives updates from Telegram through a
**webhook**. Telegram requires the webhook URL to be a **publicly accessible
HTTPS URL**, so a plain `localhost` address will not work.

### Option A — Public tunnel (recommended for local testing)

1. Install [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
   or [ngrok](https://ngrok.com/) and start a tunnel on the same port as the app:

   ```bash
   cloudflared tunnel --url http://127.0.0.1:8080
   # or
   ngrok http 8080
   ```

2. Copy the returned HTTPS URL (for example `https://abc123.trycloudflare.com`)
   and set it as `WEBHOOK_BASE_URL` in your `.env`:

   ```dotenv
   WEBHOOK_BASE_URL=https://abc123.trycloudflare.com
   ```

3. Start the bot and keep both the tunnel and the bot running:

   ```bash
   python main.py
   ```

4. Health check: open the tunnel URL (or `http://127.0.0.1:8080`) in a browser —
   it should show `Bot is running.`

> The webhook is set automatically on startup. Every time you restart the app
> with a new tunnel URL, update `WEBHOOK_BASE_URL` first so the webhook is
> re-registered to the new public address.

### Option B — Polling (quick smoke test only)

If you only want to check the handlers, you can temporarily run the previous
polling mode (see the git history of `main.py`). Do not deploy that mode to Render.

## Render Deployment

This app is designed to run as a Render **Web Service**.

1. Push this repository to GitHub and connect it to a new Render Web Service
   (or use the Blueprint / existing service).
2. Set the settings:

   | Setting        | Value                     |
   | -------------- | ------------------------- |
   | Build Command  | `pip install -r requirements.txt` |
   | Start Command  | `python main.py`          |
   | Instance Type  | Free or paid              |

3. Add the environment variables in the Render dashboard:

   - `BOT_TOKEN` — your bot token
   - `REQUIRED_CHANNEL_USERNAME` — channel users must join (without `@`)
   - `SUPPORT_USERNAME` — support contact (without `@`)
   - `ADMIN_IDS` — comma-separated admin Telegram IDs
   - `UPI_ID` — optional
   - `WEBHOOK_BASE_URL` — `https://<your-service-name>.onrender.com`
   - `WEBHOOK_SECRET` — any random string (optional but recommended)

   `PORT` is injected automatically by Render; you do not need to set it.

4. Deploy. Render runs the app, and on startup the bot registers its webhook at
   `https://<your-service-name>.onrender.com/webhook`.

5. Confirm the service is healthy: Render's health checks hit `GET /`, which
   returns `Bot is running.`

> Note: Render's free(er) instances use an ephemeral filesystem — the SQLite
> database (`bot_database.db`) is created at runtime but is reset on each
> redeploy. If you need persistent data, add a database later; the bot logic
> itself does not need to change for that.

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