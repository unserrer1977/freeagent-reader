from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ApplicationUser(Base):
    __tablename__ = "application_users"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(String, unique=True, index=True, nullable=False)
    telegram_username = Column(String, nullable=True)
    freeagent_account_id = Column(String, unique=True, nullable=False)
    freeagent_access_token = Column(String, nullable=False)
    freeagent_refresh_token = Column(String, nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    freeagent_company_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<ApplicationUser(id={self.id}, company={self.freeagent_company_name})>"
