from termcolor import colored

def print_color(message, type="info", end="\n", same_line=False):
	"""Affiche un message coloré selon le type."""
	color_map = {
		"info":    ("light_cyan", "ℹ️"),
		"success": ("light_green", "✅"),
		"error":   ("light_red", "❌"),
		"warning": ("light_yellow", "⚠️"),
		"debug":   ("light_magenta", "🐛"),
		"muted":   ("dark_grey", "…")
	}

	color, emoji = color_map.get(type, ("white", ""))
	prefix = "\033[K" if same_line else ""
	print(prefix + colored(f"{emoji} {message}", color), end=end, flush=True)
