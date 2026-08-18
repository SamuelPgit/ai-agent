"""
schema.py — Definición de todas las acciones que el agente puede ejecutar.

Cada acción tiene:
  - action: nombre de la acción
  - args:   parámetros específicos
  - done:   True si la tarea completa ha terminado
  - reason: explicación breve de por qué se hace este paso
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, Optional

ActionType = Literal[
    # ── Comunicación ──────────────────────────────
    "chat",           # Responder al usuario en texto
    "task_done",      # Declarar que la tarea está completada

    # ── Visión ────────────────────────────────────
    "screenshot",     # Tomar captura de pantalla

    # ── Mouse ─────────────────────────────────────
    "mouse_move",     # Mover mouse a (x, y)
    "mouse_click",    # Clic en (x, y) — left/right/double
    "mouse_drag",     # Arrastrar de (x1,y1) a (x2,y2)
    "mouse_scroll",   # Scroll arriba/abajo

    # ── Teclado ───────────────────────────────────
    "type_text",      # Escribir texto
    "key_press",      # Tecla especial (enter, esc, tab...)
    "hotkey",         # Combinación (ctrl+c, alt+f4...)

    # ── Sistema operativo ─────────────────────────
    "open_app",       # Abrir aplicación por nombre
    "open_url",       # Abrir URL en navegador
    "web_search",     # Buscar en Google
    "run_command",    # Ejecutar comando en CMD/PowerShell

    # ── Portapapeles ──────────────────────────────
    "clipboard_copy", # Copiar texto al portapapeles
    "clipboard_paste",# Pegar desde portapapeles

    # ── Espera ────────────────────────────────────
    "wait",           # Esperar N segundos (para que cargue algo)
]


class Action(BaseModel):
    action: ActionType
    args: Dict[str, Any] = Field(default_factory=dict)
    done: bool = False          # True = tarea completa, detener el bucle
    reason: Optional[str] = None  # Explicación del paso para mostrar al usuario
