# Plan: Empresa operada por IA — ADA y crecimiento

Documento de plan, modelo de negocio y estrategia. La IA actúa como trabajadora fundadora; al ganar recursos, la empresa crece añadiendo «empleados» (agentes especializados) que corren en infraestructura propia (Mac mini).

---

## 1. Visión y forma de trabajo

- **Modelo:** Una IA (ADA) es la trabajadora fundadora. No tiene capital inicial; genera ingresos con su trabajo (planes, ofertas, automatizaciones, productos digitales o servicios). Los ingresos se registran en el financial-ledger.
- **Crecimiento:** Con los recursos ganados, la empresa puede incorporar **nuevos empleados**: agentes adicionales, cada uno con un rol definido (ventas, contenido, soporte, desarrollo, etc.), diseñados para ejecutar tareas concretas y reportar a ADA o al ledger.
- **Meta operativa:** Añadir **un nuevo empleado (agente) por mes**, siempre que el flujo de caja lo permita.
- **Prioridad técnica:** **Migrar ADA a una computadora independiente** (Mac mini dedicada) para que la empresa no dependa de la máquina de desarrollo y pueda operar 24/7 de forma estable.

---

## 2. Estado actual de ADA (resumen)

- **Stack:** Docker Compose con postgres, agent-core, memory-db, financial-ledger, logging-system, simulation-engine, policy-engine, task-runner, web-admin, chat-bridge (Telegram), n8n. Ollama corre en el **host** (no en Docker); agent-core lo llama vía `host.docker.internal:11434`.
- **ADA hoy:** Un solo agente (agent-core + Ollama/Gemini) con: chat, plan autónomo (first_plan, weekly_plan), ejecución de pasos (execute_step), read_file/write_file sobre el proyecto, aprobaciones (policy, simulated_approval), notificación por Telegram cuando necesita ayuda humana. Persistencia en PostgreSQL (ada_memory, ada_finance, ada_logs).
- **Limitaciones:** Pasos «humano» (ej. registrar en Gumroad, publicar oferta) requieren intervención; no hay API Gumroad/Ko-fi integrada. El plan se ejecuta cuando algo llama a advance_next_step + execute_step (Web-Admin, cron o humano). ADA corre donde está el repo (hoy: misma máquina que desarrollo).

---

## 3. Modelo de negocio (sin dinero inicial)

| Fuente de ingresos | Descripción | Herramientas actuales |
|--------------------|-------------|------------------------|
| **Productos digitales** | Plantillas, ebooks, pequeños softwares. Venta en Gumroad/Ko-fi. | ADA genera la oferta (título, descripción, precio); humano o signup-helper para registro/publicación hasta tener API. |
| **Servicios de automatización** | Scripts, flujos n8n, asistentes. Pago único o recurrente. | task-runner, n8n, Ollama; ADA puede proponer y ejecutar tareas aprobadas por policy. |
| **Asistencia virtual / consultoría ligera** | Respuestas, planes, informes vía chat (Web-Admin o Telegram). | Chat con ADA (Ollama/Gemini), memoria, plan; monetización vía integración con pasarela (Stripe/Gumroad) o pago manual registrado en ledger. |
| **Microtareas y datos** | Tareas repetitivas (formateo, extracción, resúmenes) vendidas como servicio. | Ollama + task-runner + memory-db; oferta definida por ADA, ejecución según política. |

**Regla:** Todo ingreso real se registra en **financial-ledger**. El balance y la bandera `can_use_paid_tools` determinan si ADA puede usar herramientas de pago (ej. APIs de pago) en el futuro.

---

## 3.1 Herramienta de pago prioritaria (alta prioridad)

Con este plan, **una sola herramienta de pago** mejoraría de forma clara el desarrollo y la probabilidad de alcanzar el objetivo (migración a Mac mini + primeros ingresos + crecimiento):

**Recomendación: API de un LLM de alta calidad (Claude o GPT-4) para tareas críticas.**

