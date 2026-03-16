# Mejoras posibles para la memoria de ADA

La memoria actual es un almacén clave–valor en PostgreSQL (memory-db → `ada_memory.context`). Estas son mejoras razonables y consejos prácticos.

---

## 0. **Velocidad y no depender solo de la base de datos**

**Problema:** Cada mensaje de chat pide a memory-db (y al ledger) el contexto (plan, recursos, balance). Si todo va siempre a PostgreSQL, la latencia se nota y ADA depende al 100% de que memory-db responda en cada request.

**Soluciones (de menor a mayor esfuerzo):**

| Enfoque | Qué hace | Ventaja |
|--------|----------|---------|
| **Caché en agent-core (implementado)** | El resultado de `get_many` (plan + recursos) y el balance se guardan en memoria en agent-core con TTL (por defecto 20 s). Varios mensajes seguidos o rondas de herramientas reutilizan el mismo contexto sin llamar a memory-db/ledger. Al escribir en memoria (first_plan, weekly_plan, requested_hardware_resources, clear_plan, reset_all) se invalida la caché. | Chat más rápido; menos carga en memory-db y PostgreSQL. Variable opcional: `ADA_MEMORY_CACHE_TTL_SEC` (segundos). |
| **Caché en memory-db** | Dentro de memory-db, un diccionario en memoria con TTL para las claves más leídas (first_plan, weekly_plan, first_offer). En cada GET/get_many se mira primero la caché; si no está, se lee de PostgreSQL y se guarda en caché. En cada SET se invalida esa clave. | Menos lecturas a PostgreSQL; respuestas más rápidas sin añadir Redis. |
| **Redis como capa** | Un Redis delante de memory-db: las lecturas van a Redis (muy rápido); si falta, se lee de PostgreSQL y se escribe en Redis. Escrituras: escribir en PostgreSQL e invalidar/actualizar Redis. | Máxima velocidad de lectura y la base de datos solo se usa como persistencia; más componentes que mantener. |
| **Memoria híbrida (archivos + DB)** | Para datos que cambian poco (plan actual, oferta), mantener una copia en archivos (ej. `data/plan.json`) y leer de ahí en caliente; memory-db/PostgreSQL como fuente de verdad y para el resto de claves. | Menos dependencia de la DB en cada request para ese subconjunto; requiere sincronizar archivo y DB al escribir. |

**Recomendación:** Con la **caché en agent-core** ya activa, el chat debería ir más rápido en conversaciones seguidas. Si más adelante quieres aún menos dependencia de la DB o más velocidad, añadir caché en memory-db o Redis es el siguiente paso.

---

## 1. **Respaldo e inspección por archivos (recomendado)**

**Problema:** Todo está solo en la base de datos; no hay copia en archivos para backup, revisión o edición manual.

**Solución:** Exportar e importar memoria a archivos JSON.

- **Exportar:** volcar todas las claves a un directorio (p. ej. `memory_backup/`) con un JSON por clave o un solo `memory_export.json`. Útil para backup, git (opcional) y ver qué tiene ADA “en la cabeza”.
- **Importar:** restaurar desde esos archivos (restore tras fallo o carga inicial).

**Implementado en el proyecto:**
- **memory-db:** `GET /export` devuelve todo el contenido de la memoria en un único JSON (claves, valores y `updated_at`).
- **Scripts:** `./scripts/memory_export_import.sh export [directorio]` vuelca la memoria a archivos (por defecto `memory_backup/`). `./scripts/memory_export_import.sh import <archivo.json>` restaura desde un export. El directorio `memory_backup/` está en `.gitignore`.

**Ventaja:** Sigue usando memory-db y PostgreSQL como fuente de verdad; los archivos son copia de seguridad y soporte.

---

## 2. **Historial reciente de chat en memoria**

**Problema:** El historial de conversación lo lleva quien llama (web, Telegram). Si el cliente no envía historial o se pierde, ADA “olvida” lo que se habló.

