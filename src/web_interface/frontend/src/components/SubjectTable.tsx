/**
 * SubjectTable — Dashboard de estado del pipeline por asignatura.
 * Polling cada 30 segundos (BR-W05).
 */
import React, { useCallback, useEffect, useState } from "react";
import { DashboardData, getDashboard, PipelineStatus } from "../api/pipeline";

const STATE_LABELS: Record<string, string> = {
  INGESTED: "Ingresado",
  KNOWLEDGE_MATRIX_READY: "Investigación completa",
  DI_READY: "Diseño instruccional listo",
  CONTENT_READY: "Contenido generado",
  PENDING_APPROVAL: "⏳ Pendiente de aprobación",
  APPROVED: "Aprobado",
  REJECTED: "Rechazado",
  PUBLISHED: "✅ Publicado en Canvas",
  FAILED: "❌ Error",
  RESEARCH_ESCALATED: "⚠️ Escalado — Investigación",
  DI_ALIGNMENT_GAP: "⚠️ Gap de alineación",
  QA_FAILED: "⚠️ QA fallido",
  CONTENT_QA_FAILED: "⚠️ Contenido incompleto",
};

interface Props {
  onCheckpoint: (subjectId: string) => void;
}

export function SubjectTable({ onCheckpoint }: Props) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const result = await getDashboard();
      setData(result);
    } catch {
      // silently retry on next poll
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000); // BR-W05
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) return <p style={{padding:"1rem",color:"#718096"}}>Cargando asignaturas...</p>;
  if (!data) return <p style={{padding:"1rem",color:"#e53e3e"}}>Error al cargar el dashboard.</p>;

  return (
    <div>
      <div style={{display:"flex",gap:"1rem",marginBottom:"1rem",flexWrap:"wrap"}}>
        {[
          {label:"Total",value:data.total,bg:"#edf2f7",color:"#2d3748"},
          {label:"Pendientes",value:data.pending_approval_count,bg:"#fefcbf",color:"#744210"},
          {label:"Publicados",value:data.published_count,bg:"#c6f6d5",color:"#22543d"},
          {label:"Errores",value:data.failed_count,bg:"#fed7d7",color:"#742a2a"},
        ].map(s => (
          <div key={s.label} style={{background:s.bg,padding:"0.5rem 1rem",borderRadius:"8px",textAlign:"center",minWidth:"80px"}}>
            <div style={{fontSize:"1.3rem",fontWeight:700,color:s.color}}>{s.value}</div>
            <div style={{fontSize:"0.7rem",color:s.color,opacity:0.8}}>{s.label}</div>
          </div>
        ))}
      </div>

      <span data-testid="refresh-indicator" aria-live="polite" className="sr-only">
        Actualizando cada 30 segundos
      </span>

      <table aria-label="Estado del pipeline por asignatura">
        <thead>
          <tr>
            <th>Asignatura</th>
            <th>Programa</th>
            <th>Estado</th>
            <th>Actualizado</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          {[...data.subjects].sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || "")).map((subject: PipelineStatus) => (
            <tr key={subject.subject_id} data-testid={`subject-row-${subject.subject_id}`}>
              <td>{subject.subject_name}</td>
              <td>{subject.program_name}</td>
              <td>
                <span
                  data-testid={`status-badge-${subject.subject_id}`}
                  className={`status-badge status-${subject.current_state.toLowerCase()}`}
                >
                  {STATE_LABELS[subject.current_state] ?? subject.current_state}
                </span>
              </td>
              <td>{new Date(subject.updated_at).toLocaleString()}</td>
              <td>
                {subject.pending_approval && (
                  <button
                    data-testid={`action-button-${subject.subject_id}`}
                    onClick={() => onCheckpoint(subject.subject_id)}
                    aria-label={`Revisar ${subject.subject_name}`}
                    style={{background:"#dd6b20",color:"white",border:"none",padding:"0.3rem 0.75rem",borderRadius:"4px",cursor:"pointer",fontWeight:600,fontSize:"0.8rem",marginRight:"0.5rem"}}
                  >
                    📋 Revisar
                  </button>
                )}
                {subject.current_state === "PUBLISHED" && (
                  <button
                    onClick={() => onCheckpoint(subject.subject_id)}
                    style={{background:"#2b6cb0",color:"white",border:"none",padding:"0.3rem 0.75rem",borderRadius:"4px",cursor:"pointer",fontWeight:600,fontSize:"0.8rem",marginRight:"0.5rem"}}
                  >
                    👁️ Ver contenido
                  </button>
                )}
                {subject.canvas_course_url && (
                  <a
                    href={subject.canvas_course_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    data-testid={`canvas-link-${subject.subject_id}`}
                    style={{background:"#38a169",color:"white",padding:"0.3rem 0.75rem",borderRadius:"4px",fontSize:"0.8rem",fontWeight:600,textDecoration:"none",display:"inline-block"}}
                  >
                    🔗 Ver en Canvas
                  </a>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
