from __future__ import annotations

import base64
from typing import Any

import httpx


class JiraError(Exception):
    pass


class JiraService:
    def __init__(self, base_url: str, email: str, api_token: str, project_key: str):
        if not all([base_url, email, api_token, project_key]):
            raise JiraError("Jira credentials are incomplete")
        self.base_url = base_url.rstrip("/")
        self.project_key = project_key
        token = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def validate(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/rest/api/3/myself", headers=self.headers)
            if response.status_code == 401:
                raise JiraError("Invalid Jira credentials")
            if response.status_code >= 400:
                raise JiraError(f"Jira validation failed: {response.text}")
            data = response.json()
            return {"display_name": data.get("displayName"), "account_id": data.get("accountId")}

    async def get_issue_types(self) -> list[str]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/rest/api/3/issue/createmeta",
                headers=self.headers,
                params={"projectKeys": self.project_key, "expand": "projects.issuetypes"},
            )
            if response.status_code >= 400:
                raise JiraError(f"Failed to fetch Jira metadata: {response.text}")
            data = response.json()
            issue_types: list[str] = []
            for project in data.get("projects", []):
                for issue_type in project.get("issuetypes", []):
                    name = issue_type.get("name")
                    if name:
                        issue_types.append(name)
            return issue_types or ["Task"]

    def _description_adf(self, text: str) -> dict[str, Any]:
        paragraphs = text.split("\n") if text else [""]
        content = []
        for paragraph in paragraphs:
            content.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": paragraph or " "}],
                }
            )
        return {"type": "doc", "version": 1, "content": content}

    async def create_issues(self, tasks: list[dict[str, Any]], issue_type: str = "Task") -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        batch_size = 50

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]
            issue_updates = []
            for task in batch:
                fields: dict[str, Any] = {
                    "project": {"key": self.project_key},
                    "summary": task["title"],
                    "description": self._description_adf(task.get("description") or ""),
                    "issuetype": {"name": issue_type},
                }
                if task.get("priority"):
                    fields["priority"] = {"name": task["priority"]}
                if task.get("due_date"):
                    fields["duedate"] = task["due_date"]
                issue_updates.append({"fields": fields})

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/rest/api/3/issue/bulk",
                    headers=self.headers,
                    json={"issueUpdates": issue_updates},
                )
                if response.status_code >= 400:
                    raise JiraError(f"Jira bulk create failed: {response.text}")

                data = response.json()
                for idx, issue in enumerate(data.get("issues") or []):
                    results.append(
                        {
                            "task_id": batch[idx]["id"],
                            "jira_key": issue.get("key"),
                            "success": True,
                        }
                    )
                for error in data.get("errors") or []:
                    results.append({"success": False, "error": str(error)})

        return results
