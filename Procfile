web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
worker: python -c "from src.bot.telegram_bot import build_application; app = build_application(); app.run()"
