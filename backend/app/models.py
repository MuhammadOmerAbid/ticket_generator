import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    SYNCED_TO_JIRA = "synced_to_jira"


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    fathom_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    jira_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    jira_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jira_api_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    jira_project_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String(100))
    meeting_title: Mapped[str] = mapped_column(String(500))
    recording_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_identity: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[list["Task"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(50), default="Medium")
    due_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assignee: Mapped[str] = mapped_column(String(255), default="")
    source_meeting_id: Mapped[str] = mapped_column(String(100))
    source_meeting_title: Mapped[str] = mapped_column(String(500))
    source_quote: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(50), default="medium")
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.DRAFT.value)
    jira_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session: Mapped["Session"] = relationship(back_populates="tasks")
