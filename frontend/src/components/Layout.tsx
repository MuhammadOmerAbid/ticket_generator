import { NavLink, Outlet } from "react-router-dom";

const steps = [
  { to: "/settings", label: "1. Settings" },
  { to: "/meetings", label: "2. Meeting" },
  { to: "/identity", label: "3. Identity" },
  { to: "/review", label: "4. Review" },
  { to: "/export", label: "5. Export & Jira" },
];

export default function Layout() {
  return (
    <div className="app-shell">
      <h1>Ticket Generator</h1>
      <p>Meeting transcript to reviewed tasks, CSV, and Jira tickets.</p>
      <nav className="nav">
        {steps.map((step) => (
          <NavLink
            key={step.to}
            to={step.to}
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            {step.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
