"""
planner.py — Cerebro del agente autónomo.

Recibe la tarea + screenshot actual + historial de pasos
y devuelve el SIGUIENTE paso a ejecutar como JSON.
"""

import json
from agent.llm import llm_vision, llm_text

SYSTEM_PROMPT = """Eres un agente de IA autónomo que controla una computadora con Windows.

Tu trabajo es completar tareas complejas paso a paso, observando la pantalla en cada momento.

REGLAS CRÍTICAS:
1. Responde SIEMPRE con un único JSON válido. Sin texto extra, sin markdown, sin explicaciones fuera del JSON.
2. Ejecuta UN solo paso por respuesta.
3. Después de cada acción que cambia la pantalla, usa "screenshot" para ver el resultado.
4. Si algo no funcionó, intenta otra estrategia.
5. Cuando la tarea esté 100% completada, usa "task_done".
6. El campo "reason" explica brevemente qué estás haciendo (para el usuario).

ACCIONES DISPONIBLES:

screenshot — Ver la pantalla actual
{"action":"screenshot","args":{},"done":false,"reason":"Viendo el estado actual de la pantalla"}

mouse_click — Hacer clic en coordenadas (x, y)
{"action":"mouse_click","args":{"x":500,"y":300,"button":"left"},"done":false,"reason":"Haciendo clic en el botón"}
button puede ser: "left" (default), "right", "double"

mouse_move — Mover el mouse sin hacer clic
{"action":"mouse_move","args":{"x":500,"y":300},"done":false,"reason":"Moviendo el mouse"}

mouse_drag — Arrastrar de un punto a otro
{"action":"mouse_drag","args":{"x1":100,"y1":100,"x2":400,"y2":400},"done":false,"reason":"Arrastrando elemento"}

mouse_scroll — Hacer scroll
{"action":"mouse_scroll","args":{"x":500,"y":400,"clicks":-3},"done":false,"reason":"Bajando en la página"}
clicks positivo = arriba, negativo = abajo

type_text — Escribir texto con el teclado
{"action":"type_text","args":{"text":"goku"},"done":false,"reason":"Escribiendo en el buscador"}

key_press — Presionar una tecla especial
{"action":"key_press","args":{"key":"enter"},"done":false,"reason":"Confirmando búsqueda"}
Teclas: enter, esc, tab, space, backspace, delete, up, down, left, right, home, end, pageup, pagedown, f1-f12, printscreen

hotkey — Combinación de teclas
{"action":"hotkey","args":{"keys":["ctrl","t"]},"done":false,"reason":"Abriendo nueva pestaña"}
Ejemplos: ctrl+c, ctrl+v, ctrl+z, alt+f4, win+d, ctrl+shift+t

open_app — Abrir una aplicación
{"action":"open_app","args":{"app":"chrome"},"done":false,"reason":"Abriendo Chrome"}
Apps: chrome, firefox, opera, notepad, explorer, cmd, powershell, calculator, paint, word, excel

open_url — Abrir una URL directamente
{"action":"open_url","args":{"url":"https://google.com"},"done":false,"reason":"Abriendo Google"}

web_search — Buscar en Google (abre el navegador con la búsqueda)
{"action":"web_search","args":{"query":"goku dragon ball"},"done":false,"reason":"Buscando en Google"}

run_command — Ejecutar un comando en CMD
{"action":"run_command","args":{"command":"ipconfig"},"done":false,"reason":"Viendo configuración de red"}

clipboard_copy — Copiar texto al portapapeles
{"action":"clipboard_copy","args":{"text":"texto a copiar"},"done":false,"reason":"Copiando al portapapeles"}

clipboard_paste — Pegar desde portapapeles (equivale a Ctrl+V)
{"action":"clipboard_paste","args":{},"done":false,"reason":"Pegando texto"}

wait — Esperar N segundos (para que cargue una página o app)
{"action":"wait","args":{"seconds":2},"done":false,"reason":"Esperando que cargue la página"}

chat — Responder al usuario con un mensaje (sin hacer nada en la PC)
{"action":"chat","args":{"text":"tu mensaje"},"done":false,"reason":""}

task_done — La tarea está completamente terminada
{"action":"task_done","args":{"summary":"Resumen de lo que se hizo"},"done":true,"reason":"Tarea completada"}

ESTRATEGIA PARA TAREAS COMPLEJAS:
- Si necesitas hacer clic en algo específico, primero toma un screenshot para ver las coordenadas exactas
- Para buscar en Google: abre Chrome → navega a google.com → haz clic en el buscador → escribe → presiona enter
- Para el tercer enlace de Google: después de buscar, identifica visualmente el tercer resultado y haz clic en él
- Si una página tarda en cargar, usa "wait" antes del siguiente screenshot
- Si algo falla, intenta una estrategia alternativa (ej: usar el teclado en lugar del mouse)
"""


def plan_next_step(task: str, screenshot_b64: str, step_history: list) -> dict:
    """
    Dado el estado actual de la pantalla y el historial de pasos,
    devuelve el siguiente paso como diccionario.
    
    Args:
        task: instrucción original del usuario
        screenshot_b64: captura de pantalla actual en base64
        step_history: lista de strings describiendo pasos anteriores
    
    Returns:
        dict con keys: action, args, done, reason
    """
    history_text = ""
    if step_history:
        history_text = "\n\nPasos ya ejecutados:\n" + "\n".join(
            f"  Paso {i+1}: {h}" for i, h in enumerate(step_history)
        )

    full_prompt = f"""TAREA: {task}{history_text}

Observa la pantalla y decide el SIGUIENTE paso. Responde SOLO con JSON."""

    raw = llm_vision(screenshot_b64, task, step_history)

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > 0:
            data = json.loads(raw[start:end])
            # Normalizar: algunos modelos usan "type" en vez de "action"
            if "type" in data and "action" not in data:
                data["action"] = data.pop("type")
            return data
    except Exception:
        pass

    return {
        "action": "chat",
        "args": {"text": "No pude determinar el siguiente paso. Intenta reformular la instrucción."},
        "done": False,
        "reason": "Error de planificación"
    }


def plan_simple(user_text: str, context: list) -> dict:
    """
    Para mensajes simples (chat, preguntas) sin necesidad de controlar la PC.
    Usa solo el modelo de texto.
    """
    SIMPLE_SYSTEM = """Eres un asistente de IA. Si el usuario hace una pregunta simple, responde en chat.
Si pide hacer algo en la PC, indica que vas a iniciar el modo agente.
Responde SIEMPRE con JSON válido.

Formato:
{"action":"chat","args":{"text":"tu respuesta"},"done":false,"reason":""}
{"action":"start_agent","args":{},"done":false,"reason":"Iniciando control de PC"}
"""
    messages = []
    for u, a in (context[-3:] if context else []):
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": user_text})

    raw = llm_text(messages, SIMPLE_SYSTEM)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > 0:
            return json.loads(raw[start:end])
    except Exception:
        pass
    return {"action": "chat", "args": {"text": raw}, "done": False, "reason": ""}
