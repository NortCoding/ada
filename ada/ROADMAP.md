# ADA ROADMAP

## META GLOBAL
Construir un agente capaz de ejecutar trabajo real y verificable, empezando por crear y modificar aplicaciones funcionales en un entorno local.

---

## FASE ACTUAL
**FASE 1 — Builder verificable**

---

## OBJETIVO PRINCIPAL ACTUAL

Lograr que ADA cree una aplicación real, la ejecute localmente y pueda modificarla por instrucción.

---

## OBJETIVOS ACTUALES

1. Crear un proyecto real en disco
2. Escribir y modificar archivos reales del proyecto
3. Ejecutar instalación de dependencias
4. Levantar la aplicación en localhost
5. Mostrar evidencia verificable del resultado
6. Aplicar cambios simples por prompt
7. Corregir errores básicos del proyecto

---

## CRITERIO DE ÉXITO DE FASE 1

FASE 1 se considera cerrada solo cuando ADA pueda completar este flujo de punta a punta:

- crear una aplicación nueva
- generar una landing page funcional
- instalar dependencias
- ejecutar el servidor local
- devolver la URL local
- modificar la landing por una instrucción simple
- corregir un error básico si el proyecto falla

---

## PRIMERA DEMO OBLIGATORIA

**Demo 1: Create Landing**

Prompt objetivo:
`crea una landing page para ADA`

Resultado mínimo esperado:
- carpeta del proyecto creada
- archivos reales creados
- dependencias instaladas
- servidor corriendo
- landing visible en localhost
- evidencia guardada

---

## SEGUNDA DEMO OBLIGATORIA

**Demo 2: Edit Landing**

Prompt objetivo:
`agrega sección de precios y cambia la paleta de colores`

Resultado mínimo esperado:
- archivos modificados realmente
- cambios visibles en localhost
- diff o registro del cambio guardado

---

## TERCERA DEMO OBLIGATORIA

**Demo 3: Fix Error**

Prompt objetivo:
`corrige el error del proyecto`

Resultado mínimo esperado:
- ADA detecta el error real
- propone cambio verificable
- aplica fix con aprobación
- proyecto vuelve a correr

---

## OBJETIVOS FUTUROS

### FASE 2 — Memoria útil
- memoria persistente enfocada en proyectos
- registro de acciones ejecutadas
- historial de cambios y resultados
- reutilización de contexto por proyecto

### FASE 3 — Mejora guiada
- propuesta de mejoras sobre el proyecto actual
- generación de tareas concretas
- optimización de código bajo aprobación
- evaluación simple de resultados

### FASE 4 — Escala controlada
- multi-workspace
- múltiples agentes especializados
- servicios separados
- automatización más amplia con límites claros

---

## REGLAS

- No agregar complejidad innecesaria
- Priorizar ejecución real sobre arquitectura
- Todo debe ser verificable
- Cada cambio debe aportar valor visible
- No avanzar a nuevas fases sin cerrar demos reales
- Toda automatización debe dejar evidencia reproducible

---

## ESTADO

- progreso técnico base: medio
- progreso en flujo verificable: bajo
- estabilidad: media-baja
- prioridad absoluta: crear una app real y visible