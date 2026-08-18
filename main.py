import sys
import os

# 1. CONFIGURACIÓN DE RUTAS (Blindaje para OneDrive)
# Detectamos la ubicación de este archivo main.py
base_path = os.path.dirname(os.path.abspath(__file__))
# Definimos la carpeta 'agent' donde están tus módulos
agent_path = os.path.join(base_path, 'agent')

# Agregamos la carpeta 'agent' al buscador de Python para que encuentre los archivos
if agent_path not in sys.path:
    sys.path.insert(0, agent_path)

# 2. IMPORTACIÓN DE MÓDULOS EXISTENTES
try:
    # Estos archivos SÍ aparecen en tus capturas dentro de la carpeta 'agent'
    from memory import init_db, save_turn, load_last_turns
    from planner import plan_simple as plan
    from executor import execute
    
    # FUNCIONES DE INTERFAZ (Configuradas aquí para evitar el error de ui_cli.py)
    def ask_user():
        return input("\n>>> Usuario: ")

    def info(msg):
        print(f"\n[SISTEMA]: {msg}")

    def confirm(prompt):
        res = input(f"\n? {prompt} (s/n): ").lower()
        return res == 's'

    print("✓ Conexión con módulos de la carpeta 'agent' establecida.")

except ImportError as e:
    print(f"❌ ERROR DE IMPORTACIÓN: {e}")
    print(f"Buscando en: {agent_path}")
    sys.exit(1)

# 3. LÓGICA PRINCIPAL
def main():
    print("\n" + "="*40)
    print("        AI AGENT - MODO CONSOLA")
    print("="*40)
    
    # Inicializar base de datos de memoria
    init_db()
    info("Agente en línea. Escribe 'salir' para terminar.")

    while True:
        # Capturar entrada
        user_input = ask_user()
        
        if not user_input or user_input.lower() in ["salir", "exit"]:
            print("\nApagando agente...")
            break

        # Procesar con el Planner
        context = load_last_turns()
        print("\n[PENSANDO] Analizando petición...")
        
        # Generar acción (usando plan_simple del archivo planner.py)
        action_dict = plan(user_input, context)
        print(f"PLAN SUGERIDO: {action_dict}")

        # Ejecutar acción si el usuario confirma
        if confirm("¿Autorizas ejecutar esta acción?"):
            # Solo pasamos 1 argumento según requiere tu executor.py
            result = execute(action_dict)
            
            # Extraer mensaje del resultado y guardar en memoria
            msg = result.get("message", "Acción completada con éxito.")
            info(msg)
            save_turn(user_input, msg)
            print("-" * 30)
        else:
            print("Acción cancelada.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")