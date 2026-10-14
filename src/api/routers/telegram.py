from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/telegram", tags=["telegram"])


class WebhookRequest(BaseModel):
    # python-telegram-bot webhook payload
    message: Optional[dict] = None
    channel_post: Optional[dict] = None
    callback_query: Optional[dict] = None
    error_code: Optional[int] = None
