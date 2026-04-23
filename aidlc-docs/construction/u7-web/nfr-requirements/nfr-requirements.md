# NFR Requirements — U7: Interfaz Web

## Seguridad
- Autenticación Cognito con JWT en todas las rutas (BR-W03, SECURITY-08, SECURITY-12)
- Headers HTTP de seguridad en todas las respuestas API (SECURITY-04): CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- CORS restringido al dominio de la interfaz web (SECURITY-08)
- Presigned URLs de S3 con expiración de 5 minutos
- Brute-force protection en login: bloqueo tras 5 intentos fallidos (SECURITY-12)
- MFA habilitado para cuentas de Administrador (SECURITY-12)

## Rendimiento
- Tiempo de carga inicial del dashboard: < 2 segundos
- Polling cada 30 segundos (BR-W05) — no WebSocket para simplicidad
- Presigned URL generada en < 500ms

## Usabilidad
- Interfaz responsive (desktop y tablet)
- Mensajes de error claros en español/inglés según idioma del navegador
- data-testid en todos los elementos interactivos (BR-W07)

## Observabilidad
- CloudWatch Logs para todos los Lambda handlers
- Métricas: `DocumentsUploaded`, `ParseErrors`, `LoginAttempts`
