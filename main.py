from src.semantic_analysis.semantic_analyzer import SemanticAnalyzer
from src.utils.database import init_database, populate_relation_types
from src.utils.console import print_color
from src.utils.helper import create_json_file
from pathlib import Path
import argparse

def main(is_debug : bool):
	db_path = "database/medical_knowledge.db"
	print_color("Création de la DB...")
	init_database(db_path)
	print_color("Alimenter les types de relations...")
	populate_relation_types(db_path)

	analyzer = SemanticAnalyzer()
	print_color("Début de l'analyse sémantique...")
	stats = analyzer.analyze_corpus()
	if stats.get('error_count', 0) > 0:
		print_color("Analyse terminée avec des erreurs...", "warning")
		if is_debug:
			print_color("	Regarder dans log.json pour comprendre la raison", "warning")
			create_json_file(Path(), "log", stats)
	else:
		print_color("Analyse terminée avec succès !", "success")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Lance l'analyse sémantique.")
	parser.add_argument(
		"--debug", "-D",
		action="store_true",
		help="Activer le mode debug (pas de suppression de la DB, logs supplémentaires)"
	)

	args = parser.parse_args()
	main(args.debug)