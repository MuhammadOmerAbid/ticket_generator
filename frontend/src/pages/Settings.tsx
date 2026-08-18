import { FormEvent, useEffect, useState } from "react";
import { api, Settings } from "../api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [form, setForm] = useState({
    fathom_api_key: "",
    jira_base_url: "",
    jira_email: "",
    jira_api_token: "",
    jira_project_key: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jiraStatus, setJiraStatus] = useState<string | null>(null);

  useEffect(() => {
    api.getSettings().then((data) => {
      setSettings(data);
      setForm((prev) => ({
        ...prev,
        jira_base_url: data.jira_base_url || "",
        jira_email: data.jira_email || "",
        jira_project_key: data.jira_project_key || "",
      }));
    });
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const payload: Record<string, string> = {};
      if (form.fathom_api_key) payload.fathom_api_key = form.fathom_api_key;
      if (form.jira_base_url) payload.jira_base_url = form.jira_base_url;
      if (form.jira_email) payload.jira_email = form.jira_email;
      if (form.jira_api_token) payload.jira_api_token = form.jira_api_token;
      if (form.jira_project_key) payload.jira_project_key = form.jira_project_key;
      const updated = await api.updateSettings(payload);
      setSettings(updated);
      setMessage("Settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    }
  }

  async function validateJira() {
    setJiraStatus(null);
    const result = await api.validateJira();
    setJiraStatus(
      result.ok
        ? `Jira connected as ${result.display_name}`
        : result.message || "Jira validation failed",
    );
  }

  return (
    <div className="card grid">
      <h2>Settings</h2>
      <p>Connect Fathom and Jira. Keys are stored locally in the backend database.</p>
      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}
      <form className="grid" onSubmit={onSubmit}>
        <label>
          Fathom API key
          <input
            type="password"
            placeholder={settings?.fathom_api_key_set ? "Saved (enter to replace)" : "fathom_..."}
            value={form.fathom_api_key}
            onChange={(e) => setForm({ ...form, fathom_api_key: e.target.value })}
          />
        </label>
        <label>
          Jira base URL
          <input
            value={form.jira_base_url}
            onChange={(e) => setForm({ ...form, jira_base_url: e.target.value })}
            placeholder="https://your-domain.atlassian.net"
          />
        </label>
        <label>
          Jira email
          <input
            value={form.jira_email}
            onChange={(e) => setForm({ ...form, jira_email: e.target.value })}
          />
        </label>
        <label>
          Jira API token
          <input
            type="password"
            placeholder={settings?.jira_api_token_set ? "Saved (enter to replace)" : "token"}
            value={form.jira_api_token}
            onChange={(e) => setForm({ ...form, jira_api_token: e.target.value })}
          />
        </label>
        <label>
          Jira project key
          <input
            value={form.jira_project_key}
            onChange={(e) => setForm({ ...form, jira_project_key: e.target.value })}
            placeholder="PROJ"
          />
        </label>
        <div style={{ display: "flex", gap: 12 }}>
          <button type="submit">Save settings</button>
          <button type="button" className="secondary" onClick={validateJira}>
            Test Jira connection
          </button>
        </div>
      </form>
      {jiraStatus && <div className="success">{jiraStatus}</div>}
    </div>
  );
}
