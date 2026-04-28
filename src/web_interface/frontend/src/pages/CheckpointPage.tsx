/**
 * CheckpointPage — Validación humana con previsualización completa del contenido.
 * Solo visible para asignaturas en PENDING_APPROVAL (BR-W06).
 */
import React, { useEffect, useState } from "react";
import { getCheckpointSummary, submitDecision } from "../api/pipeline";

interface Props {
  subjectId: string;
  onDecisionComplete: () => void;
}

type Tab = "overview" | "objectives" | "readings" | "quizzes" | "forums" | "papers" | "maestria" | "masterclass" | "challenge" | "canvas";

export function CheckpointPage({ subjectId, onDecisionComplete }: Props) {
  const [summary, setSummary] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [comments, setComments] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

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

  if (loading) return <p style={{padding:"2rem",textAlign:"center"}}>⏳ Cargando contenido para revisión...</p>;
  if (!summary) return <p role="alert" style={{padding:"2rem",color:"#c00"}}>{error ?? "No se pudo cargar el contenido."}</p>;

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: "overview", label: "📋 Resumen" },
    { key: "objectives", label: "🎯 Objetivos", count: summary.objectives?.length },
    { key: "readings", label: "📖 Lecturas", count: summary.readings?.length },
    { key: "quizzes", label: "❓ Quizzes", count: summary.quizzes?.length },
    { key: "forums", label: "💬 Foros", count: summary.forums?.length },
    { key: "papers", label: "📚 Papers", count: summary.papers?.length },
    { key: "maestria", label: "🎓 Maestría" },
    { key: "masterclass", label: "🎬 Masterclass" },
    { key: "challenge", label: "🏆 Reto Agéntico" },
    { key: "canvas", label: "👁️ Preview Canvas", count: summary.canvas_preview?.total_pages },
  ];

  return (
    <div style={{maxWidth:"960px",margin:"0 auto",padding:"1rem",fontFamily:"system-ui,sans-serif"}}>
      {/* Header */}
      <div style={{background:"#1a365d",color:"white",padding:"1.5rem",borderRadius:"8px",marginBottom:"1rem"}}>
        <h1 style={{margin:0,fontSize:"1.4rem"}}>Validación de Contenido</h1>
        <p style={{margin:"0.5rem 0 0",opacity:0.9}}>{summary.subject_name} — {summary.program_name}</p>
        <p style={{margin:"0.25rem 0 0",opacity:0.7,fontSize:"0.85rem"}}>Tipo: {summary.subject_type} | Estado: {summary.current_state}</p>
      </div>

      {/* Tabs */}
      <div style={{display:"flex",gap:"0.25rem",borderBottom:"2px solid #e2e8f0",marginBottom:"1rem",flexWrap:"wrap"}}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            style={{
              padding:"0.6rem 1rem",border:"none",cursor:"pointer",fontSize:"0.85rem",
              borderBottom: activeTab === t.key ? "3px solid #2b6cb0" : "3px solid transparent",
              background: activeTab === t.key ? "#ebf4ff" : "transparent",
              fontWeight: activeTab === t.key ? 600 : 400,
              borderRadius:"4px 4px 0 0",
            }}>
            {t.label}{t.count != null ? ` (${t.count})` : ""}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{minHeight:"300px",marginBottom:"1.5rem"}}>
        {activeTab === "overview" && <OverviewTab summary={summary} />}
        {activeTab === "objectives" && <ObjectivesTab objectives={summary.objectives || []} card={summary.descriptive_card} />}
        {activeTab === "readings" && <ReadingsTab readings={summary.readings || []} />}
        {activeTab === "quizzes" && <QuizzesTab quizzes={summary.quizzes || []} />}
        {activeTab === "forums" && <ForumsTab forums={summary.forums || []} />}
        {activeTab === "papers" && <PapersTab papers={summary.papers || []} />}
        {activeTab === "maestria" && <MaestriaTab artifacts={summary.maestria_artifacts} />}
        {activeTab === "masterclass" && <MasterclassTab script={summary.masterclass_script} />}
        {activeTab === "challenge" && <ChallengeTab challenge={summary.agentic_challenge} />}
        {activeTab === "canvas" && <CanvasPreviewTab preview={summary.canvas_preview} />}
      </div>

      {/* Decision Panel — only for PENDING_APPROVAL */}
      {summary.current_state === "PUBLISHED" ? (
        <div style={{background:"#c6f6d5",border:"1px solid #9ae6b4",borderRadius:"8px",padding:"1.5rem",textAlign:"center"}}>
          <p style={{margin:0,fontSize:"1.1rem",color:"#22543d",fontWeight:600}}>✅ Este curso ya fue publicado en Canvas LMS</p>
          {summary.canvas_course_url && (
            <a href={summary.canvas_course_url} target="_blank" rel="noopener noreferrer"
              style={{display:"inline-block",marginTop:"0.75rem",background:"#38a169",color:"white",padding:"0.5rem 1.5rem",borderRadius:"6px",textDecoration:"none",fontWeight:600}}>
              🔗 Ver curso en Canvas
            </a>
          )}
        </div>
      ) : summary.current_state === "APPROVED" ? (
        <div style={{background:"#bee3f8",border:"1px solid #90cdf4",borderRadius:"8px",padding:"1.5rem",textAlign:"center"}}>
          <p style={{margin:0,fontSize:"1.1rem",color:"#2a4365",fontWeight:600}}>⏳ Curso aprobado, publicación en proceso...</p>
        </div>
      ) : (
      <div style={{background:"#f7fafc",border:"1px solid #e2e8f0",borderRadius:"8px",padding:"1.5rem"}}>
        <h2 style={{margin:"0 0 1rem",fontSize:"1.1rem"}}>Decisión</h2>
        <textarea
          value={comments} onChange={(e) => setComments(e.target.value)}
          rows={3} placeholder="Comentarios (obligatorios si rechaza)..."
          style={{width:"100%",padding:"0.5rem",borderRadius:"4px",border:"1px solid #cbd5e0",marginBottom:"0.75rem",boxSizing:"border-box"}}
        />
        {error && <p style={{color:"#c00",margin:"0 0 0.75rem"}}>{error}</p>}
        <div style={{display:"flex",gap:"0.75rem",flexWrap:"wrap"}}>
          <button onClick={() => handleDecision("APPROVED")} disabled={submitting}
            style={{padding:"0.7rem 1.5rem",background:"#38a169",color:"white",border:"none",borderRadius:"6px",cursor:"pointer",fontWeight:600,fontSize:"0.95rem"}}>
            ✅ Aprobar y Publicar en Canvas
          </button>
          <button onClick={() => handleDecision("REJECTED")} disabled={submitting || !comments.trim()}
            style={{padding:"0.7rem 1.5rem",background:"#e53e3e",color:"white",border:"none",borderRadius:"6px",cursor:"pointer",fontWeight:600,fontSize:"0.95rem",opacity:comments.trim()?"1":"0.5"}}>
            ❌ Rechazar con Comentarios
          </button>
        </div>
      </div>
      )}
    </div>
  );
}


