from __future__ import annotations

from typing import Any

import httpx

FATHOM_BASE_URL = "https://api.fathom.ai/external/v1"


class FathomError(Exception):
    pass


class FathomService:
    def __init__(self, api_key: str):
        if not api_key:
            raise FathomError("Fathom API key is not configured")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{FATHOM_BASE_URL}{path}",
                headers=self.headers,
                params=params or {},
            )
            if response.status_code == 401:
                raise FathomError("Invalid Fathom API key")
            if response.status_code == 429:
                raise FathomError("Fathom rate limit exceeded. Try again shortly.")
            if response.status_code >= 400:
                raise FathomError(f"Fathom API error: {response.text}")
            return response.json()

    async def list_meetings(self, limit: int = 20) -> list[dict[str, Any]]:
        data = await self._get("/meetings", {"limit": limit})
        meetings = data.get("meetings") or data.get("items") or []
        normalized = []
        for meeting in meetings:
            recording_id = meeting.get("recording_id")
            if not recording_id and meeting.get("recordings"):
                recordings = meeting["recordings"]
                if recordings:
                    recording_id = recordings[0].get("id") or recordings[0].get("recording_id")
            normalized.append(
                {
                    "id": str(meeting.get("id") or meeting.get("meeting_id") or recording_id),
                    "title": meeting.get("title") or meeting.get("meeting_title") or "Untitled meeting",
                    "created_at": meeting.get("created_at") or meeting.get("scheduled_start_time"),
                    "recording_id": str(recording_id) if recording_id else None,
                    "duration_seconds": meeting.get("duration_seconds"),
                    "_raw": meeting,
                }
            )
        return normalized

    async def get_meeting_detail(self, meeting_id: str, recording_id: str | None = None) -> dict[str, Any]:
        meetings = await self.list_meetings(limit=50)
        match = next((m for m in meetings if m["id"] == meeting_id or m["recording_id"] == meeting_id), None)
        if not match:
            raise FathomError("Meeting not found")

        raw = match["_raw"]
        resolved_recording_id = recording_id or match.get("recording_id")
        participants = self._extract_participants(raw)
        action_items = self._extract_action_items(raw)

        transcript_text = ""
        if resolved_recording_id:
            transcript_text = await self.get_transcript_text(str(resolved_recording_id))
            speakers = self._extract_speakers_from_transcript(await self.get_transcript(str(resolved_recording_id)))
            for speaker in speakers:
                if speaker not in [p["name"] for p in participants]:
                    participants.append({"name": speaker, "email": None, "source": "transcript"})

        return {
            "id": match["id"],
            "title": match["title"],
            "recording_id": str(resolved_recording_id) if resolved_recording_id else None,
            "participants": participants,
            "action_items": action_items,
            "transcript_text": transcript_text,
        }

    async def get_transcript(self, recording_id: str) -> list[dict[str, Any]]:
        data = await self._get(f"/recordings/{recording_id}/transcript")
        if isinstance(data, dict):
            return data.get("transcript") or data.get("segments") or []
        return data if isinstance(data, list) else []

    async def get_transcript_text(self, recording_id: str) -> str:
        items = await self.get_transcript(recording_id)
        lines = []
        for item in items:
            speaker = ""
            if isinstance(item.get("speaker"), dict):
                speaker = item["speaker"].get("display_name") or item["speaker"].get("name") or "Speaker"
            elif item.get("speaker"):
                speaker = str(item["speaker"])
            text = item.get("text") or item.get("content") or ""
            if text:
                lines.append(f"{speaker}: {text}" if speaker else text)
        return "\n".join(lines)

    def _extract_participants(self, meeting: dict[str, Any]) -> list[dict[str, Any]]:
        participants: list[dict[str, Any]] = []
        seen: set[str] = set()

        for invitee in meeting.get("calendar_invitees") or []:
            name = invitee.get("name") or invitee.get("email") or "Unknown"
            if name not in seen:
                seen.add(name)
                participants.append({"name": name, "email": invitee.get("email"), "source": "calendar"})

        recorded_by = meeting.get("recorded_by") or {}
        name = recorded_by.get("name") or recorded_by.get("email")
        if name and name not in seen:
            seen.add(name)
            participants.append({"name": name, "email": recorded_by.get("email"), "source": "recorder"})

        for item in meeting.get("transcript") or []:
            speaker = item.get("speaker")
            if isinstance(speaker, dict):
                name = speaker.get("display_name") or speaker.get("name")
            else:
                name = str(speaker) if speaker else None
            if name and name not in seen:
                seen.add(name)
                participants.append({"name": name, "email": None, "source": "transcript"})

        return participants

    def _extract_speakers_from_transcript(self, transcript: list[dict[str, Any]]) -> list[str]:
        speakers: list[str] = []
        for item in transcript:
            speaker = item.get("speaker")
            if isinstance(speaker, dict):
                name = speaker.get("display_name") or speaker.get("name")
            else:
                name = str(speaker) if speaker else None
            if name and name not in speakers:
                speakers.append(name)
        return speakers

    def _extract_action_items(self, meeting: dict[str, Any]) -> list[str]:
        items: list[str] = []
        for action in meeting.get("action_items") or []:
            if isinstance(action, str):
                items.append(action)
            elif isinstance(action, dict):
                text = action.get("text") or action.get("description") or action.get("title")
                if text:
                    items.append(text)
        return items
