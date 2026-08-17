from __future__ import annotations

import json
import re
from typing import Any

from anthropic import Anthropic
from openai import OpenAI

import asyncio

from app.config import get_settings
from app.schemas import ExtractedTask


class TaskExtractorError(Exception):
    pass


class TaskExtractor:
    def __init__(self):
        self.settings = get_settings()

    async def extract_tasks(
        self,
        transcript: str,
        user_identity: str,
        action_items: list[str],
        meeting_title: str,
    ) -> list[ExtractedTask]:
        if not transcript.strip() and not action_items:
            raise TaskExtractorError("No transcript or action items available for extraction")

        prompt = self._build_prompt(transcript, user_identity, action_items, meeting_title)
        raw = await asyncio.to_thread(self._call_llm, prompt)
        return self._parse_tasks(raw, user_identity)

    def _build_prompt(
        self,
        transcript: str,
        user_identity: str,
        action_items: list[str],
        meeting_title: str,
    ) -> str:
        action_items_text = "\n".join(f"- {item}" for item in action_items) or "None provided"
        return f"""You are an assistant that extracts Jira-ready action items from meeting transcripts.

Meeting title: {meeting_title}
Selected user identity: {user_identity}

Fathom action item hints:
{action_items_text}

Meeting transcript:
{transcript[:120000]}

Extract ONLY tasks that are clearly assigned to or owned by "{user_identity}".
If ownership is ambiguous, omit the task rather than guessing.
Return JSON array with objects containing:
- title (string, concise)
- description (string)
- priority ("Low" | "Medium" | "High")
- due_date (ISO date string or null)
- assignee (string, use "{user_identity}" when applicable)
- source_quote (short transcript quote supporting the task)
- confidence ("low" | "medium" | "high")

Return ONLY valid JSON array, no markdown."""

    def _call_llm(self, prompt: str) -> str:
        provider = self.settings.llm_provider.lower()
        if provider == "anthropic":
            if not self.settings.anthropic_api_key:
                raise TaskExtractorError("Anthropic API key is not configured")
            client = Anthropic(api_key=self.settings.anthropic_api_key)
            response = client.messages.create(
                model=self.settings.llm_model or "claude-3-5-haiku-latest",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        if not self.settings.openai_api_key:
            raise TaskExtractorError("OpenAI API key is not configured")
        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(
            model=self.settings.llm_model or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or "[]"

    def _parse_tasks(self, raw: str, user_identity: str) -> list[ExtractedTask]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)

        try:
            data: list[dict[str, Any]] = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise TaskExtractorError(f"Failed to parse LLM response: {exc}") from exc

        tasks: list[ExtractedTask] = []
        for item in data:
            if not item.get("title"):
                continue
            tasks.append(
                ExtractedTask(
                    title=item["title"],
                    description=item.get("description") or "",
                    priority=item.get("priority") or "Medium",
                    due_date=item.get("due_date"),
                    assignee=item.get("assignee") or user_identity,
                    source_quote=item.get("source_quote") or "",
                    confidence=item.get("confidence") or "medium",
                )
            )
        return tasks
