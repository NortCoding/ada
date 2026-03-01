# Cómo usar Ollama en VS Code / Cursor para escribir y editar código

ADA usa Ollama en el host para el chat. El **mismo Ollama** puede usarse en VS Code (o Cursor) para que la IA cree y edite código directamente en el editor. Todo local, sin coste y sin enviar archivos fuera de tu Mac.

---

## 1. Atajos en el editor (no uses solo el chat lateral)

| Atajo | Uso |
|-------|-----|
| **Cmd + I** (Mac) / **Ctrl + I** (Windows/Linux) | **Inline Edit / Generate**: barra flotante sobre el código. Escribes la instrucción y la IA genera o modifica el código. Ideal para crear archivos nuevos o cambiar fragmentos. |
| **Cmd + L** (Mac) / **Ctrl + L** (Windows/Linux) | **Chat con contexto**: abre el panel de chat. Usa **@file** para que la IA lea un archivo concreto antes de responder. |

**Ejemplo con Cmd + I:**
1. Crea o abre un archivo (ej. `app.py`).
2. Pulsa **Cmd + I**. Aparece la barra flotante.
3. Escribe: *"Crea una API básica con Flask que tenga un endpoint de salud"* y Enter.
4. Revisa el código generado y pulsa **Accept** para guardarlo.

---

## 2. Configuración (Ollama como proveedor)

En la configuración del asistente de IA (Cursor o extensión tipo Continue / Ollama en VS Code):

- **Provider:** `ollama`
- **Model:** `AUTODETECT` o el modelo que quieras (ej. `llama3.2`, `qwen2.5-coder:7b`).

Con **AUTODETECT**, cada modelo que descargues con `ollama pull <modelo>` aparecerá en el desplegable sin tocar más configuración.

La URL de Ollama suele ser `http://localhost:11434` (el mismo que usa ADA en el host).

---

## 3. Modelo recomendado para programación

**Llama 3.2** va muy bien para chat; para **generar y editar código con menos errores** conviene un modelo orientado a código.

En la terminal de tu Mac:

```bash
ollama pull qwen2.5-coder:7b
```

Cuando termine, selecciona `qwen2.5-coder:7b` en el desplegable del modelo (donde antes ponía `llama3.2:latest`). Sigue siendo local y gratuito.

---

## 4. Resumen

| Aspecto | Detalle |
|--------|---------|
| **Coste** | $0 (todo local). |
| **Privacidad** | Los archivos no salen de tu Mac. |
| **Uso** | Crear, editar y explicar código en cualquier lenguaje. |
| **Mismo motor** | Es el mismo Ollama que usa ADA en agent-core; solo cambia la interfaz (VS Code/Cursor en lugar del chat de la Web-Admin). |

---

## 5. Relación con ADA

- **ADA (agent-core)** usa Ollama para el chat del socio y para generar planes/ofertas. No controla el editor de VS Code.
- **Tú**, en tu máquina, usas Ollama en VS Code/Cursor para que la IA te ayude a escribir código (Cmd + I, Cmd + L, @file).
- Si en el futuro se quiere que ADA *escriba archivos* en un workspace (por ejemplo una carpeta del proyecto), haría falta que agent-core o task-runner tuvieran permiso para escribir en esa ruta y, opcionalmente, una extensión o script que sincronice con el editor. Este documento se centra en el uso directo de Ollama en VS Code/Cursor.
