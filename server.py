"""
server.py — Servidor Flask del agente autónomo de PC.

Endpoints:
  GET  /                → Interfaz web
  POST /chat            → Mensaje simple (sin control de PC)
  POST /task            → Iniciar tarea autónoma (streaming SSE)
  GET  /screenshot      → Captura de pantalla bajo demanda
  GET  /history         → Historial de tareas
  POST /clear           → Limpiar historial
  GET  /status          → Estado del agente
"""

import os
import sys
import json
import threading
import time
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.memory import init_db, save_chat, load_chat_history, save_task, load_task_history, clear_all
from agent.planner import plan_simple
from agent.agent_loop import run_task

app = Flask(__name__, static_folder="ui", static_url_path="")
CORS(app)

# Estado global del agente
agent_state = {
    "running": False,
    "current_task": None,
    "stop_requested": False
}

init_db()


# ──────────────────────────────────────────────────────────────
# FRONTEND
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")


# ──────────────────────────────────────────────────────────────
# CHAT SIMPLE (sin control de PC)
# ──────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Mensaje vacío"}), 400

    user_msg = data["message"].strip()

    try:
        context = load_chat_history(n=6)
        result = plan_simple(user_msg, context)
        response_text = result.get("args", {}).get("text", "Sin respuesta")
        save_chat(user_msg, response_text)
        return jsonify({
            "message": response_text,
            "action": result.get("action", "chat")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# TAREA AUTÓNOMA — Streaming SSE
# ──────────────────────────────────────────────────────────────

@app.route("/task", methods=["POST"])
def start_task():
    """
    Inicia una tarea autónoma y hace streaming de cada paso via SSE.
    
    El cliente recibe eventos en tiempo real:
      data: {"step":1, "action":"screenshot", "reason":"...", "result":"...", 
              "screenshot":"base64...", "done":false, "ok":true, "type":"step"}
    """
    data = request.get_json()
    if not data or not data.get("task", "").strip():
        return jsonify({"error": "Tarea vacía"}), 400

    task = data["task"].strip()
    max_steps = int(data.get("max_steps", 30))

    if agent_state["running"]:
        return jsonify({"error": "El agente ya está ejecutando una tarea"}), 409

    def generate():
        agent_state["running"] = True
        agent_state["current_task"] = task
        agent_state["stop_requested"] = False

        steps_log = []

        try:
            # Evento de inicio
            yield _sse_event({
                "type": "start",
                "task": task,
                "message": f"Iniciando tarea: {task}"
            })

            for step in run_task(task, max_steps=max_steps):

                # Verificar si se solicitó detener
                if agent_state["stop_requested"]:
                    yield _sse_event({
                        "type": "stopped",
                        "message": "Tarea detenida por el usuario",
                        "done": True
                    })
                    break

                # Registrar paso
                steps_log.append({
                    "step":   step["step"],
                    "action": step["action"],
                    "reason": step["reason"],
                    "result": step["result"],
                    "ok":     step["ok"]
                })

                # Emitir paso al frontend
                yield _sse_event(step)

                # Si terminó, guardar en memoria
                if step.get("done"):
                    status = "completed" if step.get("ok") else "failed"
                    save_task(task, steps_log, status)
                    break

        except Exception as e:
            yield _sse_event({
                "type": "error",
                "message": f"Error inesperado: {str(e)}",
                "done": True
            })
        finally:
            agent_state["running"] = False
            agent_state["current_task"] = None

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.route("/task/stop", methods=["POST"])
def stop_task():
    """Solicita detener la tarea en ejecución."""
    agent_state["stop_requested"] = True
    return jsonify({"status": "stop_requested"})


# ──────────────────────────────────────────────────────────────
# SCREENSHOT BAJO DEMANDA
# ──────────────────────────────────────────────────────────────

@app.route("/screenshot", methods=["GET"])
def get_screenshot():
    try:
        from agent.tools import screenshot
        b64 = screenshot()
        return jsonify({"screenshot": b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# HISTORIAL Y ESTADO
# ──────────────────────────────────────────────────────────────

@app.route("/history", methods=["GET"])
def history():
    try:
        chat_hist = load_chat_history(n=20)
        task_hist = load_task_history(n=10)
        return jsonify({
            "chat":  [{"user": u, "ai": a} for u, a in chat_hist],
            "tasks": task_hist
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "running":      agent_state["running"],
        "current_task": agent_state["current_task"]
    })


@app.route("/clear", methods=["POST"])
def clear():
    try:
        clear_all()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# UTILIDADES
# ──────────────────────────────────────────────────────────────

def _sse_event(data: dict) -> str:
    """Formatea un evento SSE."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    print("=" * 55)
    print("  AI AGENT — Control Autónomo de PC")
    print("  Desarrollado por Samuel y Angel")
    print("=" * 55)
    print(f"\n  Servidor: http://localhost:5000")
    print(f"  Asegúrate de tener Ollama corriendo con llava y llama3\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
