from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SettingsResponse, SettingsUpdate
from app.utils.settings_store import get_or_create_app_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    from app.config import get_settings as get_env_settings

    env = get_env_settings()
    settings = get_or_create_app_settings(db)
    return SettingsResponse(
        fathom_api_key_set=bool(settings.fathom_api_key or env.fathom_api_key),
        jira_base_url=settings.jira_base_url or env.jira_base_url or None,
        jira_email=settings.jira_email or env.jira_email or None,
        jira_api_token_set=bool(settings.jira_api_token or env.jira_api_token),
        jira_project_key=settings.jira_project_key or env.jira_project_key or None,
    )


@router.put("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    settings = get_or_create_app_settings(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return SettingsResponse(
        fathom_api_key_set=bool(settings.fathom_api_key),
        jira_base_url=settings.jira_base_url,
        jira_email=settings.jira_email,
        jira_api_token_set=bool(settings.jira_api_token),
        jira_project_key=settings.jira_project_key,
    )
