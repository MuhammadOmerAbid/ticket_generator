import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Session, Task } from "../api";

export default function ReviewTasksPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newTask, setNewTask] = useState({
    title: "",
    description: "",
    priority: "Medium",
  });
  const navigate = useNavigate();

  async function loadSession(sessionId: string) {
    try {
      const data = await api.getSession(sessionId);
      setSession(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load session");
    }
  }

  useEffect(() => {
    const sessionId = sessionStorage.getItem("activeSessionId");
    if (!sessionId) {
      navigate("/meetings");
      return;
    }
    loadSession(sessionId);
  }, [navigate]);

  async function updateTask(task: Task, changes: Partial<Task>) {
    if (!session) return;
    const updated = await api.updateTask(task.id, changes);
    setSession({
      ...session,
      tasks: session.tasks.map((item) => (item.id === updated.id ? updated : item)),
    });
  }

  async function approve(taskId: string) {
    if (!session) return;
    const updated = await api.approveTask(taskId);
    setSession({
      ...session,
      tasks: session.tasks.map((item) => (item.id === updated.id ? updated : item)),
    });
  }

  async function reject(taskId: string) {
    if (!session) return;
    const updated = await api.rejectTask(taskId);
    setSession({
      ...session,
      tasks: session.tasks.map((item) => (item.id === updated.id ? updated : item)),
    });
  }

  async function addTask(event: FormEvent) {
    event.preventDefault();
    if (!session || !newTask.title.trim()) return;
    const created = await api.createTask(session.id, newTask);
    setSession({ ...session, tasks: [...session.tasks, created] });
    setNewTask({ title: "", description: "", priority: "Medium" });
  }

  return (
    <div className="grid">
      <div className="card grid">
        <h2>Review tasks</h2>
        <p>Refine each task before approving. Nothing is exported or sent to Jira until approved.</p>
        {error && <div className="error">{error}</div>}
        {!session && !error && <p>Loading tasks...</p>}
        {session && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Description</th>
                  <th>Priority</th>
                  <th>Due date</th>
                  <th>Source quote</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {session.tasks.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <input
                        value={task.title}
                        onChange={(e) => updateTask(task, { title: e.target.value })}
                      />
                    </td>
                    <td>
                      <textarea
                        rows={3}
                        value={task.description}
                        onChange={(e) => updateTask(task, { description: e.target.value })}
                      />
                    </td>
                    <td>
                      <select
                        value={task.priority}
                        onChange={(e) => updateTask(task, { priority: e.target.value })}
                      >
                        <option>Low</option>
                        <option>Medium</option>
                        <option>High</option>
                      </select>
                    </td>
                    <td>
                      <input
                        value={task.due_date || ""}
                        onChange={(e) => updateTask(task, { due_date: e.target.value || null })}
                        placeholder="YYYY-MM-DD"
                      />
                    </td>
                    <td>
                      <textarea
                        rows={3}
                        value={task.source_quote}
                        onChange={(e) => updateTask(task, { source_quote: e.target.value })}
                      />
                    </td>
                    <td>
                      <span className={`status ${task.status}`}>{task.status.replace(/_/g, " ")}</span>
                      {task.jira_key && <div>{task.jira_key}</div>}
                    </td>
                    <td>
                      <div style={{ display: "grid", gap: 8 }}>
                        <button type="button" onClick={() => approve(task.id)}>
                          Approve
                        </button>
                        <button type="button" className="danger" onClick={() => reject(task.id)}>
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card grid">
        <h3>Add manual task</h3>
        <form className="grid" onSubmit={addTask}>
          <label>
            Title
            <input
              value={newTask.title}
              onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
              required
            />
          </label>
          <label>
            Description
            <textarea
              value={newTask.description}
              onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            />
          </label>
          <label>
            Priority
            <select
              value={newTask.priority}
              onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
            >
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
            </select>
          </label>
          <button type="submit">Add task</button>
        </form>
      </div>
    </div>
  );
}
