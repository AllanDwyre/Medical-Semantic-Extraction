from termcolor import colored

def print_color(message, type="info"):
    """Affiche un message coloré selon le type."""
    color_map = {
        "info":    ("light_cyan", "ℹ️"),
        "success": ("light_green", "✅"),
        "error":   ("light_red", "❌"),
        "warning": ("light_yellow", "⚠️"),
        "debug":   ("light_magenta", "🐛"),
    }

    color, emoji = color_map.get(type, ("white", ""))
    print(colored(f"{emoji} {message}", color))
