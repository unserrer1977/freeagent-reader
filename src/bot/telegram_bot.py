import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from src.api.config import settings
from src.services.freeagent import FreeAgentClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active user ids (in production, use a proper store)
active_user_ids = set()


async def start(update: Update, context: ContextTypes):
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.first_name}! I'm your FreeAgent reader. "
        f"Send me a message like 'show my accounts' or 'what invoices are overdue?' "
        f"and I'll fetch it for you from FreeAgent (read-only)."
    )


async def connect(update: Update, context: ContextTypes):
    user = update.effective_user
    await update.message.reply_html(
        f"To connect your FreeAgent account, ask David (the host) to start the OAuth flow. "
        f"You'll receive a link to authorize."
    )


async def handle_query(update: Update, context: ContextTypes):
    """Handle a text message by querying FreeAgent and replying with the result."""
    user = update.effective_user
    text = update.message.text.strip()

    try:
        # Call the query API endpoint
        import httpx
        from ..config import settings

        webhook_secret = settings.TELEGRAM_WEBHOOK_SECRET or "default-secret"
        api_base = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
        response = httpx.post(
            f"{api_base}/api/query",
            json={"query": text},
            headers={"x-telegram-user-id": str(user.id)},
            timeout=30.0,
        )
        data = response.json()
        if data.get("success") and data.get("data"):
            await update.message.reply_html(f"Here's what I found: {data['data']}")
        else:
            await update.message.reply_html(f"Sorry, I couldn't fetch that: {data.get('error', data.get('message', 'Unknown error'))}")
    except Exception as e:
        await update.message.reply_html(f"Error: {e}")


def build_application() -> Application:
    """Build the Telegram application with webhook support."""
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))

    # Webhook (v21 uses app.bot, not app.updater)
    bot = app.bot
    webhook_secret = settings.TELEGRAM_WEBHOOK_SECRET or "default-secret"
    webhook_url = os.environ.get("WEBHOOK_URL", "").rstrip("/")
    if webhook_url:
        bot.set_webhook(url=f"{webhook_url}/webhook/{webhook_secret}")

    return app


async def process_webhook(webhook_secret: str, body: dict):
    """Process incoming webhook update from Telegram."""
    from telegram import Update
    from telegram.ext import ContextTypes

    try:
        update = Update.de_json(body, None)  # None = no dispatcher yet
        # Use the global application
        app = build_application()
        await app.process_update(update)
        return {"ok": True, "result": "processed"}
    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    app = build_application()
    app.run()

