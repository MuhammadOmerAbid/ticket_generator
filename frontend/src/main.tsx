import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ExportSyncPage from "./pages/ExportSync";
import IdentityPage from "./pages/Identity";
import MeetingsPage from "./pages/Meetings";
import ReviewTasksPage from "./pages/ReviewTasks";
import SettingsPage from "./pages/Settings";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/settings" replace />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/meetings" element={<MeetingsPage />} />
          <Route path="/identity" element={<IdentityPage />} />
          <Route path="/review" element={<ReviewTasksPage />} />
          <Route path="/export" element={<ExportSyncPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
