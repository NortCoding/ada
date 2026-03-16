# ADA como CEO con agentes que resuelven problemas

Visión: ADA es el **CEO** que coordina y delega en **agentes especialistas** para resolver problemas concretos.

---

## 1. Idea general

- **ADA (CEO):** La cara ante el usuario. Toma decisiones, prioriza, explica el plan y las acciones. Cuando un problema es técnico o de un dominio concreto, **delega** en un agente especialista.
- **Agentes especialistas:** Ayudan a resolver problemas en su área (finanzas, código, marketing, visión de imágenes, etc.). No hablan directamente con el usuario; devuelven resultado a ADA y ADA lo integra en su respuesta.

El usuario **siempre habla con ADA**. ADA decide en cada mensaje si responde ella misma o si pide ayuda a uno o varios especialistas y luego resume o actúa.

---

## 2. Flujo de una conversación

1. **Usuario** escribe a ADA (ej. “¿Cómo van las finanzas?” o “Quiero que revises este código”).
2. **ADA (CEO)** analiza el mensaje:
   - Si puede responder con lo que ya sabe (plan, memoria, ledger) → responde directamente.
   - Si necesita análisis profundo de finanzas → **delega en el agente Finanzas**; recibe la respuesta y la integra en su mensaje al usuario.
   - Si necesita revisar código o proponer cambios → **delega en el agente Código**; recibe sugerencias y las presenta o ejecuta.
   - Si el usuario envía una imagen → puede usar **visión** (ya existe) o delegar en un especialista “visión” para descripción detallada.
3. **ADA** responde al usuario con una respuesta única: su criterio + lo que le hayan devuelto los especialistas (sin explicar internamente “le pregunté a Finanzas”, a no ser que quieras que sea transparente).

---

## 3. Cómo modelar a los especialistas (sin nuevos servicios)

Para no multiplicar contenedores al principio:

- **Cada especialista = un prompt de sistema distinto** en el mismo agent-core.
- ADA (el “cerebro” principal) y los especialistas comparten el mismo LLM (Ollama/Gemini) pero con **roles** distintos en el prompt:
  - **Prompt CEO:** “Eres ADA, el CEO. Puedes delegar en especialistas. Cuando el mensaje sea de finanzas, genera un mensaje interno para el especialista Finanzas y usa su respuesta para responder al usuario.”
- **Implementación en dos pasos:**
  1. **Paso 1 (delegación interna):** En un mismo turno, agent-core hace hasta dos llamadas al LLM:
     - Primera llamada: con prompt CEO, el modelo devuelve o bien “respuesta directa” o bien “delegar a: [finance|code|marketing|…]” y un “mensaje para el especialista”.
     - Si hay delegación: segunda llamada con el prompt del especialista elegido y el mensaje; se obtiene la respuesta del especialista.
     - Se inyecta esa respuesta en el contexto del CEO y se hace una tercera llamada (o se construye la respuesta final) para que ADA responda al usuario integrando el resultado.
  2. **Paso 2 (opcional):** Más adelante, si un especialista crece mucho, se puede sacar a un microservicio que agent-core llame por HTTP.

Así ADA actúa como CEO y “tiene” varios agentes que ayudan a resolver problemas, sin nuevos servicios al inicio.

---

## 4. Lista de agentes que pueden ayudar

| Especialista | Función | Ejemplo de cuándo delega ADA |
|--------------|---------|------------------------------|
| **Finanzas** | Balance, ledger, ingresos/gastos, prioridades de gasto, proyecciones | “¿Cómo van las cuentas?”, “¿Podemos permitirnos X?” |
| **Código** | Leer/escribir archivos del proyecto, proponer cambios, scripts, integraciones | “Revisa este archivo”, “Añade un endpoint para X” |
| **Marketing** | Ofertas, copy, Gumroad/Ko-fi, mensajes de venta, tráfico | “Redacta la descripción de la oferta”, “¿Cómo promociono?” |
| **Visión** | Describir y analizar imágenes (ya existe en parte con llava/Gemini) | Usuario envía captura o diagrama; ADA pide descripción o resumen |
| **Plan** | Descomponer objetivos en pasos, revisar el plan actual, sugerir siguiente paso | “¿Qué hacemos esta semana?”, “Ajusta el plan” |

Cada uno tiene un **prompt de sistema** que define su rol y qué herramientas usa (ledger, memory, READ_FILE, etc.).

---

## 5. Resumen para implementar

1. **Definir en agent-core** los prompts de cada especialista (finance, code, marketing, vision, plan) y un **prompt CEO** que indique cuándo delegar y cómo usar la respuesta.
2. **En el flujo de `/chat`:**  
   - Si se quiere “ADA como CEO” siempre: una primera llamada con prompt CEO; si el modelo devuelve delegación, una segunda llamada al especialista; luego se construye la respuesta final al usuario.  
   - Opción más simple al inicio: un parámetro opcional `delegate_to` (ej. el usuario o el frontend elige “preguntar a Finanzas”) y entonces agent-core hace una sola llamada con el prompt del especialista y ADA “presenta” esa respuesta (sin decisión automática de delegación).
3. **En la interfaz:** El usuario sigue hablando solo con ADA. Opcional: un selector “ADA (CEO)” vs “Hablar con Finanzas / Código /…” para forzar delegación cuando se quiera.

Con esto, ADA queda como **CEO** y tiene **agentes que ayudan a resolver problemas** bajo su coordinación.
