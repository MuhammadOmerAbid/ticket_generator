import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Participant } from "../api";

interface SelectedMeeting {
  id: string;
  title: string;
  recording_id: string | null;
}

export default function IdentityPage() {
  const [meeting, setMeeting] = useState<SelectedMeeting | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [userIdentity, setUserIdentity] = useState("");
  const [customIdentity, setCustomIdentity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const raw = sessionStorage.getItem("selectedMeeting");
    if (!raw) {
      navigate("/meetings");
      return;
    }
    const selected = JSON.parse(raw) as SelectedMeeting;
    setMeeting(selected);
    api
      .getMeeting(selected.id, selected.recording_id)
      .then((detail) => setParticipants(detail.participants))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load participants"));
  }, [navigate]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!meeting) return;
    const identity = userIdentity === "__custom__" ? customIdentity.trim() : userIdentity;
    if (!identity) {
      setError("Select or enter your identity in the meeting.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const session = await api.createSession({
        meeting_id: meeting.id,
        meeting_title: meeting.title,
        recording_id: meeting.recording_id,
        user_identity: identity,
      });
      sessionStorage.setItem("activeSessionId", session.id);
      navigate("/review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to extract tasks");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card grid">
      <h2>Who are you in this meeting?</h2>
      {meeting && <p>Meeting: {meeting.title}</p>}
      {error && <div className="error">{error}</div>}
      <form className="grid" onSubmit={onSubmit}>
        <label>
          Select participant
          <select value={userIdentity} onChange={(e) => setUserIdentity(e.target.value)} required>
            <option value="">Choose...</option>
            {participants.map((participant) => (
              <option key={`${participant.name}-${participant.source}`} value={participant.name}>
                {participant.name} ({participant.source})
              </option>
            ))}
            <option value="__custom__">Custom name...</option>
          </select>
        </label>
        {userIdentity === "__custom__" && (
          <label>
            Your name in the meeting
            <input value={customIdentity} onChange={(e) => setCustomIdentity(e.target.value)} />
          </label>
        )}
        <button type="submit" disabled={loading}>
          {loading ? "Extracting tasks..." : "Extract my tasks"}
        </button>
      </form>
    </div>
  );
}
