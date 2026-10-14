from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

from .config import settings


class ApplicationUser(Base):
    __tablename__ = "application_users"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(String, unique=True, index=True, nullable=False)
    telegram_username = Column(String, nullable=True)
    freeagent_account_id = Column(String, unique=True, index=True, nullable=False)
    freeagent_access_token = Column(String, nullable=False)
    freeagent_refresh_token = Column(String, nullable=True)
    freeagent_token_expires_at = Column(DateTime, nullable=True)
    freeagent_company_name = Column(String, nullable=True)
    freeagent_permissions = Column(String, nullable=True)
    is_sandbox = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class FreeAgentToken(Base):
    __tablename__ = "freeagent_tokens"

    id = Column(Integer, primary_key=True)
    account_id = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    company_name = Column(String, nullable=True)
    permissions = Column(String, nullable=True)
    is_sandbox = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


def _now():
    return datetime.now(timezone.utc)


def _utc_from_timestamp(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def get_or_create_telegram_user(db: Session, telegram_user_id: str, username: Optional[str] = None):
    """Ensure a Telegram user row exists. If they connect FreeAgent, upgrade fields."""
    user = db.scalar(select(ApplicationUser).where(ApplicationUser.telegram_user_id == telegram_user_id))
    if user is None:
        user = ApplicationUser(
            telegram_user_id=str(telegram_user_id),
            telegram_username=username,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(user)
        db.commit()
    return user


def get_or_create_freeagent_account(
    db: Session,
    telegram_user_id: str,
    account_id: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expires_at: Optional[datetime] = None,
    company_name: Optional[str] = None,
    permissions: Optional[str] = None,
):
    user = db.scalar(
        select(ApplicationUser).where(ApplicationUser.telegram_user_id == str(telegram_user_id))
    )
    if user is None:
        raise ValueError(f"No Telegram user found for id {telegram_user_id}")
    if user.freeagent_account_id is None or user.freeagent_account_id != account_id:
        user.freeagent_account_id = account_id
        user.freeagent_access_token = access_token
        user.freeagent_refresh_token = refresh_token
        user.freeagent_token_expires_at = token_expires_at
        user.freeagent_company_name = company_name
        user.freeagent_permissions = permissions
        user.is_sandbox = False
        user.updated_at = _now()
        db.commit()
    return user


def get_active_freeagent_user(db: Session, telegram_user_id: str) -> Optional[ApplicationUser]:
    return db.scalar(
        select(ApplicationUser)
        .where(ApplicationUser.telegram_user_id == str(telegram_user_id))
        .where(ApplicationUser.freeagent_account_id.isnot(None))
    )


def upsert_freeagent_token(
    db: Session,
    account_id: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expires_at: Optional[datetime],
    company_name: Optional[str],
    permissions: Optional[str],
    is_sandbox: bool,
):
    token = db.scalar(select(FreeAgentToken).where(FreeAgentToken.account_id == account_id))
    if token is None:
        token = FreeAgentToken(
            account_id=account_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            company_name=company_name,
            permissions=permissions,
            is_sandbox=is_sandbox,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(token)
    else:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.token_expires_at = token_expires_at
        token.company_name = company_name
        token.permissions = permissions
        token.is_sandbox = is_sandbox
        token.updated_at = _now()
    db.commit()
    return token


def get_freeagent_token(db: Session, account_id: str) -> Optional[FreeAgentToken]:
    return db.scalar(select(FreeAgentToken).where(FreeAgentToken.account_id == account_id))
