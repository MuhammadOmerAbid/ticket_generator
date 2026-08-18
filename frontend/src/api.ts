export interface Settings {
  fathom_api_key_set: boolean;
  jira_base_url: string | null;
  jira_email: string | null;
  jira_api_token_set: boolean;
  jira_project_key: string | null;
}

export interface MeetingSummary {
  id: string;
  title: string;
  created_at: string | null;
  recording_id: string | null;
  duration_seconds: number | null;
}

export interface Participant {
  name: string;
  email: string | null;
  source: string;
}

export interface MeetingDetail {
  id: string;
  title: string;
  recording_id: string | null;
  participants: Participant[];
  action_items: string[];
}

export interface Task {
  id: string;
  session_id: string;
  title: string;
  description: string;
  priority: string;
  due_date: string | null;
  assignee: string;
  source_meeting_id: string;
  source_meeting_title: string;
  source_quote: string;
  confidence: string;
  status: string;
  jira_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  meeting_id: string;
  meeting_title: string;
  recording_id: string | null;
  user_identity: string;
  created_at: string;
  tasks: Task[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text() as T;
}

export const api = {
  getSettings: () => request<Settings>("/api/settings"),
  updateSettings: (payload: Record<string, string | undefined>) =>
    request<Settings>("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  listMeetings: () => request<MeetingSummary[]>("/api/meetings"),
  getMeeting: (meetingId: string, recordingId?: string | null) =>
    request<MeetingDetail>(
      `/api/meetings/${meetingId}${recordingId ? `?recording_id=${recordingId}` : ""}`,
    ),
  createSession: (payload: {
    meeting_id: string;
    meeting_title: string;
    recording_id?: string | null;
    user_identity: string;
  }) =>
    request<Session>("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getSession: (sessionId: string) => request<Session>(`/api/sessions/${sessionId}`),
  updateTask: (taskId: string, payload: Partial<Task>) =>
    request<Task>(`/api/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  approveTask: (taskId: string) =>
    request<Task>(`/api/tasks/${taskId}/approve`, { method: "POST" }),
  rejectTask: (taskId: string) =>
    request<Task>(`/api/tasks/${taskId}/reject`, { method: "POST" }),
  createTask: (
    sessionId: string,
    payload: {
      title: string;
      description?: string;
      priority?: string;
      due_date?: string | null;
      assignee?: string;
      source_quote?: string;
    },
  ) =>
    request<Task>(`/api/sessions/${sessionId}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  exportCsv: async (sessionId: string) => {
    const response = await fetch(`/api/sessions/${sessionId}/export-csv`);
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.text();
  },
  importCsv: async (sessionId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`/api/sessions/${sessionId}/import-csv`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json() as Promise<Session>;
  },
  validateJira: () =>
    request<{ ok: boolean; display_name?: string; message?: string }>("/api/jira/validate", {
      method: "POST",
    }),
  getIssueTypes: () => request<{ issue_types: string[] }>("/api/jira/issue-types"),
  syncJira: (sessionId: string, issueType: string) =>
    request<{ created: string[]; skipped: string[]; errors: string[] }>(
      `/api/sessions/${sessionId}/sync-jira`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issue_type: issueType }),
      },
    ),
};