**Solución:** Guardar en memory-db las últimas N vueltas de chat (p. ej. clave `recent_chat` con una lista de `{role, content}`), con tope de tamaño (ej. últimos 10 intercambios o 4000 tokens). En cada chat, agent-core podría:
- leer `recent_chat` de memoria,
- inyectarlo en el contexto (o en los mensajes),
- al responder, actualizar `recent_chat` añadiendo user + assistant y recortando si pasa del límite.

**Consejo:** Empezar con N pequeño (5–10 mensajes) para no inflar el prompt ni el coste.

---

## 3. **Convención de claves y esquemas**

**Problema:** Las claves son “planas” (`first_plan`, `learning_xxx`, `plan_step_1_done`). A largo plazo puede costar saber qué es cada cosa y cómo se relaciona.

**Solución:**
- **Prefijos claros:** `plan.first`, `plan.weekly`, `offer.first`, `learning.<task>`, `state.gumroad`, `state.plan_step_1_done`. Así es más fácil listar por “todo lo de plan” o “todo lo de learning”.
- **Documentar el esquema** de cada clave (en este doc o en código): por ejemplo `plan.first` = `{ goal, niche, steps[], next_review, created_at?, source? }`. Así se evitan valores inconsistentes.

No hace falta cambiar memory-db; es convención al escribir/leer desde agent-core.

---

## 4. **Limpieza de aprendizajes antiguos**

**Problema:** Las claves `learning_*` pueden acumularse sin límite.

**Solución:**
- Listar keys con prefijo `learning_` (memory-db ya tiene `GET /keys?prefix=learning_`).
- Definir política: por ejemplo “mantener solo las 50 más recientes” o “borrar las que tengan más de 30 días” (si guardas `created_at` en el value).
- Añadir en agent-core un endpoint o script periódico que llame a memory-db, liste `learning_*`, y borre las que excedan el límite (habría que añadir `DELETE /delete/{key}` en memory-db).

---

## 5. **Leer varias claves a la vez**

**Problema:** Para armar el contexto del chat hoy se hace un GET por cada clave (p. ej. `first_plan`, `weekly_plan`). Funciona, pero con más claves puede ser incómodo.

**Solución:** En memory-db añadir algo como `GET /get_many?keys=first_plan,weekly_plan` que devuelva `{ "first_plan": {...}, "weekly_plan": {...} }`. Así agent-core hace una sola petición para el bloque de contexto de memoria.

---

## 6. **Memoria “solo archivos” (alternativa)**

Si quisieras que parte de la memoria viva **solo en archivos** (sin PostgreSQL para eso):

- **Pros:** Edición manual, control con git, backup trivial, sin depender de memory-db para ese dato.
- **Contras:** Concurrencia (quién escribe cuándo), no hay transacciones, y habría que decidir qué va a archivos (p. ej. solo plan y primera oferta) y qué sigue en DB (recursos, learning, pasos).

**Enfoque híbrido razonable:** Lo crítico y estable (plan actual, primera oferta) podría leerse/guardarse también en archivos (p. ej. `data/memory/plan_current.json`) como copia o incluso como fuente de verdad para ese subconjunto; el resto seguir en memory-db. Requiere un poco de lógica en agent-core para “leer de archivo si existe, si no de memory-db” y mantener ambos sincronizados cuando se actualice.

---

## Resumen de prioridades

| Prioridad | Mejora | Esfuerzo |
|-----------|--------|----------|
| Alta | **Caché en agent-core** (velocidad, menos dependencia de DB en cada mensaje) | **Hecho:** TTL 20 s, invalidación al escribir plan/recursos |
| Alta | Export/import a archivos (backup e inspección) | Bajo: script + opcional endpoint |
| Media | Historial reciente de chat en memoria | Medio: lógica en agent-core + una clave |
| Media | GET /get_many en memory-db | Bajo (ya existe) |
| Media | Caché en memory-db o Redis para lecturas | Medio |
| Baja | Convención de prefijos y documentar esquemas | Bajo |
| Baja | Limpieza de learning_* (y DELETE en memory-db) | Bajo–medio |
| Opcional | Memoria híbrida archivos + DB para plan/oferta | Medio |

Si quieres, el siguiente paso puede ser implementar solo el export/import a archivos y el endpoint `GET /export` en memory-db; el resto se puede ir haciendo poco a poco.