/* ── Tab Components ─────────────────────────────────────────── */

function OverviewTab({ summary }: { summary: Record<string, any> }) {
  const cp = summary.content_preview || {};
  const qa = summary.qa_report || {};
  const raCov = qa.ra_coverage || {};
  const bloomAl = qa.bloom_alignment || {};
  return (
    <div>
      <h3 style={{marginTop:0}}>QA Gate</h3>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:"0.75rem",marginBottom:"1.5rem"}}>
        <StatCard label="Estado QA" value={qa.overall_status || "—"} ok={qa.overall_status === "PASS"} />
        <StatCard label="Cobertura RA" value={`${raCov.covered_ras ?? 0}/${raCov.total_ras ?? 0}`} ok={raCov.gaps?.length === 0} />
        <StatCard label="Alineación Bloom" value={`${bloomAl.aligned_objectives ?? 0}/${bloomAl.total_objectives ?? 0}`} ok={bloomAl.gaps?.length === 0} />
        <StatCard label="Artefactos Maestría" value={qa.maestria_artifacts_present ? "✅" : "❌"} ok={qa.maestria_artifacts_present} />
      </div>

      <h3>Contenido Generado</h3>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(140px,1fr))",gap:"0.75rem",marginBottom:"1.5rem"}}>
        <StatCard label="Lecturas" value={cp.readings_count ?? 0} />
        <StatCard label="Quizzes" value={cp.quizzes_count ?? 0} />
        <StatCard label="Preguntas" value={cp.total_questions ?? 0} />
        <StatCard label="Papers" value={cp.papers_count ?? 0} />
        <StatCard label="Casos" value={cp.cases_count ?? 0} />
        <StatCard label="Masterclass" value={cp.has_masterclass ? "✅" : "—"} ok={cp.has_masterclass} />
        <StatCard label="Reto" value={cp.has_agentic_challenge ? "✅" : "—"} ok={cp.has_agentic_challenge} />
        <StatCard label="Foros" value={cp.forums_count ?? 0} />
      </div>

      <h3>Carta Descriptiva</h3>
      <p style={{background:"#fff",padding:"1rem",borderRadius:"6px",border:"1px solid #e2e8f0",lineHeight:1.6}}>
        <strong>Objetivo General:</strong> {summary.descriptive_card?.general_objective || "No disponible"}
      </p>

      {summary.weekly_map?.length > 0 && (
        <>
          <h3>Mapa Semanal</h3>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:"0.85rem"}}>
            <thead><tr style={{background:"#edf2f7"}}>
              <th style={thStyle}>Sem</th><th style={thStyle}>Tema</th><th style={thStyle}>Bloom</th>
            </tr></thead>
            <tbody>
              {summary.weekly_map.map((w: any) => (
                <tr key={w.week}><td style={tdStyle}>{w.week}</td><td style={tdStyle}>{w.theme}</td><td style={tdStyle}><BloomBadge level={w.bloom_level} /></td></tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

function ObjectivesTab({ objectives, card }: { objectives: any[]; card: any }) {
  return (
    <div>
      <h3 style={{marginTop:0}}>Objetivos de Aprendizaje ({objectives.length})</h3>
      {objectives.map((o: any) => (
        <div key={o.id} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"1rem",marginBottom:"0.75rem"}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"0.5rem"}}>
            <strong>{o.id}</strong>
            <BloomBadge level={o.bloom_level} />
          </div>
          <p style={{margin:"0 0 0.5rem",lineHeight:1.5}}>{o.description}</p>
          <div style={{fontSize:"0.8rem",color:"#718096"}}>
            Competencias: {o.competencies?.join(", ")} | RAs: {o.ras?.join(", ")}
          </div>
        </div>
      ))}

      {card?.specific_objectives?.length > 0 && (
        <>
          <h3>Objetivos Específicos (Carta Descriptiva)</h3>
          <ol style={{lineHeight:1.8}}>
            {card.specific_objectives.map((so: any, i: number) => (
              <li key={i}>{typeof so === "string" ? so : so.text || JSON.stringify(so)}</li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}

function ReadingsTab({ readings }: { readings: any[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  return (
    <div>
      <h3 style={{marginTop:0}}>Lecturas Ejecutivas ({readings.length})</h3>
      {readings.map((r: any, i: number) => (
        <div key={i} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",marginBottom:"0.75rem",overflow:"hidden"}}>
          <div onClick={() => setExpanded(expanded === i ? null : i)}
            style={{padding:"0.75rem 1rem",cursor:"pointer",display:"flex",justifyContent:"space-between",alignItems:"center",background:expanded===i?"#ebf4ff":"transparent"}}>
            <span><strong>Semana {r.week}:</strong> {r.title}</span>
            <span style={{fontSize:"0.8rem"}}>{expanded === i ? "▲" : "▼"}</span>
          </div>
          {expanded === i && (
            <div style={{padding:"1rem",borderTop:"1px solid #e2e8f0",whiteSpace:"pre-wrap",fontSize:"0.85rem",lineHeight:1.6,background:"#fafafa"}}>
              {r.content_md || "Sin contenido"}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function QuizzesTab({ quizzes }: { quizzes: any[] }) {
  return (
    <div>
      <h3 style={{marginTop:0}}>Quizzes ({quizzes.length})</h3>
      {quizzes.map((q: any) => (
        <div key={q.ra_id} style={{marginBottom:"1.5rem"}}>
          <h4 style={{background:"#edf2f7",padding:"0.5rem 0.75rem",borderRadius:"4px",margin:"0 0 0.75rem"}}>
            {q.ra_id}: {q.ra_description || ""} ({q.questions?.length || 0} preguntas)
          </h4>
          {q.questions?.map((qq: any, qi: number) => (
            <div key={qi} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"1rem",marginBottom:"0.5rem"}}>
              <p style={{fontWeight:600,margin:"0 0 0.5rem"}}>P{qi+1}: {qq.question}</p>
              <div style={{paddingLeft:"1rem"}}>
                {qq.options?.map((opt: string, oi: number) => (
                  <p key={oi} style={{margin:"0.25rem 0",color: oi === qq.correct_answer ? "#38a169" : "#4a5568",fontWeight: oi === qq.correct_answer ? 600 : 400}}>
                    {String.fromCharCode(65+oi)}) {opt} {oi === qq.correct_answer ? " ✓" : ""}
                  </p>
                ))}
              </div>
              {qq.feedback && <p style={{fontSize:"0.8rem",color:"#718096",marginTop:"0.5rem",fontStyle:"italic"}}>💡 {qq.feedback}</p>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function PapersTab({ papers }: { papers: any[] }) {
  return (
    <div>
      <h3 style={{marginTop:0}}>Papers Académicos ({papers.length})</h3>
      <table style={{width:"100%",borderCollapse:"collapse",fontSize:"0.85rem"}}>
        <thead><tr style={{background:"#edf2f7"}}>
          <th style={thStyle}>#</th><th style={thStyle}>Título</th><th style={thStyle}>Año</th><th style={thStyle}>Revista</th><th style={thStyle}>Hallazgo</th>
        </tr></thead>
        <tbody>
          {papers.map((p: any, i: number) => (
            <tr key={i}><td style={tdStyle}>{i+1}</td><td style={tdStyle}>{p.title}</td><td style={tdStyle}>{p.year}</td><td style={{...tdStyle,maxWidth:"150px",overflow:"hidden",textOverflow:"ellipsis"}}>{p.journal}</td><td style={{...tdStyle,fontSize:"0.8rem",color:"#718096"}}>{p.key_finding}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MaestriaTab({ artifacts }: { artifacts: any }) {
  if (!artifacts) return <p>No hay artefactos de Maestría.</p>;
  return (
    <div>
      <h3 style={{marginTop:0}}>Artefactos Maestría</h3>

      <Section title="📊 Dashboard de Evidencia">
        {artifacts.evidence_dashboard ? (
          <div style={{overflow:"auto",fontSize:"0.8rem"}} dangerouslySetInnerHTML={{__html: artifacts.evidence_dashboard.replace(/\n/g,"<br/>").replace(/\|/g," | ")}} />
        ) : <p>No disponible</p>}
      </Section>

      <Section title="🗺️ Mapa de Ruta Crítica">
        <pre style={{whiteSpace:"pre-wrap",fontSize:"0.8rem",background:"#fafafa",padding:"1rem",borderRadius:"4px"}}>{artifacts.critical_path_map || "No disponible"}</pre>
      </Section>

      <Section title="💼 Casos Ejecutivos">
        {artifacts.cases?.map((c: any, i: number) => (
          <div key={i} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"1rem",marginBottom:"0.75rem"}}>
            <h4 style={{margin:"0 0 0.5rem"}}>{c.title}</h4>
            <p style={{margin:"0 0 0.5rem",lineHeight:1.5}}><strong>Contexto:</strong> {c.context}</p>
            {c.questions?.length > 0 && (
              <div><strong>Preguntas:</strong><ol style={{margin:"0.25rem 0"}}>{c.questions.map((q: string, qi: number) => <li key={qi}>{q}</li>)}</ol></div>
            )}
            {c.rubric && <p style={{fontSize:"0.8rem",color:"#718096"}}>Rúbrica: {c.rubric.criteria?.join(" | ")}</p>}
          </div>
        )) || <p>No disponible</p>}
      </Section>

      <Section title="👨‍🏫 Guía del Facilitador">
        {artifacts.facilitator_sessions?.map((s: any, i: number) => (
          <div key={i} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"1rem",marginBottom:"0.75rem"}}>
            <h4 style={{margin:"0 0 0.5rem"}}>Semana {s.week}: {s.objective} ({s.duration_minutes} min)</h4>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:"0.8rem"}}>
              <tbody>
                {s.sequence?.map((step: any, si: number) => (
                  <tr key={si}><td style={{padding:"0.2rem 0.5rem",fontWeight:600,width:"80px"}}>{step.time}</td><td style={{padding:"0.2rem 0.5rem"}}>{step.activity}</td></tr>
                ))}
              </tbody>
            </table>
            {s.trigger_questions?.length > 0 && (
              <div style={{marginTop:"0.5rem",fontSize:"0.8rem",color:"#4a5568"}}>
                <strong>Preguntas detonadoras:</strong>
                <ul style={{margin:"0.25rem 0"}}>{s.trigger_questions.map((tq: string, ti: number) => <li key={ti}>{tq}</li>)}</ul>
              </div>
            )}
          </div>
        )) || <p>No disponible</p>}
      </Section>
    </div>
  );
}

function ForumsTab({ forums }: { forums: any[] }) {
  if (!forums || forums.length === 0) return <p style={{color:"#718096",padding:"1rem"}}>Los foros se generarán en la próxima ejecución del pipeline.</p>;
  return (
    <div>
      <h3 style={{marginTop:0}}>💬 Foros de Aprendizaje ({forums.length})</h3>
      {forums.map((f: any, i: number) => (
        <div key={i} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",marginBottom:"1rem",overflow:"hidden"}}>
          <div style={{background:"#2d3748",color:"white",padding:"0.5rem 1rem",fontSize:"0.85rem"}}>
            <strong>Semana {f.week}:</strong> {f.title}
          </div>
          <div style={{padding:"1rem"}}>
            {f.case && (
              <div style={{marginBottom:"1rem"}}>
                <h4 style={{margin:"0 0 0.5rem",color:"#2b6cb0"}}>{f.case.title || "Caso de Negocio"}</h4>
                <p style={{lineHeight:1.7,margin:0}}>{f.case.description}</p>
              </div>
            )}
            {f.questions && (
              <div style={{marginBottom:"1rem"}}>
                <h4 style={{margin:"0 0 0.5rem"}}>Preguntas de Discusión</h4>
                <ol style={{margin:0,paddingLeft:"1.5rem",lineHeight:1.8}}>
                  {f.questions.map((q: string, qi: number) => <li key={qi}>{q}</li>)}
                </ol>
              </div>
            )}
            {f.rubric && (
              <div>
                <h4 style={{margin:"0 0 0.5rem"}}>Rúbrica de Evaluación</h4>
                <div style={{overflowX:"auto"}}>
                  <table style={{width:"100%",borderCollapse:"collapse",fontSize:"0.8rem",minWidth:"500px"}}>
                    <thead>
                      <tr style={{background:"#edf2f7"}}>
                        <th style={thStyle}>Criterio</th><th style={thStyle}>Peso</th>
                        <th style={{...thStyle,background:"#c6f6d5"}}>Excelente</th>
                        <th style={{...thStyle,background:"#bee3f8"}}>Bueno</th>
                        <th style={{...thStyle,background:"#fefcbf"}}>Regular</th>
                        <th style={{...thStyle,background:"#fed7d7"}}>Deficiente</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(f.rubric.criteria || []).map((cr: any, ci: number) => (
                        <tr key={ci}>
                          <td style={{...tdStyle,fontWeight:600}}>{cr.criterion}</td>
                          <td style={tdStyle}>{cr.weight}</td>
                          <td style={{...tdStyle,background:"#f0fff4"}}>{cr.excelente || cr.excellent || ""}</td>
                          <td style={{...tdStyle,background:"#ebf8ff"}}>{cr.bueno || cr.good || ""}</td>
                          <td style={{...tdStyle,background:"#fffff0"}}>{cr.regular || ""}</td>
                          <td style={{...tdStyle,background:"#fff5f5"}}>{cr.deficiente || cr.deficient || ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function MasterclassTab({ script }: { script: any }) {
  if (!script || (typeof script === "object" && Object.keys(script).length === 0)) {
    return <p style={{color:"#718096",padding:"1rem"}}>El guión de masterclass se generará en la próxima ejecución del pipeline.</p>;
  }
  const s = typeof script === "string" ? {} : script;
  const structure = s.structure || [];
  return (
    <div>
      <h3 style={{marginTop:0}}>🎬 {s.title || "Guión de Masterclass"}</h3>
      <div style={{display:"flex",gap:"1rem",marginBottom:"1rem",flexWrap:"wrap"}}>
        <StatCard label="Duración" value={`${s.duration_minutes || 20} min`} />
        <StatCard label="Slides" value={s.total_slides || structure.length} />
        <StatCard label="Secciones" value={structure.length} />
      </div>
      {s.theme && <p style={{color:"#718096",fontSize:"0.85rem",marginBottom:"1rem"}}>Tema central: <strong>{s.theme}</strong></p>}
      {structure.map((sec: any, i: number) => (
        <div key={i} style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",marginBottom:"0.75rem",overflow:"hidden"}}>
          <div style={{background:"#2d3748",color:"white",padding:"0.5rem 1rem",display:"flex",justifyContent:"space-between",fontSize:"0.85rem"}}>
            <span><strong>{sec.section}</strong></span>
            <span>{sec.time} ({sec.duration_minutes} min)</span>
          </div>
          <div style={{padding:"1rem",lineHeight:1.7,fontSize:"0.9rem"}}>
            {(sec.content || "").split(/(\[SLIDE[^\]]*\]|\[DATO EN PANTALLA[^\]]*\]|\[CASO VISUAL[^\]]*\])/).map((part: string, pi: number) =>
              part.match(/^\[SLIDE/) ? <span key={pi} style={{background:"#bee3f8",padding:"0.1rem 0.4rem",borderRadius:"3px",fontSize:"0.8rem",fontWeight:600}}>{part}</span> :
              part.match(/^\[DATO/) ? <span key={pi} style={{background:"#fefcbf",padding:"0.1rem 0.4rem",borderRadius:"3px",fontSize:"0.8rem",fontWeight:600}}>{part}</span> :
              part.match(/^\[CASO/) ? <span key={pi} style={{background:"#fed7aa",padding:"0.1rem 0.4rem",borderRadius:"3px",fontSize:"0.8rem",fontWeight:600}}>{part}</span> :
              <span key={pi}>{part}</span>
            )}
          </div>
          {sec.notes && <div style={{padding:"0.5rem 1rem",background:"#f7fafc",borderTop:"1px solid #e2e8f0",fontSize:"0.8rem",color:"#718096"}}><em>📝 {sec.notes}</em></div>}
        </div>
      ))}
      {s.competencies_covered && <p style={{fontSize:"0.8rem",color:"#718096",marginTop:"0.5rem"}}>Competencias: {s.competencies_covered}</p>}
    </div>
  );
}

function ChallengeTab({ challenge }: { challenge: any }) {
  if (!challenge || (typeof challenge === "object" && Object.keys(challenge).length === 0)) {
    return <p style={{color:"#718096",padding:"1rem"}}>El reto de aprendizaje agéntico se generará en la próxima ejecución del pipeline.</p>;
  }
  const c = typeof challenge === "object" ? challenge : {};
  const rubric = c.rubric || {};
  const criteria = Array.isArray(rubric.criteria) ? rubric.criteria : (Array.isArray(rubric) ? rubric : []);
  return (
    <div>
      <h3 style={{marginTop:0}}>🏆 {c.title || "Reto de Aprendizaje Agéntico"}</h3>
      {c.week && <p style={{fontSize:"0.85rem",color:"#718096"}}>Semana {c.week}</p>}

      {c.scenario && (
        <div style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"1rem",marginBottom:"1rem"}}>
          <h4 style={{margin:"0 0 0.5rem",color:"#2d3748"}}>Escenario</h4>
          <p style={{lineHeight:1.7,margin:0}}>{c.scenario}</p>
        </div>
      )}

      {c.central_question && (
        <div style={{background:"#ebf4ff",border:"1px solid #bee3f8",borderRadius:"6px",padding:"1rem",marginBottom:"1rem"}}>
          <h4 style={{margin:"0 0 0.5rem",color:"#2b6cb0"}}>Pregunta Directiva Central</h4>
          <p style={{lineHeight:1.7,margin:0,fontWeight:500}}>{c.central_question}</p>
        </div>
      )}

      {c.deliverable && (
        <div style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"1rem",marginBottom:"1rem"}}>
          <h4 style={{margin:"0 0 0.5rem",color:"#2d3748"}}>Entregable</h4>
          <p style={{lineHeight:1.7,margin:0}}>{c.deliverable}</p>
        </div>
      )}

      {criteria.length > 0 && (
        <div style={{marginBottom:"1rem"}}>
          <h4 style={{margin:"0 0 0.75rem"}}>Rúbrica Analítica (4 niveles)</h4>
          <div style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:"0.8rem",minWidth:"600px"}}>
              <thead>
                <tr style={{background:"#2d3748",color:"white"}}>
                  <th style={{padding:"0.5rem",textAlign:"left",width:"20%"}}>Criterio</th>
                  <th style={{padding:"0.5rem",textAlign:"left",width:"5%"}}>Peso</th>
                  <th style={{padding:"0.5rem",textAlign:"left",background:"#38a169",width:"18.75%"}}>Excelente</th>
                  <th style={{padding:"0.5rem",textAlign:"left",background:"#3182ce",width:"18.75%"}}>Bueno</th>
                  <th style={{padding:"0.5rem",textAlign:"left",background:"#dd6b20",width:"18.75%"}}>Regular</th>
                  <th style={{padding:"0.5rem",textAlign:"left",background:"#e53e3e",width:"18.75%"}}>Deficiente</th>
                </tr>
              </thead>
              <tbody>
                {criteria.map((cr: any, i: number) => (
                  <tr key={i} style={{borderBottom:"1px solid #e2e8f0"}}>
                    <td style={{padding:"0.5rem",fontWeight:600}}>{cr.criterion || cr.criteria || ""}</td>
                    <td style={{padding:"0.5rem",textAlign:"center"}}>{cr.weight || ""}</td>
                    <td style={{padding:"0.5rem",background:"#f0fff4"}}>{cr.excelente || cr.excellent || ""}</td>
                    <td style={{padding:"0.5rem",background:"#ebf8ff"}}>{cr.bueno || cr.good || ""}</td>
                    <td style={{padding:"0.5rem",background:"#fffaf0"}}>{cr.regular || ""}</td>
                    <td style={{padding:"0.5rem",background:"#fff5f5"}}>{cr.deficiente || cr.deficient || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {c.learning_outcomes_assessed && (
        <p style={{fontSize:"0.8rem",color:"#718096"}}>RAs evaluados: {c.learning_outcomes_assessed}</p>
      )}
    </div>
  );
}

function CanvasPreviewTab({ preview }: { preview: any }) {
  const [selectedPage, setSelectedPage] = useState(0);
  if (!preview?.pages?.length) return <p>No hay preview disponible.</p>;

  const pages = preview.pages;
  const current = pages[selectedPage];

  const canvasCSS = `
    body { font-family: 'Lato', 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2D3B45; line-height: 1.5; padding: 1rem; }
    h1 { color: #2D3B45; font-size: 1.6rem; border-bottom: 1px solid #C7CDD1; padding-bottom: 0.5rem; margin-bottom: 1rem; }
    h2 { color: #2D3B45; font-size: 1.25rem; margin-top: 1.5rem; }
    h3 { color: #394B58; font-size: 1.05rem; margin-top: 1rem; }
    p { margin: 0.5rem 0; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
    th { background: #394B58; color: white; padding: 0.5rem; text-align: left; }
    td { padding: 0.4rem 0.5rem; border-bottom: 1px solid #C7CDD1; }
    tr:nth-child(even) { background: #F5F5F5; }
    ul, ol { margin: 0.5rem 0 0.5rem 1.5rem; }
    li { margin: 0.3rem 0; }
    em { color: #6B7B8D; }
    strong { color: #2D3B45; }
  `;

  return (
    <div>
      <h3 style={{marginTop:0}}>👁️ Preview Canvas LMS ({pages.length} páginas)</h3>
      <p style={{fontSize:"0.8rem",color:"#718096",marginBottom:"1rem"}}>
        Así se verá el contenido en Canvas LMS. Navegue entre páginas para revisar cada recurso.
      </p>

      {/* Page selector */}
      <div style={{display:"flex",gap:"0.25rem",marginBottom:"1rem",flexWrap:"wrap"}}>
        {pages.map((p: any, i: number) => (
          <button key={i} onClick={() => setSelectedPage(i)}
            style={{
              padding:"0.4rem 0.75rem",border:"1px solid #cbd5e0",borderRadius:"4px",cursor:"pointer",
              fontSize:"0.75rem",
              background: i === selectedPage ? "#2b6cb0" : "white",
              color: i === selectedPage ? "white" : "#4a5568",
              fontWeight: i === selectedPage ? 600 : 400,
            }}>
            {p.type === "quiz" ? "❓" : "📄"} {p.title?.substring(0, 30)}{p.title?.length > 30 ? "..." : ""}
          </button>
        ))}
      </div>

      {/* Canvas-styled preview */}
      <div style={{
        border:"1px solid #C7CDD1",borderRadius:"4px",background:"white",
        boxShadow:"0 1px 3px rgba(0,0,0,0.1)",overflow:"hidden",
      }}>
        {/* Canvas header bar */}
        <div style={{background:"#394B58",color:"white",padding:"0.5rem 1rem",fontSize:"0.8rem",display:"flex",justifyContent:"space-between"}}>
          <span>📄 {current.title}</span>
          <span style={{opacity:0.7}}>Página {selectedPage + 1} de {pages.length}</span>
        </div>
        {/* Content area */}
        <div
          style={{padding:"1.5rem",maxHeight:"600px",overflow:"auto"}}
          dangerouslySetInnerHTML={{__html: `<style>${canvasCSS}</style>${current.html || "<p>Sin contenido</p>"}`}}
        />
      </div>
    </div>
  );
}

/* ── Utility Components ─────────────────────────────────────── */

function StatCard({ label, value, ok }: { label: string; value: any; ok?: boolean }) {
  return (
    <div style={{background:"#fff",border:"1px solid #e2e8f0",borderRadius:"6px",padding:"0.75rem",textAlign:"center"}}>
      <div style={{fontSize:"1.4rem",fontWeight:700,color: ok === false ? "#e53e3e" : ok === true ? "#38a169" : "#2d3748"}}>{value}</div>
      <div style={{fontSize:"0.75rem",color:"#718096",marginTop:"0.25rem"}}>{label}</div>
    </div>
  );
}

function BloomBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    RECORDAR: "#bee3f8", COMPRENDER: "#c6f6d5", APLICAR: "#fefcbf",
    ANALIZAR: "#fed7aa", EVALUAR: "#feb2b2", CREAR: "#e9d8fd",
  };
  return (
    <span style={{background: colors[level] || "#e2e8f0",padding:"0.15rem 0.5rem",borderRadius:"4px",fontSize:"0.75rem",fontWeight:600}}>
      {level}
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div style={{marginBottom:"1rem"}}>
      <h4 onClick={() => setOpen(!open)} style={{cursor:"pointer",margin:"0 0 0.5rem",padding:"0.5rem",background:"#edf2f7",borderRadius:"4px"}}>
        {open ? "▼" : "▶"} {title}
      </h4>
      {open && <div style={{paddingLeft:"0.5rem"}}>{children}</div>}
    </div>
  );
}

const thStyle: React.CSSProperties = { padding:"0.5rem",textAlign:"left",borderBottom:"2px solid #cbd5e0",fontSize:"0.8rem" };
const tdStyle: React.CSSProperties = { padding:"0.4rem 0.5rem",borderBottom:"1px solid #e2e8f0" };
