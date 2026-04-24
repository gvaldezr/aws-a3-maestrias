import React, { useState } from "react";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";

export function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("id_token"));
  const [page, setPage] = useState<"dashboard" | "checkpoint">("dashboard");
  const [checkpointSubjectId, setCheckpointSubjectId] = useState("");

  if (!token) {
    return <LoginPage onLogin={(t) => { localStorage.setItem("id_token", t); setToken(t); }} />;
  }

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 1200, margin: "0 auto", padding: 20 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "2px solid #1565C0", paddingBottom: 10, marginBottom: 20 }}>
        <h1 style={{ color: "#1565C0", margin: 0 }}>Pipeline Academico — Anahuac Merida</h1>
        <button data-testid="logout-button" onClick={() => { localStorage.clear(); setToken(null); }}
          style={{ padding: "8px 16px", cursor: "pointer" }}>Cerrar Sesion</button>
      </header>
      <DashboardPage token={token} onCheckpoint={(id) => { setCheckpointSubjectId(id); setPage("checkpoint"); }} />
    </div>
  );
}
