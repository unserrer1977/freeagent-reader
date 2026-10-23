from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..config import settings
from ..db import get_db
from ..models import ApplicationUser, get_active_freeagent_user
from src.services.freeagent import FreeAgentClient

router = APIRouter(prefix="/freeagent", tags=["freeagent"])


class QueryRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


class QueryResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None


def get_freeagent_user(
    x_freeagent_user_id: Optional[str] = Header(default=None, alias="x-freeagent-user-id"),
    db: Session = Depends(get_db),
):
    if not x_freeagent_user_id:
        raise HTTPException(status_code=401, detail="Missing FreeAgent user ID")
    user = get_active_freeagent_user(db, x_freeagent_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not connected to FreeAgent account")
    return user


@router.post("/query")
def send_query(
    req: QueryRequest,
    user: ApplicationUser = Depends(get_freeagent_user),
):
    """
    Receive a natural-language query and answer it from FreeAgent (read-only).
    """
    client = FreeAgentClient(
        settings,
        user.freeagent_access_token,
        user.is_sandbox,
        user.freeagent_company_name,
    )
    try:
        result = client.answer_query(req.query)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
    return QueryResponse(success=True, data=result.data, message=result.message)
