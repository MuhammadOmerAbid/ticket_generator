from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    fathom_api_key: str | None = None
    jira_base_url: str | None = None
    jira_email: str | None = None
    jira_api_token: str | None = None
    jira_project_key: str | None = None


class SettingsResponse(BaseModel):
    fathom_api_key_set: bool
    jira_base_url: str | None
    jira_email: str | None
    jira_api_token_set: bool
    jira_project_key: str | None


class MeetingSummary(BaseModel):
    id: str
    title: str
    created_at: str | None = None
    recording_id: str | None = None
    duration_seconds: int | None = None


class Participant(BaseModel):
    name: str
    email: str | None = None
    source: str


class MeetingDetail(BaseModel):
    id: str
    title: str
    recording_id: str | None = None
    participants: list[Participant]
    action_items: list[str] = Field(default_factory=list)


class SessionCreate(BaseModel):
    meeting_id: str
    meeting_title: str
    recording_id: str | None = None
    user_identity: str


class ExtractedTask(BaseModel):
    title: str
    description: str = ""
    priority: Literal["Low", "Medium", "High"] = "Medium"
    due_date: str | None = None
    assignee: str = ""
    source_quote: str = ""
    confidence: Literal["low", "medium", "high"] = "medium"


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "Medium"
    due_date: str | None = None
    assignee: str = ""
    source_quote: str = ""


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    due_date: str | None = None
    assignee: str | None = None
    source_quote: str | None = None
    status: str | None = None


class TaskResponse(BaseModel):
    id: str
    session_id: str
    title: str
    description: str
    priority: str
    due_date: str | None
    assignee: str
    source_meeting_id: str
    source_meeting_title: str
    source_quote: str
    confidence: str
    status: str
    jira_key: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    meeting_id: str
    meeting_title: str
    recording_id: str | None
    user_identity: str
    created_at: datetime
    tasks: list[TaskResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class JiraValidateResponse(BaseModel):
    ok: bool
    display_name: str | None = None
    message: str | None = None


class JiraSyncRequest(BaseModel):
    issue_type: str = "Task"


class JiraSyncResponse(BaseModel):
    created: list[str]
    skipped: list[str]
    errors: list[str]
