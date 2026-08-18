"""
executor.py — Ejecuta acciones del agente sobre la PC.

Recibe un dict con {action, args, done, reason} y llama a la herramienta correcta.
Devuelve {ok, message, screenshot} donde screenshot puede ser None o base64.
"""

from agent import tools


def execute(action_data: dict) -> dict:
    """
    Ejecuta una acción y devuelve el resultado.
    
    Returns:
        {
            "ok": bool,
            "message": str,       # Descripción de lo que pasó
            "screenshot": str|None  # Base64 si se tomó captura
        }
    """
    action = action_data.get("action", "chat")
    args   = action_data.get("args", {})

    try:
        result = _dispatch(action, args)
        return {"ok": True, "message": result, "screenshot": None}

    except Exception as e:
        return {"ok": False, "message": f"Error ejecutando '{action}': {str(e)}", "screenshot": None}


def execute_with_screenshot(action_data: dict) -> dict:
    """
    Como execute(), pero si la acción modifica la pantalla,
    toma un screenshot automáticamente después.
    """
    result = execute(action_data)
    action = action_data.get("action", "chat")

    # Acciones que cambian la pantalla → tomar screenshot automático
    VISUAL_ACTIONS = {
        "mouse_click", "mouse_drag", "mouse_scroll",
        "type_text", "key_press", "hotkey",
        "open_app", "open_url", "web_search",
        "run_command", "clipboard_paste", "wait"
    }

    if action in VISUAL_ACTIONS and result["ok"]:
        import time
        time.sleep(0.5)  # Pequeña pausa para que la pantalla se actualice
        try:
            result["screenshot"] = tools.screenshot()
        except Exception:
            result["screenshot"] = None

    elif action == "screenshot":
        try:
            result["screenshot"] = tools.screenshot()
            result["message"] = "Captura de pantalla tomada"
        except Exception as e:
            result["message"] = f"Error tomando captura: {e}"

    return result


def _dispatch(action: str, args: dict) -> str:
    """Enruta la acción a la función correcta en tools.py"""

    # ── Comunicación ──────────────────────────────
    if action == "chat":
        return args.get("text", "")

    if action == "task_done":
        return args.get("summary", "Tarea completada.")

    # ── Visión ────────────────────────────────────
    if action == "screenshot":
        return "screenshot"  # El screenshot real se toma en execute_with_screenshot

    # ── Mouse ─────────────────────────────────────
    if action == "mouse_move":
        return tools.mouse_move(int(args["x"]), int(args["y"]))

    if action == "mouse_click":
        return tools.mouse_click(
            int(args["x"]),
            int(args["y"]),
            args.get("button", "left")
        )

    if action == "mouse_drag":
        return tools.mouse_drag(
            int(args["x1"]), int(args["y1"]),
            int(args["x2"]), int(args["y2"])
        )

    if action == "mouse_scroll":
        x = int(args.get("x", 0))
        y = int(args.get("y", 0))
        clicks = int(args.get("clicks", -3))
        return tools.mouse_scroll(x, y, clicks)

    # ── Teclado ───────────────────────────────────
    if action == "type_text":
        text = args.get("text", "")
        fast = args.get("fast", False)
        if fast or len(text) > 100:
            return tools.type_text_fast(text)
        return tools.type_text(text)

    if action == "key_press":
        return tools.key_press(args["key"])

    if action == "hotkey":
        keys = args.get("keys", [])
        if isinstance(keys, list):
            return tools.hotkey(*keys)
        return tools.hotkey(keys)

    # ── Sistema operativo ─────────────────────────
    if action == "open_app":
        return tools.open_app(args["app"])

    if action == "open_url":
        return tools.open_url(args["url"], args.get("browser", "default"))

    if action == "web_search":
        return tools.web_search(args["query"], args.get("browser", "default"))

    if action == "run_command":
        return tools.run_command(args["command"])

    # ── Portapapeles ──────────────────────────────
    if action == "clipboard_copy":
        return tools.clipboard_copy(args["text"])

    if action == "clipboard_paste":
        return tools.clipboard_paste()

    # ── Espera ────────────────────────────────────
    if action == "wait":
        return tools.wait(float(args.get("seconds", 1)))

    return f"Acción desconocida: {action}"
