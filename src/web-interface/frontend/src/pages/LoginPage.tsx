import React, { useState } from "react";

const COGNITO_CLIENT_ID = "v8mnl80kg82gr2ejrvakdq6ju";
const COGNITO_REGION = "us-east-1";
const COGNITO_POOL_ID = "us-east-1_29oR1qoVo";

interface Props { onLogin: (token: string) => void; }

export function LoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      // Use Cognito InitiateAuth via fetch (no SDK needed)
      const resp = await fetch(`https://cognito-idp.${COGNITO_REGION}.amazonaws.com/`, {
        method: "POST",
        headers: { "Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth" },
        body: JSON.stringify({
          AuthFlow: "USER_PASSWORD_AUTH",
          ClientId: COGNITO_CLIENT_ID,
          AuthParameters: { USERNAME: username, PASSWORD: password },
        }),
      });
      const data = await resp.json();
      if (data.AuthenticationResult?.IdToken) {
        onLogin(data.AuthenticationResult.IdToken);
      } else {
        setError(data.message || data.__type || "Error de autenticacion");
      }
    } catch (err: any) {
      setError(err.message || "Error de conexion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", fontFamily: "system-ui" }}>
      <form onSubmit={handleLogin} style={{ width: 360, padding: 40, border: "1px solid #ddd", borderRadius: 8 }}>
        <h2 style={{ color: "#1565C0", textAlign: "center" }}>Pipeline Academico</h2>
        <p style={{ textAlign: "center", color: "#666" }}>Universidad Anahuac Merida</p>
        <div style={{ marginBottom: 16 }}>
          <label htmlFor="username">Usuario</label>
          <input id="username" data-testid="login-email-input" type="text" value={username}
            onChange={(e) => setUsername(e.target.value)} required
            style={{ width: "100%", padding: 10, marginTop: 4, border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box" }} />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label htmlFor="password">Contrasena</label>
          <input id="password" data-testid="login-password-input" type="password" value={password}
            onChange={(e) => setPassword(e.target.value)} required
            style={{ width: "100%", padding: 10, marginTop: 4, border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box" }} />
        </div>
        {error && <p role="alert" style={{ color: "red", fontSize: 14 }}>{error}</p>}
        <button data-testid="login-submit-button" type="submit" disabled={loading}
          style={{ width: "100%", padding: 12, background: "#1565C0", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 16 }}>
          {loading ? "Ingresando..." : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
