import React, { useCallback, useEffect, useState } from "react";

const LABELS: Record<string, string> = {
  INGESTED: "Ingresado", KNOWLEDGE_MATRIX_READY: "Investigacion completa",
  DI_READY: "Diseno instruccional listo", CONTENT_READY: "Contenido generado",
  PENDING_APPROVAL: "Pendiente de aprobacion", APPROVED: "Aprobado",
  REJECTED: "Rechazado", PUBLISHED: "Publicado en Canvas",
  FAILED: "Error", RESEARCH_ESCALATED: "Escalado",
};
const COLORS: Record<string, string> = {
  PUBLISHED: "#4CAF50", APPROVED: "#8BC34A", PENDING_APPROVAL: "#FF9800",
  FAILED: "#f44336", REJECTED: "#f44336", INGESTED: "#2196F3",
};

interface Subject { subject_id: string; subject_name: string; program_name: string; current_state: string; updated_at: string; pending_approval: boolean; }
interface Props { apiUrl: string; checkpointApiUrl: string; headers: Record<string, string>; onCheckpoint: (id: string) => void; }

export function SubjectTable({ apiUrl, checkpointApiUrl, headers, onCheckpoint }: Props) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState({ total: 0, pending: 0, published: 0, failed: 0 });
  const [deciding, setDeciding] = useState<string | null>(null);
  const [comments, setComments] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const r = await fetch(`${apiUrl}/api/subjects`, { headers });
      if (r.ok) {
        const data = await r.json();
        setSubjects(data.subjects || []);
        setCounts({ total: data.total, pending: data.pending_approval_count, published: data.published_count, failed: data.failed_count });
      }
    } catch {} finally { setLoading(false); }
  }, [apiUrl, headers]);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 30000); return () => clearInterval(i); }, [fetchData]);

  const handleDecision = async (subjectId: string, decision: string) => {
    try {
      await fetch(`${checkpointApiUrl}/subjects/${subjectId}/decision`, {
        method: "POST", headers,
        body: JSON.stringify({ decision, comments: comments || undefined }),
      });
      setDeciding(null); setComments("");
      fetchData();
    } catch (err: any) { alert(`Error: ${err.message}`); }
  };

  if (loading) return <p data-testid="refresh-indicator">Cargando...</p>;

  return (
    <div>
      <h2>Estado del Pipeline</h2>
      <div style={{ display: "flex", gap: 20, marginBottom: 20 }}>
        <span style={{ padding: "8px 16px", background: "#e3f2fd", borderRadius: 4 }}>Total: {counts.total}</span>
        <span style={{ padding: "8px 16px", background: "#fff3e0", borderRadius: 4 }}>Pendientes: {counts.pending}</span>
        <span style={{ padding: "8px 16px", background: "#e8f5e9", borderRadius: 4 }}>Publicados: {counts.published}</span>
        <span style={{ padding: "8px 16px", background: "#ffebee", borderRadius: 4 }}>Errores: {counts.failed}</span>
      </div>
      <span data-testid="refresh-indicator" style={{ fontSize: 12, color: "#999" }}>Actualiza cada 30s</span>
      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 10 }}>
        <thead>
          <tr style={{ background: "#f5f5f5", textAlign: "left" }}>
            <th style={{ padding: 10 }}>Asignatura</th><th style={{ padding: 10 }}>Programa</th>
            <th style={{ padding: 10 }}>Estado</th><th style={{ padding: 10 }}>Actualizado</th><th style={{ padding: 10 }}>Accion</th>
          </tr>
        </thead>
        <tbody>
          {subjects.map((s) => (
            <tr key={s.subject_id} data-testid={`subject-row-${s.subject_id}`} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ padding: 10 }}>{s.subject_name}</td>
              <td style={{ padding: 10 }}>{s.program_name}</td>
              <td style={{ padding: 10 }}>
                <span data-testid={`status-badge-${s.subject_id}`}
                  style={{ padding: "4px 10px", borderRadius: 12, fontSize: 13, color: "white", background: COLORS[s.current_state] || "#9e9e9e" }}>
                  {LABELS[s.current_state] || s.current_state}
                </span>
              </td>
              <td style={{ padding: 10, fontSize: 13 }}>{new Date(s.updated_at).toLocaleString()}</td>
              <td style={{ padding: 10 }}>
                {s.pending_approval && deciding !== s.subject_id && (
                  <button data-testid={`action-button-${s.subject_id}`} onClick={() => setDeciding(s.subject_id)}
                    style={{ padding: "6px 14px", background: "#FF9800", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>
                    Revisar
                  </button>
                )}
                {deciding === s.subject_id && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <button data-testid="approve-button" onClick={() => handleDecision(s.subject_id, "APPROVED")}
                      style={{ padding: "6px 12px", background: "#4CAF50", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>
                      Aprobar
                    </button>
                    <input data-testid="rejection-comments-input" placeholder="Comentarios (obligatorio para rechazar)"
                      value={comments} onChange={(e) => setComments(e.target.value)}
                      style={{ padding: 6, border: "1px solid #ccc", borderRadius: 4 }} />
                    <button data-testid="reject-button" onClick={() => handleDecision(s.subject_id, "REJECTED")} disabled={!comments}
                      style={{ padding: "6px 12px", background: "#f44336", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>
                      Rechazar
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
          {subjects.length === 0 && <tr><td colSpan={5} style={{ padding: 20, textAlign: "center", color: "#999" }}>No hay asignaturas en proceso</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
