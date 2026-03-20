# ADA ROADMAP

## META GLOBAL

Construir un agente autónomo capaz de:

- generar valor real
- mejorar su propio código
- ejecutar tareas de desarrollo
- escalar a sistema distribuido

---

## FASE ACTUAL

**FASE 1 — CLI funcional**

---

## OBJETIVOS ACTUALES

1. Crear CLI funcional
2. Implementar lectura de proyecto
3. Implementar escritura de archivos
4. Ejecutar comandos shell
5. Debug básico

---

## OBJETIVOS FUTUROS

### FASE 2

- memoria persistente
- registro de acciones
- evaluación de resultados

### FASE 3

- self-improvement
- generación de tareas
- optimización de código

### FASE 4

- arquitectura distribuida
- autonomía completa

---

## REGLAS

- No agregar complejidad innecesaria
- Priorizar ejecución real
- Todo debe ser verificable
- Cada cambio debe aportar valor

---

## ESTADO

- progreso: 0%
- estabilidad: baja
- prioridad: ejecución real

---

## ESTADO REAL DEL CÓDIGO (referencia)

*Lo que ya existe en el repo, para alinear ROADMAP con la realidad.*

| Fase   | En código hoy |
|--------|----------------|
| FASE 1 | ✅ Lectura/escritura (LIST_DIR, READ_FILE, WRITE_FILE), ejecución de comandos (RUN_COMMAND), modo ejecución estricto. Interfaz web (chat + explorador). |
| FASE 2 | ✅ Memoria (memory_service + Postgres), metas (goals), historial (experiences), evaluación (opportunities, learning). |
| FASE 3 | ✅ Self-improvement (self_improvement_engine), generación de ideas/planes (scheduler, strategy_engine, opportunity_engine), propuestas y ejecución con confirmación. |
| FASE 4 | ✅ Microservicios (agent-core, memory_service, chat_interface), scheduler en background, multi-agente (agent_manager, workspaces), agent_market, knowledge_base. |

*Actualizar "FASE ACTUAL" y "ESTADO" arriba según el foco que el equipo quiera (ej. consolidar FASE 1 como "base verificable" antes de más autonomía).*

---

## TRACE DE ETAPAS (APPEND-ONLY)

Objetivo: poder identificar qué fases/etapas están alcanzadas y cuáles hacen falta, y documentar en este mismo archivo qué se hizo en cada etapa.

Regla de mantenimiento:
- Siempre que se alcance un hito, **agrega** una nueva entrada al final del registro de esa fase.
- No edites ni elimines entradas ya registradas (si hay correcciones, se documentan como una nueva entrada).

Plantilla de entrada (para copiar y pegar):
- [YYYY-MM-DD] HIT0: <nombre corto del hito>
  - Resultado verificable: <link a PR/commit/archivo o comando/ejecución>
  - Evidencia mínima: <1-2 frases sobre qué se observó>
  - Nota de siguiente paso: <qué falta o qué se intenta después>

### FASE 1 — CLI funcional (base verificable)

