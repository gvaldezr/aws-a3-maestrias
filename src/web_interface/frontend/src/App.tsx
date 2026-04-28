import React, { useState, useCallback, useRef } from "react";
import { SubjectTable } from "./components/SubjectTable";
import { CheckpointPage } from "./pages/CheckpointPage";
import { requestUploadUrl, uploadFileToS3 } from "./api/pipeline";

const WEB_API = "https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod";
const CHECKPOINT_API = "https://zcf0tiic2e.execute-api.us-east-1.amazonaws.com/prod";
(window as any).__API_BASE__ = WEB_API;
(window as any).__CHECKPOINT_API__ = CHECKPOINT_API;

export function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token") || "");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [checkpointSubject, setCheckpointSubject] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{type:"ok"|"err";text:string}|null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleLogin = async () => {
    setLoginError("");
    try {
      const resp = await fetch("https://cognito-idp.us-east-1.amazonaws.com/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-amz-json-1.1",
          "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        },
        body: JSON.stringify({
          AuthFlow: "USER_PASSWORD_AUTH",
          ClientId: "v8mnl80kg82gr2ejrvakdq6ju",
          AuthParameters: { USERNAME: username, PASSWORD: password },
        }),
      });
      const data = await resp.json();
      if (data.AuthenticationResult) {
        localStorage.setItem("access_token", data.AuthenticationResult.IdToken);
        setToken(data.AuthenticationResult.IdToken);
      } else if (data.ChallengeName === "NEW_PASSWORD_REQUIRED") {
        setLoginError("Debe cambiar su contraseña en la consola de AWS Cognito.");
      } else {
        setLoginError(data.message || "Error de autenticación");
      }
    } catch (e: any) {
      setLoginError(e.message || "Error de conexión");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setToken("");
    setCheckpointSubject(null);
  };

  const handleUpload = useCallback(async () => {
    const files = fileRef.current?.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    setUploadMsg(null);
    let ok = 0, fail = 0;
    for (const file of Array.from(files)) {
      try {
        const { upload_url } = await requestUploadUrl(file.name, file.size, file.type);
        await uploadFileToS3(upload_url, file);
        ok++;
      } catch (e: any) {
        fail++;
      }
    }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
    if (fail === 0) {
      setUploadMsg({type:"ok", text:`${ok} archivo(s) cargado(s). El pipeline se ejecutará automáticamente.`});
    } else {
      setUploadMsg({type:"err", text:`${ok} cargado(s), ${fail} con error.`});
    }
  }, []);

  /* ── Login ── */
  if (!token) {
    return (
      <div style={styles.loginWrapper}>
        <div style={styles.loginCard}>
          <div style={{textAlign:"center",marginBottom:"1.5rem"}}>
            <div style={{fontSize:"2rem",marginBottom:"0.5rem"}}>🎓</div>
            <h1 style={{margin:0,fontSize:"1.3rem",color:"#040404"}}>Vince Scholar</h1>
            <p style={{margin:"0.3rem 0 0",color:"#9C9C9C",fontSize:"0.85rem"}}>Anáhuac Mayab</p>
          </div>
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Usuario"
            style={styles.input} />
          <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Contraseña" type="password"
            onKeyDown={e => e.key === "Enter" && handleLogin()} style={styles.input} />
          {loginError && <p style={{color:"#e53e3e",fontSize:"0.85rem",margin:"0 0 0.5rem"}}>{loginError}</p>}
          <button onClick={handleLogin} style={styles.btnPrimary}>Iniciar Sesión</button>
        </div>
      </div>
    );
  }

  /* ── Checkpoint Review ── */
  if (checkpointSubject) {
    return (
      <>
        <nav style={styles.nav}>
          <button onClick={() => setCheckpointSubject(null)} style={styles.navBtn}>← Volver al Dashboard</button>
          <button onClick={handleLogout} style={styles.navBtnLight}>Cerrar Sesión</button>
        </nav>
        <CheckpointPage subjectId={checkpointSubject} onDecisionComplete={() => setCheckpointSubject(null)} />
      </>
    );
  }

  /* ── Dashboard ── */
  return (
    <div style={{fontFamily:"'Inter',system-ui,-apple-system,sans-serif",background:"#f7f7f7",minHeight:"100vh"}}>
      <nav style={styles.nav}>
        <div style={{display:"flex",alignItems:"center",gap:"0.75rem"}}>
          <span style={{fontSize:"1.3rem"}}>🎓</span>
          <h1 style={{margin:0,fontSize:"1rem",fontWeight:600}}>Vince Scholar</h1>
        </div>
        <button onClick={handleLogout} style={styles.navBtnLight}>Cerrar Sesión</button>
      </nav>

      <div style={{maxWidth:"1100px",margin:"0 auto",padding:"1.5rem"}}>
        {/* Upload Section */}
        <div style={styles.card}>
          <h2 style={{margin:"0 0 0.75rem",fontSize:"1.05rem",color:"#040404"}}>📤 Cargar Documentos</h2>
          <p style={{margin:"0 0 1rem",color:"#718096",fontSize:"0.85rem"}}>
            Suba archivos PDF, DOCX o XLSX con la información de la asignatura. El pipeline se ejecutará automáticamente.
          </p>
          <div style={{display:"flex",gap:"0.75rem",alignItems:"center",flexWrap:"wrap"}}>
            <input ref={fileRef} type="file" multiple accept=".pdf,.docx,.xlsx"
              style={{flex:1,minWidth:"200px",padding:"0.4rem",border:"1px solid #cbd5e0",borderRadius:"6px",background:"white"}} />
            <button onClick={handleUpload} disabled={uploading}
              style={{...styles.btnPrimary,opacity:uploading?0.6:1,minWidth:"120px"}}>
              {uploading ? "Subiendo..." : "Cargar"}
            </button>
          </div>
          {uploadMsg && (
            <p style={{margin:"0.75rem 0 0",padding:"0.5rem 0.75rem",borderRadius:"4px",fontSize:"0.85rem",
              background: uploadMsg.type === "ok" ? "#c6f6d5" : "#fed7d7",
              color: uploadMsg.type === "ok" ? "#22543d" : "#742a2a"}}>
              {uploadMsg.text}
            </p>
          )}
        </div>

        {/* Subject Table */}
        <div style={{...styles.card,marginTop:"1rem"}}>
          <h2 style={{margin:"0 0 0.75rem",fontSize:"1.05rem",color:"#040404"}}>📋 Estado del Pipeline</h2>
          <SubjectTable onCheckpoint={(id) => setCheckpointSubject(id)} />
        </div>
      </div>
    </div>
  );
}

