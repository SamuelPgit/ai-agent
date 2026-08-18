"""
memory.py — Memoria persistente del agente usando SQLite.

Guarda el historial de tareas y conversaciones.
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "memory.db"


def init_db():
    """Crea las tablas si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Historial de conversación simple (chat)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chatlog (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user      TEXT,
            ai        TEXT
        )
    """)

    # Historial de tareas autónomas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasklog (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            task      TEXT,
            steps     TEXT,   -- JSON array de pasos
            status    TEXT    -- "completed" | "failed" | "partial"
        )
    """)

    conn.commit()
    conn.close()


# ── Chat simple ──────────────────────────────────────────────

def save_chat(user: str, ai: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO chatlog (timestamp, user, ai) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), user, ai)
    )
    conn.commit()
    conn.close()


def load_chat_history(n: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT user, ai FROM chatlog ORDER BY id DESC LIMIT ?", (n,)
    )
    rows = cur.fetchall()
    conn.close()
    rows.reverse()
    return rows


# ── Tareas autónomas ─────────────────────────────────────────

def save_task(task: str, steps: list, status: str = "completed"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tasklog (timestamp, task, steps, status) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), task, json.dumps(steps, ensure_ascii=False), status)
    )
    conn.commit()
    conn.close()


def load_task_history(n: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT timestamp, task, status FROM tasklog ORDER BY id DESC LIMIT ?", (n,)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"timestamp": r[0], "task": r[1], "status": r[2]} for r in rows]


# ── Limpiar ──────────────────────────────────────────────────

def clear_all():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM chatlog")
    conn.execute("DELETE FROM tasklog")
    conn.commit()
    conn.close()
# --- Al final de memory.py ---

# Creamos alias para que coincidan con lo que busca main.py
save_turn = save_chat
load_last_turns = load_chat_history