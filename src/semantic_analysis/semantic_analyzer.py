import json
import concurrent.futures
from tqdm import tqdm
from pathlib import Path
from collections import Counter
from threading import Lock

from src.utils.helper import load_nlp_model, clear_directory, create_json_file
from src.utils.database import save_to_database

from src.semantic_analysis.content_analyser import ContentAnalyzer
from src.semantic_analysis.infobox_analyzer import InfoboxAnalyzer

class SemanticAnalyzer:
	def __init__(self, data_dir="data/raw", output_dir="data/processed", db_path="database/medical_knowledge.db", max_workers=4	):
		self.data_dir = Path(data_dir)
		self.output_dir = Path(output_dir)
		self.db_path = Path(db_path)
		self.max_workers = max_workers

		nlp_model = load_nlp_model()
		self.content_analyzer = ContentAnalyzer(nlp_model, nlp_model.Defaults.stop_words)
		self.infobox_analyzer = InfoboxAnalyzer(nlp_model)

		self.output_dir.mkdir(parents=True, exist_ok=True)
		clear_directory(output_dir)
		
		self.lock = Lock()

	def preprocess_document(self, json_file):
		"""Prétraite un document"""
		try:
			with open(json_file, 'r', encoding='utf-8') as f:
				data = json.load(f)

			title = data.get('titre', 'Sans titre')
			content = data.get('contenu', '')
			infobox = data.get('infobox', {})
			url = data.get('url', '')

			preprocessed_tokens = self.content_analyzer.preprocess_text(content)
			entities = self.content_analyzer.extract_entities(content)
			relations_text = self.content_analyzer.extract_relations(content)
			relations_infobox, infobox_keywords = self.infobox_analyzer.analyze_infobox(title, infobox)
			
			return {
				'file': json_file,
				'title': title,
				'content': content,
				'url': url,
				'infobox': infobox,
				'relations_text': relations_text,
				'relations_infobox': relations_infobox,
				'preprocessed_tokens': preprocessed_tokens,
				'infobox_keywords': infobox_keywords
			}
		except Exception as e:
			return {"error": str(e), "file": str(json_file)}

	def analyze_corpus(self):
		json_files = list(self.data_dir.glob('*.json'))
		preprocessed_documents = []
		errors = []

		# Étape 1: Prétraitement parallèle de tous les documents sans TF-IDF
		with tqdm(total=len(json_files), desc="Prétraitement des documents") as progress_bar:
			with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
				future_to_file = {executor.submit(self.preprocess_document, json_file): json_file for json_file in json_files}
				
				for future in concurrent.futures.as_completed(future_to_file):
					json_file = future_to_file[future]
					try:
						result = future.result()
						if "error" in result:
							errors.append(result)
							tqdm.write(f"Erreur lors du prétraitement de {json_file.stem}: {result['error']}")
						else:
							preprocessed_documents.append(result)
					except Exception as e:
						tqdm.write(f"Exception lors du prétraitement de {json_file.stem}: {e}")
						errors.append({"error": str(e), "file": str(json_file)})
					
					progress_bar.update(1)
					progress_bar.set_description(f"Prétraitement: {json_file.stem}")

		# Étape 2: Extraction des mots-clés TF-IDF sur tout le corpus
		if preprocessed_documents:
			tqdm.write("Extraction des mots-clés TF-IDF sur l'ensemble du corpus...")
			
			# Collecte des contenus et titres pour TF-IDF
			all_contents = [doc['content'] for doc in preprocessed_documents]
			all_titles = [doc['title'] for doc in preprocessed_documents]
			
			# Calcul TF-IDF sur tout le corpus
			keywords_results = self.content_analyzer.extract_keywords_tfidf(all_contents, all_titles)
			
			# Création de la version finale des documents avec les mots-clés
			analyzed_documents = []
			
			with tqdm(total=len(preprocessed_documents), desc="Finalisation des documents") as progress_bar:
				for i, doc in enumerate(preprocessed_documents):
					try:
						# Création du document final avec les mots-clés
						final_doc = {
							'title': doc['title'],
							'content': doc['content'],
							'url': doc['url'],
							'infobox': doc['infobox'],
							'keywords': keywords_results[i]['keywords'],
							'relations_text': doc['relations_text'],
							'relations_infobox': doc['relations_infobox']
						}

						# On ajoute le titre comme keywords
						title_keyword = {
							'keyword': doc['title'],
							'score': 1.0 
						}
						final_doc['keywords'].append(title_keyword)

						# On ajoute les infobox_keywords comme keywords
						for value in doc.get('infobox_keywords', []):
							infobox_value_keyword = {
								'keyword': value,
								'score': 0.8
							}
							final_doc['keywords'].append(infobox_value_keyword)
						
						# on supprime les doublons
						keywords_by_word = {}

						for kw in final_doc['keywords']:
							word = kw['keyword']
							score = kw['score']
							keywords_by_word[word] = max(score, keywords_by_word.get(word, 0))

						# Conversion en liste de dictionnaires
						final_doc['keywords'] = [
							{'keyword': k, 'score': s} for k, s in keywords_by_word.items()
						]
							
						analyzed_documents.append(final_doc)
						json_file = doc['file']
						create_json_file(self.output_dir, Path(json_file).stem, final_doc)
						
					except Exception as e:
						json_file = doc.get('file', 'unknown')
						tqdm.write(f"Exception lors de la finalisation de {Path(json_file).stem}: {e}")
						errors.append({"error": str(e), "file": str(json_file)})
					
					progress_bar.update(1)
					progress_bar.set_description(f"Finalisation: {Path(doc['file']).stem}")

			# Sauvegarde dans la base de données
			tqdm.write(f"Sauvegarde de {len(analyzed_documents)} documents dans la base de données...")
			save_to_database(str(self.db_path), analyzed_documents)
		
		return {
			"analyzed_count": len(preprocessed_documents) - len(errors),
			"error_count": len(errors),
			"errors": errors
		}