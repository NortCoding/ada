# Por qué ADA pide intervención y qué ajustar para que actúe sola

## Resumen

ADA pide tu intervención por **tres motivos** principales. Cada uno tiene un ajuste posible:

| Motivo | Qué pasa ahora | Qué ajustar |
|--------|-----------------|-------------|
| **1. Compras/gastos** | Cualquier propuesta que parezca una compra va a «pendiente de aprobación» y no se ejecuta hasta que tú apruebas. | Política con aprobación simulada o variable `ADA_AUTONOMOUS_PURCHASES` (ver abajo). |
| **2. Pasos del plan «humano»** | El plan tiene pasos con herramienta «humano» (registrar en Gumroad, publicar oferta). ADA no puede hacerlos porque no hay API. | Integrar API de Gumroad/Ko-fi o automatización (navegador) para esos pasos. |
| **3. Nadie dispara el plan** | El plan existe pero hace falta que alguien llame a «ejecutar siguiente paso» (Web-Admin, cron o tú). | Programar un cron o orquestador que llame a `/autonomous/execute_step` y notifique por Telegram cuando toque un paso humano. |

---

## 1. Compras y aprobación humana

**Código (agent-core):** Si la propuesta es de tipo «compra» y la política **no** devuelve `simulated_approval`, se devuelve `pending_approval` y no se ejecuta.

**Opciones para que ADA ejecute sola (sin preguntarte):**

### A) Política con aprobación simulada (recomendado)

En PostgreSQL ya existe una regla con `simulated_approval: true` para acción `*` (cualquier acción), con condiciones `roi_min` y `risk_max`. Si la **simulación** devuelve ROI y riesgo dentro de ese rango, la política devuelve `simulated_approval` y agent-core **sí ejecuta** (también para compras).

- Revisa que la regla esté activa en `ada_policies.rules` (action_type `'*'`, `config` con `simulated_approval: true`, `roi_min`, `risk_max`).
- Asegúrate de que **simulation-engine** y **policy-engine** estén en marcha y que las propuestas que quieras auto-aprobar pasen por simulación y cumplan esas métricas.

### B) Variable `ADA_AUTONOMOUS_PURCHASES`

Si en el `.env` de agent-core pones:

```env
ADA_AUTONOMOUS_PURCHASES=true
```

entonces, cuando la **política apruebe** (approved), agent-core ejecutará la tarea **incluso si es una compra**, sin esperar aprobación humana. Úsalo solo si confías en la política y la simulación.

---

## 2. Pasos del plan que son «humano»

Los pasos con `tool: "humano"` (p. ej. «Registrar en Gumroad», «Publicar oferta») no tienen implementación automática: no hay API de Gumroad/Ko-fi en el proyecto.

**Para que ADA los haga sola hace falta:**

- Integrar la **API de Gumroad** (y/o Ko-fi) en agent-core o task-runner para:
  - publicar productos,
  - (opcional) crear/gestión de cuenta vía API si aplica.
- O usar **automatización de navegador** (p. ej. Playwright) asistida para esos pasos (más frágil, pero posible).

Mientras no exista una de esas dos cosas, esos pasos seguirán requiriendo que un humano los haga (o los marque como hechos en Web-Admin / `step_done`).

---

## 3. Que «algo» ejecute el plan sin que tengas que entrar tú

Hoy el plan se ejecuta cuando:

- Tú (o la Web-Admin) llamas a **ejecutar paso** o **marcar como realizado**, o
- Un orquestador/cron llama a los endpoints.

**Para que ADA «avance sola»:**

- **Cron o orquestador** que cada X tiempo:
  1. Llame a `POST /autonomous/advance_next_step` (devuelve el siguiente paso pendiente).
  2. Si `next_step_index` viene definido, llame a `POST /autonomous/execute_step?step_index=N`.
  3. Si la respuesta es `needs_help` (paso humano), envíe notificación por **Telegram** (por ejemplo al chat-bridge `POST /send`) pidiendo ayuda.
- Así ADA ejecuta sola los pasos Ollama y solo te notifica cuando toca un paso humano.

---

## Notificación por Telegram cuando ADA necesita ayuda

ADA **solo pide ayuda cuando no puede hacer algo** (pasos «humano» del plan). Cuando eso pasa:

- Agent-core envía un mensaje a **Telegram** (vía chat-bridge `POST /send`) con el paso, la acción y una sugerencia.
- El mensaje incluye: *«Si hace falta instalar nuevas herramientas, responde en el chat y te indico los pasos.»*

**Qué necesitas:** En `.env` (o en el entorno de agent-core) definir:

- `TELEGRAM_CHAT_ID` = tu chat_id (el número que obtienes cuando abres @ADA_SocioBot y envías /start).
- Tener **chat-bridge** en marcha (`docker compose --profile telegram up -d chat-bridge`) para que agent-core pueda llamar a `CHAT_BRIDGE_URL/send` (por defecto `http://chat-bridge:8081`).

Si no defines `TELEGRAM_CHAT_ID` o `CHAT_BRIDGE_URL`, ADA no envía Telegram pero sigue registrando el «needs_help» en logs y en Plan y avances.

---

## Checklist rápido para más autonomía

1. **Política:** Regla `*` con `simulated_approval: true` activa y simulation-engine devolviendo ROI/riesgo.
2. **Compras:** Opcionalmente `ADA_AUTONOMOUS_PURCHASES=true` en agent-core si quieres que las compras aprobadas por política se ejecuten sin preguntar.
3. **Telegram cuando pide ayuda:** `TELEGRAM_CHAT_ID` y chat-bridge en marcha (ADA te avisa solo cuando necesita ayuda).
4. **Plan:** Cron/orquestador que llame a `advance_next_step` + `execute_step`; en pasos humanos recibirás needs_help y (si está configurado) el aviso por Telegram.
5. **A largo plazo:** API Gumroad (o automatización navegador) para que los pasos «publicar oferta» / «registrar cuenta» dejen de ser «humano».
