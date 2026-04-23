/**
 * CheckpointPage — Validación humana antes de publicar en Canvas.
 * Solo visible para asignaturas en PENDING_APPROVAL (BR-W06).
 */
import React, { useEffect, useState } from "react";
import { getCheckpointSummary, submitDecision } from "../api/pipeline";

interface Props {
  subjectId: string;
  onDecisionComplete: () => void;
}

export function CheckpointPage({ subjectId, onDecisionComplete }: Props) {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [comments, setComments] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCheckpointSummary(subjectId)
      .then(setSummary)
      .catch(() => setError("Error al cargar el resumen del contenido"))
      .finally(() => setLoading(false));
  }, [subjectId]);

  const handleDecision = async (decision: "APPROVED" | "REJECTED") => {
    if (decision === "REJECTED" && !comments.trim()) {
      setError("Los comentarios son obligatorios al rechazar.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitDecision(subjectId, decision, comments || undefined);
      onDecisionComplete();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al enviar decisión");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p>Cargando resumen del contenido...</p>;
  if (!summary) return <p role="alert">{error ?? "No se pudo cargar el contenido."}</p>;

  const qa = summary.qa_report as Record<string, unknown> | undefined;
  const content = summary.content_preview as Record<string, unknown> | undefined;

  return (
    <div className="checkpoint-page">
      <h1>Validación de Contenido</h1>

      {/* QA Report Summary */}
      <section data-testid="qa-report-summary" aria-label="Resultado del QA Gate">
        <h2>Resultado del QA Gate</h2>
        <p>Estado: <strong>{qa?.status as string ?? "—"}</strong></p>
        {qa?.ra_coverage && (
          <p>Cobertura de RA: {(qa.ra_coverage as Record<string, number>).covered_ras} / {(qa.ra_coverage as Record<string, number>).total_ras}</p>
        )}
      </section>

      {/* Descriptive Card Preview */}
      <section data-testid="descriptive-card-view" aria-label="Vista previa de la Carta Descriptiva">
        <h2>Carta Descriptiva V1</h2>
        <p>{summary.descriptive_card_preview as string ?? "No disponible"}</p>
      </section>

      {/* Content Counts */}
      <section data-testid="content-counts-view" aria-label="Resumen de recursos generados">
        <h2>Recursos Generados</h2>
        {content && (
          <ul>
            <li>Lecturas ejecutivas: {content.readings_count as number ?? 0}</li>
            <li>Quizzes: {content.quizzes_count as number ?? 0}</li>
            <li>Casos de laboratorio: {content.cases_count as number ?? 0}</li>
            <li>Artefactos Maestría: {content.maestria_artifacts ? "✅ Presentes" : "N/A"}</li>
          </ul>
        )}
      </section>

      {/* Decision Panel */}
      <section className="decision-panel" aria-label="Panel de decisión">
        <h2>Decisión</h2>

        <label htmlFor="rejection-comments">
          Comentarios (obligatorios si rechaza):
        </label>
        <textarea
          id="rejection-comments"
          data-testid="rejection-comments-input"
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          rows={4}
          placeholder="Describa los cambios requeridos..."
          aria-required="false"
        />

        {error && <p role="alert" className="error-message">{error}</p>}

        <div className="decision-buttons">
          <button
            data-testid="approve-button"
            onClick={() => handleDecision("APPROVED")}
            disabled={submitting}
            aria-busy={submitting}
            className="btn-approve"
          >
            ✅ Aprobar y Publicar en Canvas
          </button>

          <button
            data-testid="reject-button"
            onClick={() => handleDecision("REJECTED")}
            disabled={submitting || !comments.trim()}
            aria-busy={submitting}
            className="btn-reject"
          >
            ❌ Rechazar con Comentarios
          </button>

          <button
            data-testid="edit-content-button"
            onClick={() => {/* open edit modal */}}
            disabled={submitting}
            className="btn-edit"
          >
            ✏️ Editar Manualmente
          </button>
        </div>
      </section>
    </div>
  );
}
