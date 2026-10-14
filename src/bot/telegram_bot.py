import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from ..config import settings
from ..services.freeagent import FreeAgentClient

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
    user = update.effective_user
    text = update.message.text.strip()

    # Check if user is connected
    if not active_user_ids:
        await update.message.reply_html("You're not connected to a FreeAgent account yet. Ask David to connect.")
        return

    # Build the client (in production, use a proper store)
    # For now, we need the access token - this is a placeholder
    # In production, look up the user's stored token
    await update.message.reply_html("Processing your query...")


def build_application() -> Application:
    """Build the Telegram application with webhook support."""
    from ..config import settings

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))

    # Webhook
    webhook_secret = settings.TELEGRAM_WEBHOOK_SECRET or "default-secret"
    webhook_url = os.environ.get("WEBHOOK_URL", "").rstrip("/")
    if webhook_url:
        app.updater.bot.set_webhook(url=f"{webhook_url}/webhook/{webhook_secret}")

    return app


def setup_webhook(app: Application, webhook_url: str, secret: str):
    """Set the webhook URL for the bot."""
    app.updater.bot.set_webhook(url=f"{webhook_url}/webhook/{secret}")
    logger.info(f"Webhook set to {webhook_url}/webhook/{secret}")
