# Propuesta: ADA como agente constructor de webs con imágenes de internet

Objetivo: permitir que ADA busque imágenes reales en internet e inserte URLs en el diseño generado, **sin fingir éxito** — si no hay imagen real, usar placeholders de forma explícita.

---

## 1. Flujo de proveedores de imágenes

### Orden de intento (una cadena por petición, sin “scraping” aleatorio)

```
search_images(query, count)
    │
    ├─► ¿PEXELS_API_KEY?  → Pexels API (GET /v1/search?query=…)
    │       │
    │       └─► Si devuelve ≥1 foto → normalizar a { title, url, source: "pexels" } y RETORNAR
    │
    ├─► ¿UNSPLASH_ACCESS_KEY?  → Unsplash API (GET /search/photos?query=…)
    │       │
    │       └─► Si devuelve ≥1 foto → URLs directas usables, source: "unsplash" → RETORNAR
    │
    └─► Fallback obligatorio: Picsum
            → Sin API key, determinista: e.g. https://picsum.photos/800/600?random=N
            → source: "picsum"
            → RETORNAR (nunca fallar; siempre lista de N URLs)
```

**Reglas:**

- **Un solo fallback chain por llamada**: primero Pexels, si no hay key o no hay resultados → Unsplash; si no hay key o no hay resultados → Picsum.
- **No mezclar fuentes en una misma respuesta** para una misma búsqueda: o todo de un provider o todo Picsum (para no confundir “reales vs placeholder”).
- **Límite por sección**: `count` acotado (ej. 3–5 por sección); el llamador (planificador) no pedirá más del máximo.

Resultado de `search_images` siempre es una lista de 0..count ítems; cada ítem tiene `title`, `url`, `source`. Si `source == "picsum"` → es placeholder; si `source in ("pexels","unsplash")` → imagen real de búsqueda.

---

## 2. Lógica de fallback (nunca fingir éxito)

### Criterios “no hay imagen real”

- No hay API key para ese provider.
- Llamada al API falla (red, 4xx/5xx).
- API devuelve 0 resultados para la query.

### Comportamiento

| Situación                         | Acción                                                                 |
|----------------------------------|------------------------------------------------------------------------|
| Pexels OK con ≥1 resultado       | Devolver esas URLs, `source: "pexels"`. No llamar a Unsplash/Picsum.  |
| Pexels sin key / error / 0 hits  | Pasar a Unsplash.                                                      |
| Unsplash OK con ≥1 resultado    | Devolver esas URLs, `source: "unsplash"`. No usar Picsum.             |
| Unsplash sin key / error / 0 hits| **Fallback a Picsum**: generar N URLs placeholder, `source: "picsum"`. |
| Sin ninguna key                  | No llamar a Pexels ni Unsplash; ir directo a Picsum.                   |

- **Nunca** devolver una URL inventada o un ítem sin `url` válida.
- **Siempre** devolver exactamente `count` ítems cuando se use Picsum (rellenar con placeholders).
- En el resultado final del plan/website, **marcar explícitamente**:
  - `asset_mode: "external_image_url"` + `source: "pexels"|"unsplash"` → imagen real.
  - `asset_mode: "placeholder_image"` o `source: "picsum"` → placeholder.

Así el “éxito” o “placeholder” es visible en datos y en el reporte.

---

## 3. Cómo el planificador de website asigna imágenes a secciones

### 3.1 Estructura del plan de website (con tareas de imagen)

El “website plan” incluirá secciones y, para cada sección que requiera imágenes, una **tarea de imagen** con:

- `section_id`: ej. `hero`, `gallery`, `ambiance`, `contact`.
- `section_label`: texto corto para logs/reporte (ej. "Hero", "Galería comida", "Ambiente").
- `image_query`: query de búsqueda (ej. "restaurant hero food", "restaurant interior").
- `max_images`: 1 para hero, 3–5 para galerías (respetando límites de Fase 7).
- `image_tasks`: resultado de `search_images(query, max_images)`:
  - lista de `{ title, url, source }`.
  - si todo es Picsum → la sección queda con `asset_mode: "placeholder_image"` y se indica en el resumen.

### 3.2 Flujo en el planificador

1. **Detectar secciones que necesitan imágenes**  
   A partir del tipo de sitio (ej. restaurante), definir secciones estándar:
   - Hero → 1 imagen.
   - Galería (comida/menú) → 3–5 imágenes.
   - Ambiente/interior → 1–2 imágenes.
   - Contacto/reservas → 0–1 imagen (opcional).

2. **Generar `image_query` por sección**  
   Por sección, un string de búsqueda (puede venir de template o de LLM):
   - hero → `"restaurant hero"` o `"restaurant food banner"`;
   - gallery → `"restaurant food dish"`;
   - ambiance → `"restaurant interior"`.

3. **Ejecutar búsqueda por sección (una chain por sección)**  
   Para cada sección:
   - `results = search_images(image_query, count=max_images)`.
   - Asignar `section.images = results`.
   - Marcar `section.asset_mode = "external_image_url"` si algún ítem tiene `source` pexels/unsplash; si todos son `picsum`, `section.asset_mode = "placeholder_image"`.

4. **Almacenar en el plan**  
   - En el plan/task: para cada sección, guardar `images` (lista de `{ title, url, source }`) y `asset_mode`.
   - Así la generación HTML/CSS solo lee el plan y coloca `url` en `img.src` o `background-image`.

5. **Reporte final**  
   - Listar secciones con “imágenes reales” (source pexels/unsplash) vs “solo placeholders” (source picsum), para no fingir éxito.

### 3.3 Ejemplo de estructura en el plan (restaurante)

```json
{
  "sections": [
    {
      "id": "hero",
      "label": "Hero",
      "image_query": "restaurant hero food",
      "max_images": 1,
      "images": [
        { "title": "Restaurant hero", "url": "https://…", "source": "pexels" }
      ],
      "asset_mode": "external_image_url"
    },
    {
      "id": "gallery",
      "label": "Galería comida",
      "image_query": "restaurant food dish",
      "max_images": 4,
      "images": [
        { "title": "Placeholder 1", "url": "https://picsum.photos/800/600?random=1", "source": "picsum" },
        …
      ],
      "asset_mode": "placeholder_image"
    }
  ],
  "image_summary": {
    "real": ["hero"],
    "placeholders": ["gallery", "ambiance"]
  }
}
```

---

## 4. Resumen de decisiones

| Tema              | Decisión                                                                 |
|-------------------|--------------------------------------------------------------------------|
| Orden providers   | Pexels → Unsplash → Picsum; una sola cadena por query.                   |
| Fallback          | Si no hay key o no hay resultados → siguiente; al final siempre Picsum.  |
| No fingir éxito   | Siempre `source` en cada ítem; `asset_mode` y `image_summary` en el plan. |
| Asignación imágenes | Plan con `sections[].image_query`, `max_images`, `images`, `asset_mode`. |
| Límites           | 3–5 imágenes por sección; 1 fallback chain por query.                   |
| Config            | `PEXELS_API_KEY`, `UNSPLASH_ACCESS_KEY`; si no hay ninguna → solo Picsum.|

Cuando tengas esta propuesta validada, el siguiente paso es implementar en este orden: **Phase 1 (image_search_engine) → Phase 2 (providers) → Phase 8 (config)** y luego integrar con el website planner (Phases 3–7 y 9) usando esta misma estructura de plan y flujo.
