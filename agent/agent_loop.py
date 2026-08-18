"""
agent_loop.py — Bucle principal del agente autónomo.

Flujo por cada tarea:
  1. Tomar screenshot inicial
  2. Llamar al LLM de visión → obtener siguiente acción
  3. Ejecutar la acción
  4. Si la acción modifica la pantalla → tomar screenshot automático
  5. Repetir desde 2 hasta que done=True o se alcance el límite de pasos
  6. Emitir cada paso como evento (callback) para el frontend en tiempo real
"""

import time
from typing import Callable, Generator
from agent.planner import plan_next_step
from agent.executor import execute_with_screenshot
from agent import tools

# Límite de seguridad: máximo de pasos por tarea
MAX_STEPS = 30

# Acciones que terminan el bucle
TERMINAL_ACTIONS = {"task_done", "chat"}

# Acciones que NO necesitan screenshot previo (ya tienen la info necesaria)
NO_SCREENSHOT_NEEDED = {"wait", "clipboard_copy"}


def run_task(
    task: str,
    on_step: Callable[[dict], None] = None,
    max_steps: int = MAX_STEPS
) -> Generator[dict, None, None]:
    """
    Ejecuta una tarea de forma autónoma, paso a paso.
    
    Yields dicts con:
      {
        "step":       int,      # Número de paso
        "action":     str,      # Acción ejecutada
        "reason":     str,      # Explicación del paso
        "result":     str,      # Resultado de la ejecución
        "screenshot": str|None, # Base64 del screenshot (si aplica)
        "done":       bool,     # True si la tarea terminó
        "ok":         bool,     # True si la acción fue exitosa
        "type":       str       # "step" | "done" | "error"
      }
    """
    step_history = []
    current_screenshot = None

    # ── Paso 0: Screenshot inicial ──────────────────────────
    try:
        current_screenshot = tools.screenshot()
        yield {
            "step": 0,
            "action": "screenshot",
            "reason": "Viendo el estado inicial de la pantalla",
            "result": "Captura inicial tomada",
            "screenshot": current_screenshot,
            "done": False,
            "ok": True,
            "type": "step"
        }
    except Exception as e:
        yield {
            "step": 0,
            "action": "error",
            "reason": "",
            "result": f"No se pudo tomar captura de pantalla: {e}. Asegúrate de que el agente corre en Windows con pantalla.",
            "screenshot": None,
            "done": True,
            "ok": False,
            "type": "error"
        }
        return

    # ── Bucle principal ─────────────────────────────────────
    for step_num in range(1, max_steps + 1):

        # 1. Planificar siguiente paso
        try:
            action_data = plan_next_step(task, current_screenshot, step_history)
        except Exception as e:
            yield {
                "step": step_num,
                "action": "error",
                "reason": "",
                "result": f"Error en el planificador: {e}",
                "screenshot": None,
                "done": True,
                "ok": False,
                "type": "error"
            }
            break

        action  = action_data.get("action", "chat")
        reason  = action_data.get("reason", "")
        is_done = action_data.get("done", False)

        # 2. Ejecutar la acción
        try:
            exec_result = execute_with_screenshot(action_data)
        except Exception as e:
            exec_result = {"ok": False, "message": str(e), "screenshot": None}

        # 3. Actualizar screenshot si la acción generó uno nuevo
        if exec_result.get("screenshot"):
            current_screenshot = exec_result["screenshot"]

        # 4. Registrar en historial
        step_desc = f"{action}: {exec_result['message'][:80]}"
        step_history.append(step_desc)

        # 5. Emitir el paso al frontend
        step_type = "done" if (is_done or action == "task_done") else "step"

        yield {
            "step":       step_num,
            "action":     action,
            "reason":     reason,
            "result":     exec_result["message"],
            "screenshot": exec_result.get("screenshot"),
            "done":       is_done or action == "task_done",
            "ok":         exec_result["ok"],
            "type":       step_type
        }

        # 6. Verificar si terminamos
        if is_done or action == "task_done":
            break

        # 7. Si la acción fue solo chat sin cambios en pantalla, terminar
        if action == "chat" and step_num > 1:
            break

        # 8. Pequeña pausa entre pasos para estabilidad
        time.sleep(0.3)

    else:
        # Se alcanzó el límite de pasos
        yield {
            "step":       max_steps + 1,
            "action":     "task_done",
            "reason":     "Límite de pasos alcanzado",
            "result":     f"Se alcanzó el límite de {max_steps} pasos. La tarea puede estar incompleta.",
            "screenshot": current_screenshot,
            "done":       True,
            "ok":         True,
            "type":       "done"
        }
