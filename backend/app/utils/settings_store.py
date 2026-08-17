from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AppSettings


def get_or_create_app_settings(db: Session) -> AppSettings:
    settings = db.get(AppSettings, 1)
    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def resolve_fathom_api_key(db: Session) -> str:
    env_settings = get_settings()
    db_settings = get_or_create_app_settings(db)
    return db_settings.fathom_api_key or env_settings.fathom_api_key


def resolve_jira_config(db: Session) -> dict[str, str]:
    env_settings = get_settings()
    db_settings = get_or_create_app_settings(db)
    return {
        "base_url": db_settings.jira_base_url or env_settings.jira_base_url,
        "email": db_settings.jira_email or env_settings.jira_email,
        "api_token": db_settings.jira_api_token or env_settings.jira_api_token,
        "project_key": db_settings.jira_project_key or env_settings.jira_project_key,
    }