/* ── Styles ── */
const styles: Record<string, React.CSSProperties> = {
  loginWrapper: {
    display:"flex",justifyContent:"center",alignItems:"center",minHeight:"100vh",
    background:"linear-gradient(135deg,#040404 0%,#262626 100%)",fontFamily:"'Inter',system-ui,sans-serif",
  },
  loginCard: {
    background:"white",borderRadius:"12px",padding:"2rem",width:"100%",maxWidth:"380px",
    boxShadow:"0 4px 24px rgba(0,0,0,0.2)",
  },
  input: {
    width:"100%",padding:"0.65rem 0.75rem",marginBottom:"0.6rem",borderRadius:"6px",
    border:"1px solid #e5e5e5",fontSize:"0.9rem",boxSizing:"border-box" as const,
  },
  btnPrimary: {
    width:"100%",padding:"0.7rem",background:"#FF5900",color:"white",border:"none",
    borderRadius:"6px",cursor:"pointer",fontWeight:600,fontSize:"0.9rem",
  },
  nav: {
    background:"#040404",padding:"0.6rem 1.5rem",display:"flex",justifyContent:"space-between",
    alignItems:"center",color:"white",
  },
  navBtn: {
    background:"none",border:"none",color:"white",cursor:"pointer",fontSize:"0.9rem",fontWeight:500,
  },
  navBtnLight: {
    background:"rgba(255,255,255,0.1)",border:"1px solid rgba(255,255,255,0.3)",color:"white",
    padding:"0.3rem 0.75rem",borderRadius:"4px",cursor:"pointer",fontSize:"0.8rem",
  },
  card: {
    background:"white",borderRadius:"8px",padding:"1.25rem",boxShadow:"0 1px 3px rgba(0,0,0,0.06)",
    border:"1px solid #e5e5e5",
  },
};