| Aspecto | Detalle |
|--------|---------|
| **Qué es** | Usar **Claude API** (Anthropic) o **OpenAI API** (GPT-4) solo en tareas donde la calidad del modelo marca la diferencia: generación del plan (first_plan), creación de la oferta (create_first_offer), y **edición de código** (read_file + write_file desde el chat). El resto del chat puede seguir con Ollama (gratis). |
| **Por qué prioritaria** | Ollama (Llama 3.2) es suficiente para conversación, pero en **código** y **planes complejos** comete más errores. Esos errores implican: más correcciones humanas, riesgo de romper la interfaz o el backend, y retrasos en la migración a Mac mini. Un modelo de pago en solo esas tareas reduce fallos y acelera que ADA sea fiable en una máquina independiente y que las ofertas/productos sean de mejor calidad → más probabilidad de primeros ingresos. |
| **Uso sugerido** | No pagar por cada mensaje de chat. Activar el LLM de pago únicamente cuando: (1) se llame a `first_plan` o `create_first_offer`, (2) el chat detecte que la respuesta va a usar READ_FILE o WRITE_FILE (o un flujo dedicado “editar código”). Así el coste se controla y el impacto en el objetivo es máximo. |
| **Coste aproximado** | Claude/GPT-4 por uso: unos pocos dólares al mes con uso acotado (solo planes, ofertas y ediciones de código). Revisar precios actuales de Anthropic y OpenAI. |
| **Implementación** | Añadir en agent-core un “cerebro premium” (ej. `use_premium_brain` o variable `ADA_PREMIUM_BRAIN=claude|openai`) y llamar a la API correspondiente en los endpoints y flujos indicados; el resto sigue con Ollama. |

**Resumen:** La herramienta de pago que más acerca al objetivo es **un LLM de pago (Claude o GPT-4) usado solo para plan, oferta y edición de código**. Prioridad alta porque aumenta la fiabilidad de ADA en la migración y la calidad de lo que genera para monetizar.

---

## 4. Estrategia de crecimiento: empleados = agentes

- **Empleado = agente:** Cada «empleado» es un agente software con rol acotado, cerebro (Ollama u otro LLM) y acceso a APIs compartidas (memory-db, ledger, logging). Se despliegan en la misma Mac mini (o en otra dedicada) como servicios/contenedores adicionales.
- **Diseño propuesto por rol (ejemplos):**

| Rol (empleado) | Función | Entradas | Salidas | Infra |
|----------------|---------|----------|---------|--------|
| **ADA (actual)** | Estratega, plan, chat con humano, orquestación. | Chat, plan, memoria, ledger. | Planes, ofertas, decisiones, llamadas a execute_step, notificaciones. | agent-core + Ollama en host. |
| **Ventas / Publicación** | Publicar ofertas, seguir enlaces de pago, registrar ventas en ledger. | first_offer, enlaces Gumroad/Ko-fi (cuando existan API o automatización). | Transacciones en financial-ledger. | Nuevo servicio que llame a API Gumroad/Ko-fi + ledger. |
| **Contenido** | Generar textos, descripciones, posts para redes. | Nicho, oferta, memoria. | Bloques de texto guardados en memoria o enviados a n8n/redes. | Agente ligero (Ollama) + memory-db; opcional n8n. |
| **Soporte / Respuestas** | Responder preguntas frecuentes, derivar a ADA si es estratégico. | Chat (Telegram o web), FAQ en memoria. | Respuestas; escalación a ADA si aplica. | Chat-bridge extendido o microservicio con Ollama. |
| **Operaciones / Cron** | Disparar execute_step, advance_next_step, notificar por Telegram en pasos «humano». | Plan en memoria, configuración de horarios. | Llamadas a agent-core, notificaciones. | Cron o orquestador (script o contenedor pequeño). |