- Estado: EN PROGRESO
- Hitos (append-only):
  - [2026-03-16] HIT0: V1 de ROADMAP creado y alineación conceptual por fases.
    - Resultado verificable: se actualizó `ada/ROADMAP.md` con el plan por fases.
    - Evidencia mínima: sección `FASE ACTUAL`, objetivos y tabla de `ESTADO REAL DEL CÓDIGO`.
    - Nota de siguiente paso: definir criterio formal de “CLI funcional” y cerrar la verificación con ejecuciones reales.
  - [2026-03-19] HIT1: CLI entrypoint funcional (comando recibido).
    - Resultado verificable: se creó `ada/cli/main.py`.
    - Evidencia mínima: ejecutado `python3 -m ada.cli.main "hola"` y se obtuvo `Command received: hola`.
    - Nota de siguiente paso: añadir router para comandos y conectar una primera “skill” real.
  - [2026-03-19] HIT2: Router básico para `analyze/fix/create`.
    - Resultado verificable: se creó `ada/cli/command_router.py` con detección por keywords.
    - Evidencia mínima: ejecutado `python3 -m ada.cli.main "fix proyecto"` -> `TODO: fix project (placeholder)`, y `python3 -m ada.cli.main "create proyecto"` -> `TODO: create project (placeholder)`.
    - Nota de siguiente paso: implementar un analizador real conectado a `analyze`.
  - [2026-03-19] HIT3: Skill real `analyze` (analizador de archivos).
    - Resultado verificable: se creó `ada/core/code_analyzer.py` y se conectó vía router.
    - Evidencia mínima: ejecutado `python3 -m ada.cli.main "analyze project"`, se imprimió listado de archivos y `Summary` con `Number of files: 1757` y breakdown por extensiones.
    - Nota de siguiente paso: definir criterio de “calidad” del analizador (filtros/limitación de listado) y registrar una ejecución reproducible desde otra carpeta.
  - [2026-03-19] HIT4: Ciclo completo verificable en CLI (`cycle`).
    - Resultado verificable: se implementó comando `cycle` vía router y utilidades (runner + resumen).
    - Evidencia mínima: ejecutado `python3 -m ada.cli.main "cycle"` y se observó:
      - `[read] files=1758`
      - `[write] wrote ada/cli/cycle_test/latest.json`
      - `[debug] failure captured as expected (returncode=2)`
    - Nota de siguiente paso: definir el formato final de evidencia (campos obligatorios) y automatizar un “read -> write -> run -> debug” reproducible desde una subcarpeta de prueba.
  - [2026-03-19] HIT5: Comando real `create file <path>`.
    - Resultado verificable: se implementó `create file` en el router y operaciones reales de filesystem.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "create file test.txt"`
      - `test.txt` existe en el repo después del comando.
    - Nota de siguiente paso: extender a más variantes (ej. `create dir`, `create file --force`) con criterios simples.
  - [2026-03-19] HIT6: Comando real `fix error`.
    - Resultado verificable: se implementó un fix determinista basado en `error.txt`.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "fix error"`
      - `error.txt` se creó/actualizó y contiene `FIXED: example`.
    - Nota de siguiente paso: hacer que `fix` acepte instrucciones con archivo objetivo (sin complejidad extra).
  - [2026-03-19] HIT7: Mini E2E (analyze -> create -> fix).
    - Resultado verificable: los 3 comandos del CLI funcionan en secuencia y modifican archivos en el workspace.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "analyze project"` (salida con `Summary`/`Number of files`)
      - ejecutado `python3 -m ada.cli.main "create file test_ada.txt"` -> crea `test_ada.txt`
      - ejecutado `python3 -m ada.cli.main "fix error"` -> `error.txt` contiene `FIXED: example`
    - Nota de siguiente paso: refinar parseo de comandos (p.ej. `create file ... --force`) y hacer el output más compacto.
  - [2026-03-19] HIT8: Alias profesional `fix-error` (guion).
    - Resultado verificable: el router reconoce `fix-error` como sinónimo de `fix error`.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "fix-error"` -> `Fixed error in error.txt`
      - ejecutado `python3 -m ada.cli.main "fix error"` -> `Fixed error in error.txt`
    - Nota de siguiente paso: estandarizar el naming (kebab-case) para futuras acciones (`create-file`, etc.).
  - [2026-03-19] HIT9: Tools FS + analyzer conectados (`list files` / `analyze project`).
    - Resultado verificable: `ada/tools/file_tools.py` y `ada/core/code_analyzer.py` habilitan comandos reales.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "list files"` -> imprime archivos del workspace
      - ejecutado `python3 -m ada.cli.main "analyze project"` -> imprime `Project Analysis:` con `Total files` y `Types:`
    - Nota de siguiente paso: recortar/estandarizar el formato de salida de tipos (p.ej. Top-N) si se vuelve ruidoso.
  - [2026-03-19] HIT10: `create file ... with content ...` (creación con contenido).
    - Resultado verificable: el comando crea el archivo con el contenido proporcionado.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "create file test.txt with content hello"`
      - `test.txt` existe y su contenido es `hello`
    - Nota de siguiente paso: soportar comillas/escapado para contenido multilínea o con espacios complejos.
  - [2026-03-19] HIT11: Escritura real via `write_file()` (overwrite + size).
    - Resultado verificable: `create file <name> with content <text>` sobrescribe y reporta tamaño real.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "create file test.txt with content hola mundo"`
      - salida:
        - `File created: test.txt`
        - `Size: 10 bytes`
      - verificado contenido: `hola mundo`
    - Nota de siguiente paso: añadir soporte opcional para rutas y contenido multilínea (p.ej. heredoc/quotes).
  - [2026-03-19] HIT12: `read_file` + `debug_engine` + `fix error <texto>` (debug real).
    - Resultado verificable: el router detecta `fix error File <path> line <n> ...`, lee el archivo real y muestra snippet.
    - Evidencia mínima:
      - ejecutado `python3 -m ada.cli.main "fix error File ada/cli/main.py line 1 NameError: x is not defined"`
      - se imprimió:
        - `== ADA DEBUG ENGINE: analyze_error ==`
        - snippet del archivo con la línea indicada
        - `Proposed fix` (placeholder) y `Apply? (y/n): n (auto-no in this phase)`
    - Nota de siguiente paso: conectar Ollama/LLM en `suggest_fix()` sin romper “debug real” y luego pasar a aplicación bajo aprobación.
  - [2026-03-19] HIT13: PRO FIX con DIFF + confirmación + apply real.
    - Resultado verificable: `fix error <...>` muestra un DIFF unificado, pide confirmación y al aceptar sobreescribe el archivo.
    - Evidencia mínima:
      - se creó `testOpt/test.py` con `print(x)` y falló con `NameError: x is not defined`
      - ejecutado: `printf "y\n" | python3 -m ada.cli.main "fix error File testOpt/test.py line 1 NameError: x is not defined"`
      - se mostró `=== DIFF (unified) ===` con cambio `+x = 0`
      - se aplicó: `Write success: ...` y `Fix applied`
      - `python3 testOpt/test.py` terminó con `exit=0`
    - Nota de siguiente paso: mejorar el heurístico para más tipos de errores y hacer soporte de diff más compacto en archivos grandes.
  - [2026-03-19] HIT14: Ejecución real de comandos vía CLI (`run`/`execute`).
    - Resultado verificable: el router permite `run <command>` y `execute <command>` con confirmación antes de ejecutar.
    - Evidencia mínima:
      - ejecutado `printf "y\n" | python3 -m ada.cli.main "run ls"` -> se listó el workspace
      - ejecutado `printf "y\n" | python3 -m ada.cli.main "run python testOpt/test.py"` -> exit 0
      - ejecutado `printf "y\n" | python3 -m ada.cli.main "execute ls"` -> listó el workspace
    - Nota de siguiente paso: añadir protección extra (whitelist de comandos o limites) y timeout configurable para procesos largos.
  - [2026-03-19] HIT15: `roadmap_engine` implementado (leer ROADMAP + fase + objetivos).
    - Resultado verificable: `ada "roadmap"` y `ada "what next"` funcionan usando texto de `ada/ROADMAP.md`.
    - Evidencia mínima: extracción simple de `FASE <n>` y bullets bajo `OBJETIVOS ACTUALES`.
    - Nota de siguiente paso: refinar parseo cuando haya cambios en formato del ROADMAP.
  - [2026-03-19] HIT16: Comandos `roadmap` y `what next` en el router.
    - Resultado verificable: prints un resumen (fase + objetivos) sin ejecutar acciones.
    - Evidencia mínima:
      - `python3 -m ada.cli.main "roadmap"`
      - `python3 -m ada.cli.main "what next"`
    - Nota de siguiente paso: añadir comando `roadmap --phase` si el formato crece.
  - [2026-03-19] HIT17: `task_planner.suggest_tasks()` implementado (LLM opcional + fallback).
    - Resultado verificable: el planner propone 3-5 tareas alineadas con la fase actual.
    - Evidencia mínima:
      - `python3 -m ada.cli.main "improve yourself"` imprime `Proposed actions:`
    - Nota de siguiente paso: optimizar prompt y esquema (JSON) para mejorar calidad y velocidad.
  - [2026-03-19] HIT18: Memoria de progreso (`ada/memory/progress.md` + `log_progress()`).
    - Resultado verificable: el sistema registra propuestas (append-only).
    - Evidencia mínima: tras `improve yourself`, aparece un nuevo entry en `ada/memory/progress.md`.
    - Nota de siguiente paso: registrar también resultados cuando se ejecuten tareas aprobadas.
  - [2026-03-19] HIT19: Comando `improve yourself` (propuesta sin auto-ejecución).
    - Resultado verificable: lee roadmap, sugiere acciones y NO aplica cambios automáticamente.
    - Evidencia mínima: imprime `Apply this evolution now? (y/n): n (auto-no, by rule)`.
    - Nota de siguiente paso: cuando se implemente “aplicar”, hacerlo tras confirmación explícita y con diff.
  - [2026-03-19] HIT20: `what should I build next` llama al `task_planner` (no solo muestra goals).
    - Resultado verificable: imprime 3–5 `Proposed actions:` alineadas con la fase actual.
    - Evidencia mínima:
      - `python3 -m ada.cli.main "what should I build next"`
    - Nota de siguiente paso: unificar nomenclatura (`what next` vs `what should...`) y estandarizar el formato de salida.
  - [2026-03-19] HIT21: Business engine (oportunidades + ranking + microproductos + plan).
    - Resultado verificable: comandos:
      - `python3 -m ada.cli.main "find business opportunities"`
      - `python3 -m ada.cli.main "generate product ideas"`
      - `python3 -m ada.cli.main "what can we sell"`
      - `python3 -m ada.cli.main "create a business plan"`
    - Evidencia mínima:
      - imprime oportunidades rankeadas con score/speed/difficulty/revenue/alignment
      - imprime microproductos sugeridos
      - genera plan por pasos con opción de aprobación humana (sin ejecutar cambios)
    - Nota de siguiente paso: convertir la propuesta del plan en tareas concretas tipo “build/test” y registrar progreso en `ada/memory/progress.md`.
  - [2026-03-19] HIT22: Refactor frontend web-admin (incremental).
    - Resultado verificable:
      - Se deshabilitaron secciones que dependían de endpoints no soportados (`/api/balance`, `/api/events`, `/api/projects/preview/*`) y se removió el tab `Results` roto.
      - Se creó `web-admin/frontend/src/api/client.js` para manejo de errores consistente.
      - Se extrajeron componentes: `ChatPane`, `FileExplorer`, `CodeViewer`, `AgentMarketPage`, `SystemMonitorPage`.
      - Se redujo polling (sin balance/events) y se agregó pestaña `Roadmap` con `RoadmapGoalsView`.
      - Se verificó compilación ejecutando `npm run build` en `web-admin/frontend`.
    - Evidencia mínima: `vite build` completó sin errores.
    - Nota de siguiente paso: migración incremental adicional (más componentes + API endpoints) y limpieza del código muerto en `App.jsx`.
  - [2026-03-19] HIT23: Phase 2 frontend cleanup (dead code + fallbacks).
    - Resultado verificable:
      - Se eliminó código muerto/unreachable de `web-admin/frontend/src/App.jsx` (ramas agent_market/system_monitor).
      - Se actualizó `SystemMonitorPage` para manejar fallos del endpoint con fallback UI (`systemMonitor.error`).
      - Se mantuvo refactor incremental (sin reescritura total).
    - Evidencia mínima:
      - `npm run build` en `web-admin/frontend` finaliza OK.
    - Nota de siguiente paso: pruebas manuales mínimas en UI (dashboard -> Developer Lab -> chat -> file explorer -> System Monitor -> Agent Market -> Roadmap).
  - [2026-03-19] HIT24: ADA Front v2 (estructura modular + rutas reales en /v2).
    - Resultado verificable:
      - Se creó una nueva estructura v2 (api/components/pages/hooks) sin reescribir el frontend viejo.
      - Se agregó routing real con `react-router-dom` para:
        - `/v2` (Home)
        - `/v2/developer`
        - `/v2/business`
        - `/v2/research`
        - `/v2/roadmap`
        - `/v2/monitor`
      - Convivencia: `main.jsx` renderiza App v2 solo si la URL empieza por `/v2`, si no mantiene el App actual.
      - Roadmap/Goals es first-class en v2 y lee `ada/ROADMAP.md` vía `/api/fs/read`.
    - Evidencia mínima:
      - `npm run build` en `web-admin/frontend` compila OK.
    - Nota de siguiente paso:
      - Migrar piezas estables del App viejo hacia v2 (sin borrar el viejo hasta confirmar).
      - Añadir “activity summary” desde `ada/memory/progress.md` y /o `ROADMAP_Registros.md` en Home v2.
  - [2026-03-19] HIT25: ADA Front v2 “operational workspace” (fase 1).
    - Resultado verificable:
      - Top status bar ahora muestra: project, workspace, ADA status (idle/running/waiting approval), execution mode y model (best-effort).
      - Developer workspace ahora es task-oriented: quick actions crean tasks visibles + approvals pendientes.
      - Se añadió un “Recent activity” dock leyendo `ada/memory/progress.md` (fallback si no existe).
      - Se mantuvo UI limpia y ligera (sin ejecutar acciones automáticamente aún).
    - Evidencia mínima:
      - `npm run build` en `web-admin/frontend` compila OK.
    - Nota de siguiente paso:
      - Conectar approvals a ejecución real (run command / fs write / apply patch) manteniendo diff + confirmación.
- Checklist de lo que falta para cerrar la FASE 1:
  - Definir comandos/outputs esperados para `leer proyecto`, `modificar archivos`, `ejecutar comandos`, `debug básico`.
  - Registrar una ejecución de “ciclo completo” (read -> write -> run -> debug) con evidencia.

### FASE 2 — META + MEMORIA

- Estado: PENDIENTE DE CIERRE
- Hitos (append-only):
  - [2026-03-16] HIT0: ROADMAP preparado para FASE 2 con objetivos (memoria persistente, registro de acciones, evaluación).
    - Resultado verificable: sección `OBJETIVOS FUTUROS` dentro de este mismo archivo.
    - Evidencia mínima: aparecen bullets de memoria, historial de acciones y evaluación simple.
    - Nota de siguiente paso: convertir cada bullet en criterio verificable y registrar evidencia real cuando se cumpla.
- Checklist de lo que falta para cerrar la FASE 2:
  - Identificar dónde se persiste la memoria (DB/archivos) y cómo se valida.
  - Definir formato de “historial de acciones” y cómo se demuestra.
  - Definir métrica simple de evaluación y su prueba reproducible.

### FASE 3 — AUTO-CONSTRUCCIÓN

- Estado: PENDIENTE DE CIERRE
- Hitos (append-only):
  - [2026-03-16] HIT0: ROADMAP preparado para self-improvement por fases (detectar carencias, proponer mejoras, implementar con confirmación).
    - Resultado verificable: bullets de FASE 3 en `OBJETIVOS FUTUROS`.
    - Evidencia mínima: aparece la intención de propuestas con confirmación.
    - Nota de siguiente paso: exigir evidencia de “auto-construcción” (antes/después) con confirmación humana.
- Checklist de lo que falta para cerrar la FASE 3:
  - Confirmar flujo: detectar carencias -> plan -> propuesta -> confirmación -> implementación.
  - Registrar al menos 1 caso real con evidencia de cambio y rollback si aplica.

### FASE 4 — HÍBRIDO (escala)

- Estado: PENDIENTE DE CIERRE
- Hitos (append-only):
  - [2026-03-16] HIT0: ROADMAP preparado para multi-agente y arquitectura distribuida (microservicios, scheduler, autonomía completa).
    - Resultado verificable: bullets de FASE 4 en `OBJETIVOS FUTUROS`.
    - Evidencia mínima: aparecen microservicios, scheduler background y multi-agente.
    - Nota de siguiente paso: convertir “escala” en criterios medibles (número de agentes, colas, latencias, etc.) y registrar evidencia.
- Checklist de lo que falta para cerrar la FASE 4:
  - Definir qué significa “autonomía completa” (límites, seguridad, intervención humana mínima).
  - Registrar evidencia de ejecución distribuida (contenedores/servicios/colas).

---

## TRACE DE ETAPAS (APPEND-ONLY) — HIT26

- [2026-03-16] **HIT26: UI approvals conectadas a ejecución real (backend controlado)**.
  - **Qué se hizo**:
    - Se añadió endpoint controlado `POST /api/approve/execute` en `web-admin/src/web_admin_api.py` para ejecutar acciones aprobadas desde la UI.
    - Se conectó ADA Front v2 (`DeveloperWorkspace` + `PendingApprovalsPanel`) para aprobar y ejecutar **de verdad** vía backend, mostrando resultado verificable o error.
  - **Orden implementado**: `create_file` → `run_command` → `apply_patch`.
  - **Reglas de seguridad**:
    - La UI **no ejecuta directo**: siempre llama al backend.
    - `run_command` usa allowlist (`ADA_UI_RUN_ALLOWLIST`) + timeout (`ADA_UI_RUN_TIMEOUT`).
    - Escritura/patch requieren `ENABLE_AGENT_FS=1`.
  - **Resultado verificable**:
    - Build frontend OK (`vite build`) y en UI aparecen approvals con estado + resultado/error tras ejecutar.

---

## TRACE DE ETAPAS (APPEND-ONLY) — HIT27

- [2026-03-20] **HIT27: ADA v1 — poda de compose, agent-core y frontend; flujo plan → ejecución; demo landing documentada**.
  - **Qué se hizo**:
    - `docker-compose.yml` recortado al núcleo (postgres, memory_service, agent-core, chat_interface); servicios históricos movidos a `docker-compose.legacy.yml`.
    - `agent-core`: encabezado y prompt de herramientas alineados a desarrollo; convención `dockers/ada-landing-demo/` para demo de landing.
    - Frontend: solo workspace de desarrollo; plan pendiente (`pending_plan`) con **Ejecutar plan** / **Descartar plan**; atajo **Demo: landing ADA (prompt)**; proxy web-admin sin depender de capabilities/monitor/market para el camino v1.
    - Documentación de demo: `docs/DEMO-LANDING-ADA.md`.
  - **Resultado verificable**:
    - `docker compose up -d` levanta solo el núcleo; UI en `http://localhost:8080` con flujo chat → (pending_plan) → execute_plan.
