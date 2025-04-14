from src.semantic_analysis.semantic_analyzer import SemanticAnalyzer
from src.utils.database import init_database
from src.utils.console import print_color


def main():
	db_path = "database/medical_knowledge.db"
	init_database(db_path)
	analyzer = SemanticAnalyzer()
	print_color("Début de l'analyse sémantique...")
	analyzer.analyze_corpus()
	print_color("Analyse terminée avec succès !", "success")


if __name__ == "__main__":
	main()