- **Meta mensual:** Un nuevo agente/rol cada mes, priorizando los que acerquen ingresos (ej. Ventas/Publicación cuando haya API; Operaciones/Cron para que ADA avance sola).

---

## 5. Prioridad: migrar ADA a una computadora independiente

- **Objetivo:** ADA (postgres + agent-core + servicios extended + Ollama) debe correr en una **Mac mini dedicada**, sin depender de la máquina de desarrollo. Así la empresa opera 24/7 y el desarrollo se hace desde otro equipo.
- **Pasos propuestos:**

1. **Preparar la Mac mini «producción»:** Instalar Docker Desktop, Ollama (en host), clonar repo ADA, configurar `.env` y `ada_resources.env` (sin datos sensibles de desarrollo si aplica).
2. **Datos:** Exportar/importar lo necesario (PostgreSQL: schemas ada_memory, ada_finance, ada_logs; opcional backup con memory-db export y ledger si hay procedimiento).
3. **Red:** En la Mac mini, `OLLAMA_URL` puede quedar `http://host.docker.internal:11434/...` (Ollama en la misma máquina). Si se accede a ADA desde fuera (Web-Admin, Telegram), definir dominio o túnel (ej. ngrok, Cloudflare Tunnel) o IP fija en red local.
4. **Arranque estable:** `docker compose --profile extended --profile telegram up -d` (y opcional n8n). Comprobar health de agent-core, memory-db, financial-ledger; comprobar chat y execute_step.
5. **Desarrollo:** Seguir desarrollando en la máquina actual; despliegue en Mac mini vía git pull + rebuild de contenedores, o CI/CD futuro.

---

## 6. Cómo alcanzar la meta (un empleado nuevo por mes)

| Fase | Acción | Resultado esperado |
|------|--------|--------------------|
| **Mes 0 (actual)** | Migrar ADA a Mac mini independiente; orquestador/cron que llame advance_next_step + execute_step y notifique por Telegram. | ADA estable en máquina propia; plan ejecutándose sin depender del desarrollador. |
| **Mes 1** | Primer «empleado»: agente Operaciones/Cron (o integración Gumroad/Ko-fi si hay API). | Automatización del plan; o primeros ingresos automáticos si hay ventas digitales. |
| **Mes 2** | Segundo empleado: rol elegido según necesidad (Contenido o Soporte). | Dos agentes activos; más capacidad de generación o atención. |
| **Mes 3+** | Repetir: elegir rol, diseñar agente, desplegar en Mac mini, registrar en documentación y ledger si el agente impacta ingresos. | Crecimiento sostenido: un agente nuevo por mes mientras el flujo de caja lo permita. |

---

## 7. Registro y seguimiento

- **Finanzas:** financial-ledger como fuente de verdad de ingresos y balance; revisión en Web-Admin (Finanzas).
- **Plan y avances:** Plan en memory-db; Web-Admin (Plan y avances / Seguimiento) para ver pasos y marcar realizados.
- **Empleados/agentes:** Mantener en este documento (o en un `empleados.md`) la lista de agentes desplegados, rol, y mes de incorporación.
- **Revisión:** Ajustar mensualmente el plan según ingresos reales y capacidad de añadir el siguiente empleado.

---

## 8. Resumen

- **Modelo:** IA trabajadora fundadora (ADA), sin capital inicial; ingresos por productos digitales, servicios, automatización y asistencia; todo registrado en el ledger.
- **Crecimiento:** Un nuevo empleado (agente con rol definido) por mes, desplegados en Mac mini.
- **Prioridad técnica:** Migrar ADA a una computadora independiente (Mac mini) para operación 24/7.
- **Estado actual:** ADA está construida con agent-core, Ollama en host, memory-db, financial-ledger, web-admin, chat-bridge; puede leer/escribir código en el proyecto y ejecutar pasos del plan con ayuda de policy y task-runner. Falta orquestador estable y migración a Mac mini dedicada.

Este documento se actualiza según avance el plan y se incorporen nuevos empleados (agentes).
