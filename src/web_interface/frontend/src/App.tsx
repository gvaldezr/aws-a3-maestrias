import React, { useState, useCallback } from "react";
import { SubjectTable } from "./components/SubjectTable";
import { CheckpointPage } from "./pages/CheckpointPage";

const WEB_API = "https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod";
const CHECKPOINT_API = "https://zcf0tiic2e.execute-api.us-east-1.amazonaws.com/prod";

// Override API_BASE for the pipeline module
(window as any).__API_BASE__ = WEB_API;
(window as any).__CHECKPOINT_API__ = CHECKPOINT_API;

export function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token") || "");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [checkpointSubject, setCheckpointSubject] = useState<string | null>(null);

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
        const t = data.AuthenticationResult.IdToken;
        localStorage.setItem("access_token", t);
        setToken(t);
      } else if (data.ChallengeName === "NEW_PASSWORD_REQUIRED") {
        setLoginError("Debe cambiar su contraseña. Use la consola de AWS Cognito.");
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

  if (!token) {
    return (
      <div style={{maxWidth:"400px",margin:"4rem auto",padding:"2rem",fontFamily:"system-ui,sans-serif",background:"#fff",borderRadius:"8px",boxShadow:"0 2px 8px rgba(0,0,0,0.1)"}}>
        <h1 style={{textAlign:"center",color:"#1a365d",fontSize:"1.3rem"}}>Pipeline Académico</h1>
        <p style={{textAlign:"center",color:"#718096",fontSize:"0.85rem"}}>Anáhuac Mérida — Staff de Tecnología Educativa</p>
        <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Usuario"
          style={{width:"100%",padding:"0.6rem",marginBottom:"0.5rem",borderRadius:"4px",border:"1px solid #cbd5e0",boxSizing:"border-box"}} />
        <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Contraseña" type="password"
          onKeyDown={e => e.key === "Enter" && handleLogin()}
          style={{width:"100%",padding:"0.6rem",marginBottom:"0.75rem",borderRadius:"4px",border:"1px solid #cbd5e0",boxSizing:"border-box"}} />
        {loginError && <p style={{color:"#c00",fontSize:"0.85rem"}}>{loginError}</p>}
        <button onClick={handleLogin}
          style={{width:"100%",padding:"0.7rem",background:"#2b6cb0",color:"white",border:"none",borderRadius:"6px",cursor:"pointer",fontWeight:600}}>
          Iniciar Sesión
        </button>
      </div>
    );
  }

  if (checkpointSubject) {
    return (
      <div>
        <div style={{background:"#1a365d",padding:"0.5rem 1rem",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <button onClick={() => setCheckpointSubject(null)} style={{background:"none",border:"none",color:"white",cursor:"pointer",fontSize:"0.9rem"}}>← Volver al Dashboard</button>
          <button onClick={handleLogout} style={{background:"none",border:"none",color:"#cbd5e0",cursor:"pointer",fontSize:"0.8rem"}}>Cerrar Sesión</button>
        </div>
        <CheckpointPage subjectId={checkpointSubject} onDecisionComplete={() => setCheckpointSubject(null)} />
      </div>
    );
  }

  return (
    <div style={{fontFamily:"system-ui,sans-serif"}}>
      <div style={{background:"#1a365d",padding:"0.75rem 1.5rem",display:"flex",justifyContent:"space-between",alignItems:"center",color:"white"}}>
        <h1 style={{margin:0,fontSize:"1.1rem"}}>Pipeline Académico — Dashboard</h1>
        <button onClick={handleLogout} style={{background:"none",border:"1px solid #cbd5e0",color:"white",padding:"0.3rem 0.75rem",borderRadius:"4px",cursor:"pointer",fontSize:"0.8rem"}}>Cerrar Sesión</button>
      </div>
      <div style={{padding:"1rem"}}>
        <SubjectTable onCheckpoint={(id) => setCheckpointSubject(id)} />
      </div>
    </div>
  );
}
