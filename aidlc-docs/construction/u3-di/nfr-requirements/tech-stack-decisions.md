# Tech Stack — U3: Agente DI

| Componente | Tecnología | Justificación |
|---|---|---|
| Agente DI | Amazon Bedrock Agent (Claude Sonnet 3.5, temp=0) | Idempotencia, contexto largo para Carta Descriptiva |
| Lógica de negocio | Python 3.11 (funciones puras) | Testeable con PBT, sin efectos secundarios |
| PBT | Hypothesis | Consistente con U1/U2 (PBT-09) |
