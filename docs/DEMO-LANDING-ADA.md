# Demo ADA v1 — Landing desde una idea

## Objetivo

Crear una landing estática **en disco** bajo el volumen de proyectos (`dockers/` en el explorador del panel), sin nuevos servicios.

## Arranque

```bash
docker compose up -d
```

Interfaz: `http://localhost:8080` → workspace de desarrollo.

## Flujo

1. Pulsa **Demo: landing ADA (prompt)** o escribe en el chat una variante de:
   - crear `dockers/ada-landing-demo/index.html` y `styles.css`
   - usar `WRITE_FILE:` … `END_FILE` por archivo
2. Si la respuesta incluye `status: pending_plan`:
   - revisa el plan en el panel derecho
   - **Ejecutar plan** (o **Descartar plan**)
3. En el explorador, abre `ada-landing-demo/index.html` y comprueba el contenido.

## Evidencia

- Resultado del plan en el chat (lecturas/escrituras, salida de comandos si los hubo).
- Archivos visibles en el explorador bajo `dockers/ada-landing-demo/`.

## Nota

Para “ver en navegador” como URL propia hace falta un servidor estático o abrir el archivo desde el host; ADA v1 prioriza **archivos reales + evidencia**, no un hosting automático adicional.
