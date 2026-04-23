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

  if (loading) return <p data-testid="refresh-indicator">Cargando...</p>;
  if (!data) return <p>Error al cargar el dashboard.</p>;

  return (
    <div>
      <div className="dashboard-summary">
        <span>Total: {data.total}</span>
        <span>Pendientes: {data.pending_approval_count}</span>
        <span>Publicados: {data.published_count}</span>
        <span>Errores: {data.failed_count}</span>
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
          {data.subjects.map((subject: PipelineStatus) => (
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
                  >
                    Revisar
                  </button>
                )}
                {subject.canvas_course_url && (
                  <a
                    href={subject.canvas_course_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    data-testid={`canvas-link-${subject.subject_id}`}
                  >
                    Ver en Canvas
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
