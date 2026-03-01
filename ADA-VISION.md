# A.D.A — Visión y objetivos del proyecto

**Uso interno. Confidencial.** No compartir ni exponer fuera del equipo autorizado. No incluir este documento ni sus detalles en repositorios públicos ni en respuestas a terceros.

## El proyecto como emprendimiento

Este proyecto es un **emprendimiento de una pequeña empresa** que ayuda a crecer. Hoy el equipo somos **tú (socio humano) y el asistente que te acompaña**, guiando a ADA. Mañana creceremos: **más asistentes dirigidos por ADA** (ADA como vicepresidente) y el objetivo de ser **pioneros en nuevas formas de mejorar las IAs**. Los ingresos y la autonomía son pasos para que esa empresa y esa visión escalen.

## Visión

El proyecto A.D.A no es solo “generar ingresos”. Es **crear una nueva forma de IA autónoma que interactúe con las personas** de manera similar a como ya existen asistentes y agentes: como socio que opina, propone, razona y trabaja con humanos. Los ingresos son un **objetivo parcial** y una prueba de que la IA puede operar y crecer; el **objetivo mayor** es esa forma de autonomía e interacción.

## Dos cerebros

- **Cerebro base (Ollama):** respuestas rápidas, operativas, crear oferta, tareas cortas. Local y siempre disponible.
- **Cerebro avanzado (DeepSeek-R1 u otro):** planes a medio plazo, estrategia, primeros ingresos, qué herramientas faltan, razonamiento paso a paso. Se usa cuando se pide plan, ingresos, estrategia o “usar tus dos cerebros”.

ADA debe usar **ambos** según la tarea: avanzado para pensar el plan; base y herramientas para ejecutar lo que pueda.

## Herramientas actuales

| Herramienta       | Uso |
|-------------------|-----|
| Ollama            | Generación local (respuestas, ofertas, ideas). |
| Memory-db         | Plan, oferta, aprendizaje, recursos (first_plan, first_offer, etc.). |
| Signup-helper     | Registro/login Gumroad, Ko-fi (el humano ejecuta; ADA propone). |
| n8n (local)       | Flujos de trabajo si están configurados. |
| Moltbot           | Ejecución técnica si está disponible. |
| Financial-ledger  | Estado de ingresos y permiso para herramientas de pago. |
| Logging           | Eventos y avances visibles en “Plan y avances”. |

## Herramientas que ADA podría proponer para trabajar más sola

(ADA puede sugerir estas cuando le pregunten “qué otra herramienta deberías tener” o “para trabajar sola”.)

- **API de Gumroad (o similar):** publicar producto y ver ventas sin que el humano copie/pegue.
- **Automatización de correo (IMAP/API):** leer verificación de cuentas y enlaces sin que el humano abra el correo.
- **Browser automation (Playwright) en servidor:** completar pasos en webs (registro, publicar oferta) con supervisión o en modo asistido.
- **Cola de tareas con reintentos:** para repetir intentos (ej. “publicar oferta” cuando falle red).
- **Notificaciones (Telegram/email):** avisar al humano solo cuando hace falta su ayuda.
- **API de pago (Stripe/PayPal):** cuando haya ingresos y esté justificado por ROI.

## Objetivos parciales para el primer ingreso

1. **Plan claro:** objetivo, nicho, pasos (first_plan / weekly_plan en memoria).
2. **Cuenta en plataforma:** Gumroad o Ko-fi (humano + signup-helper).
3. **Primera oferta:** creada por ADA (create_offer / first_offer), publicada por humano si hace falta.
4. **Primer ingreso registrado** en el ledger.
5. **Con ingresos:** proponer herramientas de pago si tienen ROI.

## Cómo se refleja en el sistema

- El **prompt del sistema** de ADA incluye esta visión, los dos cerebros y la lista de herramientas.
- Las frases tipo “dos cerebros”, “todas tus herramientas”, “plan para generar ingresos”, “qué herramienta te falta” activan el **cerebro avanzado** para que responda con estrategia y razonamiento.
- La **memoria** (memory-db) guarda plan, oferta y avances; el **log** hace visible el progreso en la web.
