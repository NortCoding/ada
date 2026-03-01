# A.D.A en modo producción — Primeros ingresos

Cuando ADA está en **modo producción** (`ADA_ENV=production`), el sistema está configurado para operar y generar los primeros ingresos. Este documento describe cómo activarlo y los pasos siguientes.

---

## 1. Activar modo producción

- En **ada_resources.env** (o en el env que use agent-core) pon:
  ```bash
  ADA_ENV=production
  ```
- En **docker-compose** ya está definido `ADA_ENV: ${ADA_ENV:-production}`; si no pones nada en `.env`, por defecto será producción.
- Reinicia agent-core para que lea la variable:
  ```bash
  docker compose up -d agent-core
  ```
- Comprueba: `curl -s http://localhost:3001/health` debe devolver `"mode": "production"`.

---

## 2. Arrancar el flujo de primeros ingresos

Un solo paso prepara plan y oferta:

```bash
curl -X POST http://localhost:3001/autonomous/start_production
```

Ese endpoint:
- **Si no hay plan:** crea el primer plan (objetivo, nicho, pasos) con Ollama y lo guarda en memoria.
- **Si no hay primera oferta:** crea la oferta (título, descripción, precio sugerido) y la guarda en memoria.

La respuesta incluye `plan`, `offer` y `next_steps` con los pasos que debe hacer el humano.

También puedes hacerlo desde la **web-admin** (si tienes un botón que llame a este endpoint) o en dos llamadas:
- `POST /autonomous/first_plan` — crear plan.
- `POST /autonomous/create_first_offer` — crear primera oferta.

---

## 3. Pasos para que llegue el primer ingreso

| Paso | Quién | Acción |
|------|--------|--------|
| 1 | Humano | **Cuenta en Gumroad o Ko-fi:** registrar con el correo de ADA (`ADA_EMAIL`). Enlaces: `GET /api/autonomous/register_platforms`. Opcional: usar `signup-helper` para registro asistido. |
| 2 | Humano | **Publicar la oferta:** en la plataforma, crear el producto con el título, descripción y precio que ADA guardó en memoria (first_offer). Copiar el enlace de la oferta. |
| 3 | Humano / sistema | **Registrar el ingreso:** cuando haya una venta, registrar el ingreso en el financial-ledger (POST tipo `income`) o desde web-admin. Así ADA tiene ingresos y puede seguir creciendo. |

---

## 4. Resumen

- **Modo producción:** `ADA_ENV=production` en el entorno de agent-core.
- **Inicio del flujo:** `POST /autonomous/start_production` (crea plan y oferta si no existen).
- **Siguiente:** cuenta en plataforma → publicar oferta → registrar ingreso en el ledger.

Con eso ADA queda en modo producción y con todo listo para generar los primeros ingresos; el humano completa los pasos de cuenta, publicación y registro del ingreso.
