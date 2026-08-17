import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, MeetingSummary } from "../api";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .listMeetings()
      .then(setMeetings)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load meetings"))
      .finally(() => setLoading(false));
  }, []);

  function selectMeeting(meeting: MeetingSummary) {
    sessionStorage.setItem(
      "selectedMeeting",
      JSON.stringify({
        id: meeting.id,
        title: meeting.title,
        recording_id: meeting.recording_id,
      }),
    );
    navigate("/identity");
  }

  return (
    <div className="card grid">
      <h2>Select meeting</h2>
      {loading && <p>Loading meetings from Fathom...</p>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && meetings.length === 0 && <p>No meetings found.</p>}
      <div className="grid">
        {meetings.map((meeting) => (
          <div key={`${meeting.id}-${meeting.recording_id}`} className="card">
            <strong>{meeting.title}</strong>
            <div>{meeting.created_at || "Unknown date"}</div>
            <button style={{ marginTop: 12 }} onClick={() => selectMeeting(meeting)}>
              Use this meeting
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
