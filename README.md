# AI Agent — Autonomous PC Control with Computer Vision

An autonomous AI agent that controls your computer using natural language instructions. Built with **Python**, it perceives the screen through screenshots, reasons with a vision LLM (Ollama + LLaVA), plans the next step, and executes actions (mouse, keyboard, apps, web, system) in a perception → action → verification loop. The entire agent runs **100% locally** — no data ever leaves your machine.

> Developed by [Samuel Prato](https://github.com/SamuelPgit) and Angel.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)



---

## How It Works

The agent operates in a **perception → action → verification** loop:

1. You send an instruction in natural language (e.g., *"search goku on Google and open the third link"*)
2. The agent takes a **screenshot** of the screen and analyzes it with a vision model (LLaVA)
3. The planner decides the **next step** (click, type, key combination, open app, etc.)
4. The executor runs the action and takes another screenshot to **verify** the result
5. Steps repeat until the task is complete or the step limit is reached

Each step is streamed in real time to the web UI via **Server-Sent Events (SSE)**, so you can watch the agent think and act live.

```
User instruction
      │
      ▼
┌─────────────┐    screenshot     ┌──────────────┐
│   Planner    │◄─────────────────│ Vision LLM   │
│  (llama3)    │                   │   (llava)    │
└──────┬──────┘                    └──────────────┘
       │ action
       ▼
┌─────────────┐    screenshot     ┌──────────────┐
│  Executor    │──────────────────►│  Verification │
│(mouse/keyboard│                   │  (next loop)  │
│ /apps/system)│                    └──────────────┘
└─────────────┘
```

---

## Capabilities

| Category | Actions |
|----------|---------|
| **Vision** | Full-screen and region screenshots, visual analysis of the screen |
| **Mouse** | Move, left/right/double click, drag, scroll |
| **Keyboard** | Type text, special keys, combinations (Ctrl+C, Alt+F4, ...) |
| **Apps** | Open Chrome, Firefox, Opera, Notepad, Explorer, CMD, PowerShell, Calculator, Paint |
| **Web** | Open URLs, Google search |
| **System** | Run commands in CMD/PowerShell |
| **Clipboard** | Copy and paste text |

## Project Structure

```text
ai_agent/
├── server.py              # Flask server — API endpoints + SSE streaming
├── main.py                # CLI alternative entry point
├── requirements.txt       # Python dependencies
├── agent/
│   ├── agent_loop.py      # Autonomous perception → action → verification loop
│   ├── planner.py         # Next-step reasoning (llama3)
│   ├── executor.py        # Action execution with screenshot verification
│   ├── llm.py             # Ollama connection (llama3 + llava)
│   ├── schema.py          # Pydantic type definitions for all actions
│   ├── tools.py           # PC control toolset (20+ actions)
│   └── memory.py          # Persistent task/chat history (SQLite)
└── ui/
    ├── index.html         # Web interface
    ├── style.css          # Styles (dark/light theme)
    └── app.js             # Frontend logic + SSE step streaming
```

## Quick Start

### Prerequisites

1. **Python 3.10+**
2. **[Ollama](https://ollama.com)** installed and running
3. Models pulled:

```bash
ollama pull llama3    # text reasoning
ollama pull llava     # screen vision (required for agent mode)
```

### Install & Run

```bash
# Clone the repository
git clone https://github.com/SamuelPgit/ai-agent.git
cd ai-agent

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server and open http://localhost:5000
python server.py
```

### Using the Agent

**Chat mode** — simple conversation with the agent (no PC control).

**Autonomous agent mode** — the agent sees your screen and executes the task step by step. Watch each step stream live in the web UI.

| Instruction | What it does |
|-------------|--------------|
| `Search goku on Google and open the third link` | Search & navigation |
| `Open notepad and write a to-do list` | App control & typing |
| `Open YouTube in Chrome and search lofi music` | Web navigation |
| `Take a screenshot and tell me what's on screen` | Vision |
| `Open calculator and compute 1234 × 56` | App control |
| `Create a folder called Project on the desktop` | File system |

## Safety Features

- `pyautogui.FAILSAFE = True` — moving the mouse to the **top-left corner** emergency-stops the agent
- Runs **100% local** with Ollama — no data sent to the internet
- Configurable step limit per task (default: 25)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Backend | Flask, Flask-CORS, Server-Sent Events |
| AI / Vision | Ollama, llama3, llava |
| PC Control | pyautogui, pynput, pyperclip |
| Data Validation | Pydantic |
| Persistence | SQLite |
| Frontend | Vanilla HTML/CSS/JS (dark/light theme) |

## Notes

- The `llava` vision model is required for the agent to *see* the screen. Without it, the agent runs in "blind" text-only mode.
- For better vision performance, use `llava:13b` if you have 8GB+ VRAM.
- The agent is optimized for **Windows**. On Linux/macOS, minor adjustments in `tools.py` may be needed.

## License

This project is licensed under the [MIT License](LICENSE).
