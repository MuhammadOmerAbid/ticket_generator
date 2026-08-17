import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Session } from "../api";

export default function ExportSyncPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [issueTypes, setIssueTypes] = useState<string[]>(["Task"]);
  const [issueType, setIssueType] = useState("Task");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const sessionId = sessionStorage.getItem("activeSessionId");
    if (!sessionId) {
      navigate("/meetings");
      return;
    }
    api.getSession(sessionId).then(setSession).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load session");
    });
    api.getIssueTypes().then((data) => {
      if (data.issue_types.length > 0) {
        setIssueTypes(data.issue_types);
        setIssueType(data.issue_types[0]);
      }
    });
  }, [navigate]);

  async function downloadCsv() {
    const sessionId = sessionStorage.getItem("activeSessionId");
    if (!sessionId) return;
    setError(null);
    try {
      const csv = await api.exportCsv(sessionId);
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `tasks-${sessionId}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      setMessage("CSV downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV export failed");
    }
  }

  async function uploadCsv(file: File | null) {
    const sessionId = sessionStorage.getItem("activeSessionId");
    if (!sessionId || !file) return;
    setError(null);
    try {
      const updated = await api.importCsv(sessionId, file);
      setSession(updated);
      setMessage("CSV imported and tasks updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV import failed");
    }
  }

  async function syncJira() {
    const sessionId = sessionStorage.getItem("activeSessionId");
    if (!sessionId) return;
    setError(null);
    setMessage(null);
    try {
      const result = await api.syncJira(sessionId, issueType);
      const refreshed = await api.getSession(sessionId);
      setSession(refreshed);
      setMessage(
        `Created ${result.created.length} Jira ticket(s). Skipped ${result.skipped.length}. Errors: ${result.errors.length}.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Jira sync failed");
    }
  }

  const approvedCount = session?.tasks.filter((task) => task.status === "approved").length || 0;

  return (
    <div className="card grid">
      <h2>Export & Jira sync</h2>
      <p>{approvedCount} approved task(s) ready for export or Jira sync.</p>
      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button onClick={downloadCsv}>Download approved tasks CSV</button>
        <label style={{ display: "inline-grid" }}>
          Upload updated CSV
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => uploadCsv(e.target.files?.[0] || null)}
          />
        </label>
      </div>

      <div className="grid">
        <label>
          Jira issue type
          <select value={issueType} onChange={(e) => setIssueType(e.target.value)}>
            {issueTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <button onClick={syncJira}>Push approved tasks to Jira</button>
      </div>
    </div>
  );
}
