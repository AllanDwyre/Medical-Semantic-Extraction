import spacy
import webbrowser
import time
import os
import json
from pathlib import Path


def create_directory(directory) -> None:
	"""Crée un répertoire s'il n'existe pas."""
	
	if not os.path.exists(directory):
		os.makedirs(directory)
		
		print(f"Répertoire créé: {directory}")
		
def clear_directory(directory) -> None:
	"""Supprime tous les fichiers dans un répertoire donné."""
	for filename in os.listdir(directory):
		file_path = os.path.join(directory, filename)
		if os.path.isfile(file_path):
			os.remove(file_path)

def create_json_file(output_path:Path, filename: str, content: dict):
	output_path.mkdir(parents=True, exist_ok=True)
	file_path = output_path / f"{filename}.json"
	with open(file_path, 'w', encoding='utf-8') as f:
		json.dump(content, f, ensure_ascii=False, indent=4)
			
def load_nlp_model() -> spacy.Language:
	try:
		return spacy.load('fr_core_news_md')
	except OSError:
		from spacy.cli import download
		download('fr_core_news_md')
		return spacy.load('fr_core_news_md')
	
def open_localhost(url: str = "http://127.0.0.1:5000/") -> None:
	time.sleep(5)
	webbrowser.open_new_tab(url)