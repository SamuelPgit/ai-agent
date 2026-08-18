"""
tools.py — Todas las herramientas de control de PC del agente.

Requiere Windows con pantalla. Usa pyautogui + subprocess + pyperclip.
"""

import os
import time
import base64
import io
import subprocess
import webbrowser
from urllib.parse import quote_plus

import pyautogui
import pyperclip
from PIL import Image

# Configuración de seguridad de pyautogui
pyautogui.FAILSAFE = True   # Mover mouse a esquina sup-izq detiene el agente
pyautogui.PAUSE = 0.2       # Pausa mínima entre acciones

# ──────────────────────────────────────────────────────────────
# VISIÓN — Captura de pantalla
# ──────────────────────────────────────────────────────────────

def screenshot() -> str:
    """Toma captura de pantalla y devuelve base64 PNG."""
    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def screenshot_region(x: int, y: int, w: int, h: int) -> str:
    """Captura una región específica de la pantalla."""
    img = pyautogui.screenshot(region=(x, y, w, h))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def get_screen_size() -> tuple:
    return pyautogui.size()


# ──────────────────────────────────────────────────────────────
# MOUSE
# ──────────────────────────────────────────────────────────────

def mouse_move(x: int, y: int) -> str:
    pyautogui.moveTo(x, y, duration=0.3)
    return f"Mouse movido a ({x}, {y})"


def mouse_click(x: int, y: int, button: str = "left") -> str:
    if button == "double":
        pyautogui.doubleClick(x, y)
        return f"Doble clic en ({x}, {y})"
    elif button == "right":
        pyautogui.rightClick(x, y)
        return f"Clic derecho en ({x}, {y})"
    else:
        pyautogui.click(x, y)
        return f"Clic izquierdo en ({x}, {y})"


def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> str:
    pyautogui.moveTo(x1, y1, duration=0.2)
    pyautogui.dragTo(x2, y2, duration=0.5, button="left")
    return f"Arrastrado de ({x1},{y1}) a ({x2},{y2})"


def mouse_scroll(x: int, y: int, clicks: int) -> str:
    pyautogui.moveTo(x, y)
    pyautogui.scroll(clicks)
    direction = "arriba" if clicks > 0 else "abajo"
    return f"Scroll {direction} {abs(clicks)} clicks en ({x},{y})"


# ──────────────────────────────────────────────────────────────
# TECLADO
# ──────────────────────────────────────────────────────────────

def type_text(text: str, interval: float = 0.04) -> str:
    """Escribe texto carácter por carácter con intervalo natural."""
    pyautogui.write(text, interval=interval)
    return f"Texto escrito: '{text[:50]}{'...' if len(text) > 50 else ''}'"


def type_text_fast(text: str) -> str:
    """Escribe texto pegándolo desde el portapapeles (más rápido para textos largos)."""
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    return f"Texto pegado: '{text[:50]}{'...' if len(text) > 50 else ''}'"


def key_press(key: str) -> str:
    pyautogui.press(key)
    return f"Tecla presionada: {key}"


def hotkey(*keys) -> str:
    pyautogui.hotkey(*keys)
    return f"Combinación: {'+'.join(keys)}"


# ──────────────────────────────────────────────────────────────
# SISTEMA OPERATIVO — Aplicaciones
# ──────────────────────────────────────────────────────────────

APP_COMMANDS = {
    "chrome":      "start chrome",
    "firefox":     "start firefox",
    "opera":       None,  # Ruta especial abajo
    "notepad":     "notepad",
    "explorer":    "explorer",
    "cmd":         "start cmd",
    "powershell":  "start powershell",
    "calculator":  "calc",
    "paint":       "mspaint",
    "word":        "start winword",
    "excel":       "start excel",
    "taskmgr":     "taskmgr",
    "regedit":     "regedit",
    "control":     "control",
}

OPERA_PATHS = [
    r"C:\Users\Asus\AppData\Local\Programs\Opera\opera.exe",
    r"C:\Program Files\Opera\opera.exe",
    r"C:\Program Files (x86)\Opera\opera.exe",
    r"C:\Users\Samuel\AppData\Local\Programs\Opera\opera.exe",
]


def open_app(app: str) -> str:
    app = app.lower().strip()

    if app == "opera":
        for path in OPERA_PATHS:
            if os.path.exists(path):
                subprocess.Popen([path])
                return "Opera abierto"
        return "Opera no encontrado en las rutas conocidas"

    cmd = APP_COMMANDS.get(app)
    if cmd:
        os.system(cmd)
        return f"'{app}' abierto"

    # Intentar abrir directamente por nombre
    try:
        subprocess.Popen(app)
        return f"'{app}' iniciado"
    except Exception as e:
        return f"No se pudo abrir '{app}': {e}"


def open_url(url: str, browser: str = "default") -> str:
    if browser == "opera":
        for path in OPERA_PATHS:
            if os.path.exists(path):
                subprocess.Popen([path, url])
                return f"URL abierta en Opera: {url}"
    webbrowser.open(url)
    return f"URL abierta: {url}"


def web_search(query: str, browser: str = "default") -> str:
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    return open_url(url, browser)


def run_command(command: str, shell: bool = True) -> str:
    """Ejecuta un comando en CMD y devuelve la salida."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=15
        )
        output = result.stdout.strip() or result.stderr.strip() or "Comando ejecutado"
        return output[:500]  # Limitar salida
    except subprocess.TimeoutExpired:
        return "Comando agotó el tiempo de espera"
    except Exception as e:
        return f"Error al ejecutar comando: {e}"


# ──────────────────────────────────────────────────────────────
# PORTAPAPELES
# ──────────────────────────────────────────────────────────────

def clipboard_copy(text: str) -> str:
    pyperclip.copy(text)
    return f"Copiado al portapapeles: '{text[:50]}'"


def clipboard_paste() -> str:
    pyautogui.hotkey("ctrl", "v")
    return "Pegado desde portapapeles"


def clipboard_get() -> str:
    return pyperclip.paste()


# ──────────────────────────────────────────────────────────────
# UTILIDADES
# ──────────────────────────────────────────────────────────────

def wait(seconds: float) -> str:
    time.sleep(seconds)
    return f"Esperado {seconds} segundos"
