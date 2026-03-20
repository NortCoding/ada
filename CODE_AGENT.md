# Agente #3 (CODE) - Capacidades y Limitaciones

## Propósito
El **Agente #3 (CODE)** está diseñado como un ingeniero de software autónomo integrado en el ecosistema A.D.A. Su objetivo es recibir requerimientos (por ejemplo, "Crear una aplicación React") y traducirlos en planes de implementación técnicos, generando propuestas que se ejecuten de manera segura en el entorno local.

## Capacidades
- **Ejecución en Sandbox**: El Agente #3 tiene un entorno aislado en el contenedor de `task-runner` donde puede ejecutar comandos `bash` y correr scripts.
- **Herramientas Disponibles**: Puede utilizar herramientas como `git`, `curl`, `npm`, `node`, `python3` e interactuar con el ecosistema de Node.js y Python para configurar proyectos de desarrollo.
- **Validación del Entorno**: Todas sus operaciones de archivo están contenidas estrictamente en el directorio de montaje `/workspace`, impidiendo de esta manera escrituras e interacciones maliciosas o erróneas en el sistema base de ADA.
- **Mecanismo de Propuestas**: Las acciones generadas por sugerencias de código o CLI (`RUN_COMMAND`) se transforman en entidades de tipo `Proposal` (tipo `bash_command`), que fluyen de manera asíncrona por el `decision-engine` y el `policy-engine` de ADA.

## Limitaciones
- **Contención Geográfica Segura**: Cualquier instrucción para manipular archivos (por ejemplo `rm -rf /` o modificar configuraciones externas `/etc/passwd`) fuera del espacio `/workspace` es bloqueada estáticamente por reglas de denegación predefinidas y verificaciones del `policy-engine`.
- **Aprobación Obligatoria**: Por defecto, comandos de alta sensibilidad o que superen los umbrales de riesgo requerirán el token de un usuario humano para propagarse al contenedor `task-runner`.
- **Interacciones Reactivas**: El contenedor del agente CODE carece de entorno gráfico con lo cual no puede testear visualmente cambios a interfaces de usuario completas o navegar como un navegador per-se; requiere orquestación adicional para este propósito.
- **Memoria Temporal**: Cualquier paquete global instalado con `npm -g` o `pip` se pierde si el contenedor de `task-runner` se destruye y se vuelve a crear sin incluirse explícitamente en su respectivo `Dockerfile`.
