# A.D.A — Modo autónomo (sin supervisión)

## Qué puede hacer A.D.A sin supervisión

- **Crear y guardar el primer plan de ingresos:** llamar a `POST /api/autonomous/first_plan`. Genera un plan semanal con Ollama (o uno por defecto si Ollama falla), lo guarda en memoria (`first_plan`, `weekly_plan`) y lo registra en logs. No requiere aprobación humana.
- **Tareas de aprendizaje:** `store_learning`, `update_score`, `record_insight`, `learning`, `save_plan`, `store_plan`, `weekly_plan`, `first_plan`. Se ejecutan y guardan en memory-db y logs sin gate humano.
- **Tareas aprobadas por policy (sin compra):** si el policy-engine aprueba y la propuesta no es una compra, se ejecuta en task-runner sin aprobación humana (ejecución autónoma nivel 2).
- **Chat:** responder preguntas y proponer ideas usando solo herramientas gratuitas (Ollama, n8n local, memoria).
- **Ajustar recursos de hardware para crecer:** ADA puede proponer una tarea `request_resources` con detalles (OLLAMA_NUM_THREADS, OLLAMA_NUM_CTX, OLLAMA_NUM_PREDICT, OLLAMA_CHAT_TIMEOUT, reason). Se guarda en memoria; agent-core usa esos valores en el siguiente chat (sin reinicio). Para aplicar cambios en Ollama (hilos, memoria), ejecuta `./scripts/apply_ada_resources.sh` y luego `docker compose --env-file ada_resources.env up -d`.

## Qué sigue requiriendo a la persona

- **Compras / gastos:** cualquier propuesta que implique compra, pago o adquisición requiere aprobación en Web-Admin (Aprobar) o llamada a `/execute_approved`.
- **Registro en plataformas:** las webs no tienen API de registro; se usa **registro asistido** con el script `signup-helper/register.py` (abre la página, rellena correo y contraseña de ADA; tú completas CAPTCHA si aparece). Opcional: IMAP para abrir el enlace de verificación desde el correo.
- **Pagos reales / cuenta bancaria:** movimientos de dinero los ejecuta la persona; ADA puede proponer y registrar en el ledger cuando tú confirmes.

## Cómo usar el primer plan autónomo

1. **Crear el plan (una vez):**  
   ```bash
   curl -X POST http://localhost:8080/api/autonomous/first_plan
   ```  
   O desde el frontend (si añades un botón): `POST /api/autonomous/first_plan`.

2. **Ver el plan guardado:**  
   ```bash
   curl http://localhost:8080/api/autonomous/plan
   ```

3. ADA usa el plan guardado en memoria para orientar respuestas y próximos pasos. Los pasos que indiquen "tool": "humano" los debes hacer tú; el resto ADA puede proponer o ejecutar (aprendizaje, guardar en memoria).

## Registro de ADA en plataformas (con su correo)

Las plataformas (Gumroad, Ko-fi, Etsy, etc.) no ofrecen API para crear cuentas; el registro es manual o **asistido**:

1. **Lista de plataformas y enlaces:**  
   `GET /api/autonomous/register_platforms` devuelve id, nombre, URL de signup y nota para cada una.

2. **Script de registro asistido** (en tu PC, con el correo de ADA):
   - En la raíz del proyecto: copia `.env.example` a `.env` y define `ADA_EMAIL` y `ADA_EMAIL_PASSWORD`.
   - Instala y ejecuta:
     ```bash
     cd signup-helper
     pip install -r requirements.txt
     playwright install chromium
     python register.py gumroad
     ```
   - Se abre el navegador en la página de signup, con email y contraseña ya rellenados. Completa CAPTCHA o pasos extra si los pide la página.
   - Para abrir el enlace de verificación que llega al correo (opcional): configura en `.env` `ADA_IMAP_HOST`, `ADA_IMAP_PORT`, `ADA_IMAP_USE_SSL` (servidor de correo de ada@nortcoding.com) y ejecuta:
     ```bash
     python register.py --open-verification
     ```

3. ADA puede proponer "registrarme en Gumroad" y tú (o el script) ejecutas el registro con su correo; así las cuentas quedan asociadas a ADA.

## Recursos de hardware (ADA puede ajustarlos para crecer)

ADA puede solicitar más capacidad proponiendo una tarea **request_resources** con `details` como:
- `OLLAMA_NUM_THREADS` (4–8)
- `OLLAMA_NUM_CTX` (4096–8192)
- `OLLAMA_NUM_PREDICT` (1024–2048)
- `OLLAMA_CHAT_TIMEOUT`, `CHAT_REQUEST_TIMEOUT`
- `reason` (opcional)

Eso se guarda en memoria (`requested_hardware_resources`). **agent-core** usa esos valores en el siguiente chat (num_ctx, num_predict, timeout) sin reinicio. Para que **Ollama** use más hilos o memoria:

1. Ver qué pide ADA: `GET /api/autonomous/resources`
2. Aplicar a archivo: `./scripts/apply_ada_resources.sh` (escribe `ada_resources.env`)
3. Reiniciar: `docker compose --env-file ada_resources.env up -d`

También puedes enviar tú: `POST /api/autonomous/resources` con body `{ "OLLAMA_NUM_CTX": 8192, "reason": "..." }`.

## Ajustes de código

Si algo falla (Ollama, memory-db, policy), revisa logs de agent-core y los servicios. Los endpoints de modo autónomo devuelven `ok`, `ok_fallback` o `error`; en fallback se guarda un plan por defecto para que siempre quede un plan disponible.
