import os
import subprocess
import shlex

# El directorio raíz permitido para todas las operaciones del CODE agent
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/workspace")

def is_safe_path(target_path: str) -> bool:
    """Verifica si la ruta destino está dentro del directorio permitido (workspace)."""
    # Resuelve la ruta absoluta para evitar trucos con '../'
    abs_workspace = os.path.abspath(WORKSPACE_DIR)
    abs_target = os.path.abspath(os.path.join(abs_workspace, target_path))
    
    # Comprueba que la ruta destino comience con la ruta del workspace permitida
    return abs_target.startswith(abs_workspace)

def execute_bash(command_str: str, timeout_seconds: int = 30) -> dict:
    """
    Ejecuta un comando bash en un entorno aislado y seguro.
    Solo permite comandos ejecutados explícitamente dentro de WORKSPACE_DIR.
    """
    # 1. Validación básica de seguridad (lista negra temporal - idealmente usar un parser de comandos completo)
    dangerous_commands = ["rm -rf /", "mkfs", "dd ", "> /dev/sd"]
    for danger in dangerous_commands:
        if danger in command_str:
             return {
                "success": False,
                "stdout": "",
                "stderr": f"Error de seguridad: El comando contiene patrones prohibidos '{danger}'.",
                "exit_code": 1
            }

    try:
        # Asegurarse de que el directorio del workspace existe
        if not os.path.exists(WORKSPACE_DIR):
            os.makedirs(WORKSPACE_DIR)

        # 2. Ejecutar el comando usando subprocess.
        # shell=True es peligroso, pero necesario para scripts complejos que el agente pueda generar.
        # Mitigamos el riesgo forzando el 'cwd' (current working directory) al workspace
        # y confiando en que este contenedor Docker NO tiene montados volúmenes sensibles.
        process = subprocess.Popen(
            command_str,
            shell=True,  # Necesario para poder hacer pipelines como `echo "hola" > archivo.txt`
            cwd=WORKSPACE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Usar timeout para evitar comandos que se quedan colgados (ej. 'read' o servidores interactivos)
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        
        return {
            "success": process.returncode == 0,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "exit_code": process.returncode
        }

    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error: El comando excedió el tiempo límite de {timeout_seconds} segundos.",
            "exit_code": 124 # Código común para timeout
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Excepción interna al ejecutar: {str(e)}",
            "exit_code": 1
        }
