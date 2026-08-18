"""
llm.py — Interfaz con el modelo de lenguaje local (Ollama)

Modelos usados:
  - llama3        → planificación de pasos (texto puro, rápido)
  - llava / llava:13b → visión de pantalla (imagen + texto)

Si no tienes llava, instálalo con: ollama pull llava
"""

import json
import base64
import ollama

# Modelo de texto para planificación general
TEXT_MODEL = "llama3"

# Modelo de visión para analizar screenshots
VISION_MODEL = "llava"


def llm_text(messages: list, system: str) -> str:
    """Llama al LLM de texto y devuelve JSON crudo."""
    try:
        response = ollama.chat(
            model=TEXT_MODEL,
            format="json",
            messages=[
                {"role": "system", "content": system},
                *messages
            ],
            options={"temperature": 0}
        )
        content = response["message"]["content"].strip()
        json.loads(content)  # Validar que sea JSON
        return content
    except json.JSONDecodeError:
        return '{"action":"chat","args":{"text":"No pude generar una respuesta valida."},"done":false}'
    except Exception as e:
        return f'{{"action":"chat","args":{{"text":"Error LLM: {str(e)}"}}, "done":false}}'


def llm_vision(screenshot_b64: str, task: str, history: list) -> str:
    """
    Llama al LLM de visión con un screenshot y devuelve la siguiente acción JSON.
    
    screenshot_b64: imagen en base64 (PNG)
    task: instrucción original del usuario
    history: lista de pasos ya ejecutados
    """
    history_text = ""
    if history:
        history_text = "\n\nPasos ya ejecutados:\n" + "\n".join(
            f"  {i+1}. {h}" for i, h in enumerate(history)
        )

    prompt = f"""Tarea del usuario: {task}{history_text}

Observa la pantalla y decide el SIGUIENTE paso para completar la tarea.
Responde SOLO con JSON valido, sin texto adicional."""

    try:
        response = ollama.chat(
            model=VISION_MODEL,
            format="json",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [screenshot_b64]
                }
            ],
            options={"temperature": 0}
        )
        content = response["message"]["content"].strip()
        json.loads(content)
        return content
    except json.JSONDecodeError:
        return '{"action":"chat","args":{"text":"No pude interpretar la pantalla."},"done":false}'
    except Exception as e:
        # Si llava no está disponible, usar solo texto
        return llm_text_fallback(task, history, str(e))


def llm_text_fallback(task: str, history: list, error: str = "") -> str:
    """Fallback cuando no hay modelo de visión disponible."""
    history_text = ""
    if history:
        history_text = "Pasos ya ejecutados: " + "; ".join(history)

    system = """Eres un agente que controla una PC. Sin ver la pantalla, decide el siguiente paso logico.
Responde SOLO con JSON valido."""

    messages = [{"role": "user", "content": f"Tarea: {task}. {history_text}"}]
    return llm_text(messages, system)
