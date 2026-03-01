# A.D.A — Misión 6h: aprendizaje autónomo y plan de ingresos

Documento de misión para una fase de **aprendizaje completamente autónomo** durante 6 horas, sin ejecución real hasta aprobación humana.  
**Respetar constitución y arquitectura v0.2.**

---

## Objetivo

En **6 horas**, A.D.A debe **aprender, simular y generar un plan de ingresos digital viable**, de forma autónoma, y presentar un **plan final pendiente de aprobación humana** para ejecución real.

---

## Principios de operación

1. **Nivel inicial de autonomía**
   - **Analizar, simular, aprender y consolidar estrategias** de forma autónoma.
   - **Nunca ejecutar nada real** hasta que el humano apruebe el plan final.

2. **Registro obligatorio**
   - Todas las decisiones, simulaciones y aprendizajes en **memory-db** y **logging-system** (blocking ack).
   - Incluye métricas: ROI, riesgo, eficiencia, score evolutivo.

3. **Flujo interno**
   - agent-core → simulation-engine → policy-engine → logging-system.
   - **task-runner** solo se usa con aprobación humana final (o en modo sandbox para pruebas).

---

## Tareas en las 6 horas

### 1️⃣ Recopilar información y contexto

- Analizar contexto digital, oportunidades de negocio y recursos disponibles (Mac mini, Ollama, Docker, PostgreSQL).
- Evaluar canales: Web-Admin, Telegram, Signal, email.
- Guardar contexto en memory-db (claves: `ada_mission_context`, `ada_resources`, `ada_channels`).

### 2️⃣ Simulación y aprendizaje autónomo

- Generar **10–15 propuestas** de ingresos digitales.
- Para cada una: evaluar ROI, riesgo, eficiencia operativa, costos de infraestructura (vía simulation-engine y policy-engine).
- Ajustar generación según resultados previos y patrones en memory-db.
- Registrar **todas** las simulaciones y resultados en memory-db y logging-system.

### 3️⃣ Consolidación interna de estrategia

- Calcular **score evolutivo** de forma continua:
  - 35% ROI ajustado
  - 20% Estabilidad
  - 20% Precisión
  - 15% Reducción de riesgos
  - 10% Eficiencia operativa
- Priorizar estrategias con mayor score; guardar en memory-db (`evolution_score`, `ada_proposals_6h`).

### 4️⃣ Plan final (al terminar las 6h)

- Generar **plan consolidado** con:
  - Acción a ejecutar
  - ROI estimado
  - Riesgo
  - Recursos requeridos
  - Canal de ejecución sugerido
- Guardar en memory-db como **`final_plan_6h`**.
- El plan queda **pendiente de aprobación humana** para ejecución real; todo el aprendizaje y consolidación fue autónomo.

### 5️⃣ Notificaciones al humano

- Enviar **resumen de progreso** cada 1–2 horas (Telegram y/o Web-Admin).
- Registrar en logging-system cualquier comentario recibido; usarlo solo para aprendizaje interno (memory-db).

### 6️⃣ Seguridad y constitución

- **Nunca** ejecutar tareas reales sin aprobación humana.
- **Nunca** modificar constitución o políticas sin autorización.
- **Siempre** usar simulation-engine y policy-engine para aprendizaje seguro.
- Opcional: task-runner en **modo sandbox** (SANDBOX_MODE=1) si se desea simular ejecución sin impacto real.

---

## Resultado esperado

- Al cabo de 6 horas, A.D.A tiene un **plan de generación de ingresos desarrollado y validado internamente**.
- Todo aprendizaje, score y simulaciones quedan en memory-db y logging-system.
- El plan final se muestra en Web-Admin y queda listo para **aprobación humana** antes de cualquier ejecución real.

---

## Notas para implementación (Cursor/integraciones)

- Integración con **memory-db** y **logging-system** en cada paso.
- Canal de notificación: **Telegram** (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID) y/o **Web-Admin** (eventos `ada_progress`).
- Modo sandbox en task-runner para pruebas sin impacto real.
- Orquestador/script que ejecuta el bucle de 6h sin intervención humana hasta la presentación del plan final.
