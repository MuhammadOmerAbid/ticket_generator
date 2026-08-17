from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Session as ReviewSession
from app.models import Task, TaskStatus
from app.schemas import (
    JiraSyncRequest,
    JiraSyncResponse,
    JiraValidateResponse,
    SessionCreate,
    SessionResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.csv_service import csv_to_task_updates, tasks_to_csv
from app.services.fathom import FathomError, FathomService
from app.services.jira import JiraError, JiraService
from app.services.task_extractor import TaskExtractor, TaskExtractorError
from app.utils.settings_store import resolve_fathom_api_key, resolve_jira_config

router = APIRouter(tags=["sessions"])


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse.model_validate(task)


def _session_to_response(session: ReviewSession) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        meeting_id=session.meeting_id,
        meeting_title=session.meeting_title,
        recording_id=session.recording_id,
        user_identity=session.user_identity,
        created_at=session.created_at,
        tasks=[_task_to_response(task) for task in session.tasks],
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    api_key = resolve_fathom_api_key(db)
    try:
        fathom = FathomService(api_key)
        detail = await fathom.get_meeting_detail(payload.meeting_id, payload.recording_id)
        transcript = detail.get("transcript_text") or ""
        extractor = TaskExtractor()
        extracted = await extractor.extract_tasks(
            transcript=transcript,
            user_identity=payload.user_identity,
            action_items=detail.get("action_items") or [],
            meeting_title=payload.meeting_title,
        )
    except (FathomError, TaskExtractorError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = ReviewSession(
        meeting_id=payload.meeting_id,
        meeting_title=payload.meeting_title,
        recording_id=payload.recording_id or detail.get("recording_id"),
        user_identity=payload.user_identity,
    )
    db.add(session)
    db.flush()

    for item in extracted:
        db.add(
            Task(
                session_id=session.id,
                title=item.title,
                description=item.description,
                priority=item.priority,
                due_date=item.due_date,
                assignee=item.assignee or payload.user_identity,
                source_meeting_id=payload.meeting_id,
                source_meeting_title=payload.meeting_title,
                source_quote=item.source_quote,
                confidence=item.confidence,
                status=TaskStatus.DRAFT.value,
            )
        )

    db.commit()
    db.refresh(session)
    return _session_to_response(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ReviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session)


@router.get("/sessions/{session_id}/tasks", response_model=list[TaskResponse])
def list_tasks(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ReviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [_task_to_response(task) for task in session.tasks]


@router.post("/sessions/{session_id}/tasks", response_model=TaskResponse)
def create_task(session_id: str, payload: TaskCreate, db: Session = Depends(get_db)):
    session = db.get(ReviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    task = Task(
        session_id=session.id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        assignee=payload.assignee or session.user_identity,
        source_meeting_id=session.meeting_id,
        source_meeting_title=session.meeting_title,
        source_quote=payload.source_quote,
        confidence="high",
        status=TaskStatus.DRAFT.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.post("/tasks/{task_id}/approve", response_model=TaskResponse)
def approve_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.APPROVED.value
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.post("/tasks/{task_id}/reject", response_model=TaskResponse)
def reject_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.REJECTED.value
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.get("/sessions/{session_id}/export-csv")
def export_csv(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ReviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    approved_tasks = [task for task in session.tasks if task.status == TaskStatus.APPROVED.value]
    content = tasks_to_csv(approved_tasks)
    return PlainTextResponse(
        content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="tasks-{session_id}.csv"'},
    )


@router.post("/sessions/{session_id}/import-csv", response_model=SessionResponse)
async def import_csv(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    session = db.get(ReviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    raw = (await file.read()).decode("utf-8-sig")
    updates = csv_to_task_updates(raw)
    task_map = {task.id: task for task in session.tasks}

    for update in updates:
        task = task_map.get(update["id"])
        if not task:
            continue
        task.title = update["title"]
        task.description = update["description"]
        task.priority = update["priority"]
        task.due_date = update["due_date"]
        task.assignee = update["assignee"]
        task.source_quote = update["source_quote"]
        task.status = update["status"]
        task.jira_key = update["jira_key"]

    db.commit()
    db.refresh(session)
    return _session_to_response(session)


@router.post("/jira/validate", response_model=JiraValidateResponse)
async def validate_jira(db: Session = Depends(get_db)):
    config = resolve_jira_config(db)
    try:
        service = JiraService(**config)
        result = await service.validate()
        return JiraValidateResponse(ok=True, display_name=result.get("display_name"))
    except JiraError as exc:
        return JiraValidateResponse(ok=False, message=str(exc))


@router.get("/jira/issue-types")
async def list_issue_types(db: Session = Depends(get_db)):
    config = resolve_jira_config(db)
    try:
        service = JiraService(**config)
        return {"issue_types": await service.get_issue_types()}
    except JiraError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/sync-jira", response_model=JiraSyncResponse)
async def sync_jira(session_id: str, payload: JiraSyncRequest, db: Session = Depends(get_db)):
    session = db.get(ReviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    config = resolve_jira_config(db)
    try:
        service = JiraService(**config)
    except JiraError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    to_create = [
        task
        for task in session.tasks
        if task.status == TaskStatus.APPROVED.value and not task.jira_key
    ]
    skipped = [task.id for task in session.tasks if task.jira_key]

    if not to_create:
        return JiraSyncResponse(created=[], skipped=skipped, errors=[])

    try:
        results = await service.create_issues(
            [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "due_date": task.due_date,
                }
                for task in to_create
            ],
            issue_type=payload.issue_type,
        )
    except JiraError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    created: list[str] = []
    errors: list[str] = []
    task_map = {task.id: task for task in to_create}

    for result in results:
        if result.get("success"):
            task = task_map.get(result["task_id"])
            if task:
                task.jira_key = result["jira_key"]
                task.status = TaskStatus.SYNCED_TO_JIRA.value
                created.append(result["jira_key"])
        else:
            errors.append(result.get("error") or "Unknown Jira error")

    db.commit()
    return JiraSyncResponse(created=created, skipped=skipped, errors=errors)
