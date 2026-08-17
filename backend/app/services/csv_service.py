from __future__ import annotations

import csv
import io
from typing import Any

from app.models import Task


CSV_FIELDS = [
    "id",
    "title",
    "description",
    "priority",
    "due_date",
    "assignee",
    "source_meeting_id",
    "source_meeting_title",
    "source_quote",
    "status",
    "jira_key",
]


def tasks_to_csv(tasks: list[Task]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for task in tasks:
        writer.writerow(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "due_date": task.due_date or "",
                "assignee": task.assignee,
                "source_meeting_id": task.source_meeting_id,
                "source_meeting_title": task.source_meeting_title,
                "source_quote": task.source_quote,
                "status": task.status,
                "jira_key": task.jira_key or "",
            }
        )
    return output.getvalue()


def csv_to_task_updates(csv_content: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(csv_content))
    updates: list[dict[str, Any]] = []
    for row in reader:
        if not row.get("id"):
            continue
        updates.append(
            {
                "id": row["id"],
                "title": row.get("title") or "",
                "description": row.get("description") or "",
                "priority": row.get("priority") or "Medium",
                "due_date": row.get("due_date") or None,
                "assignee": row.get("assignee") or "",
                "source_quote": row.get("source_quote") or "",
                "status": row.get("status") or "draft",
                "jira_key": row.get("jira_key") or None,
            }
        )
    return updates
