from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MeetingDetail, MeetingSummary, Participant
from app.services.fathom import FathomError, FathomService
from app.utils.settings_store import resolve_fathom_api_key

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=list[MeetingSummary])
async def list_meetings(limit: int = Query(default=20, ge=1, le=50), db: Session = Depends(get_db)):
    api_key = resolve_fathom_api_key(db)
    try:
        service = FathomService(api_key)
        meetings = await service.list_meetings(limit=limit)
        return [
            MeetingSummary(
                id=m["id"],
                title=m["title"],
                created_at=m.get("created_at"),
                recording_id=m.get("recording_id"),
                duration_seconds=m.get("duration_seconds"),
            )
            for m in meetings
        ]
    except FathomError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(
    meeting_id: str,
    recording_id: str | None = None,
    db: Session = Depends(get_db),
):
    api_key = resolve_fathom_api_key(db)
    try:
        service = FathomService(api_key)
        detail = await service.get_meeting_detail(meeting_id, recording_id)
        return MeetingDetail(
            id=detail["id"],
            title=detail["title"],
            recording_id=detail.get("recording_id"),
            participants=[Participant(**p) for p in detail["participants"]],
            action_items=detail["action_items"],
        )
    except FathomError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
