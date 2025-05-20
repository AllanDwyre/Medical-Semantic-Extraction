import multiprocessing
from tqdm import tqdm
from pathlib import Path

from src.utils.helper import load_nlp_model, clear_directory
from src.semantic_analysis.content_analyser import ContentAnalyzer
from src.semantic_analysis.infobox_analyzer import InfoboxAnalyzer
from src.semantic_analysis.document import DocumentInfo, ProcessedDocument
import traceback

# Variables globales par process
nlp_model = None
content_analyzer = None
infobox_analyzer = None

def initializer():
	global nlp_model, content_analyzer, infobox_analyzer
	nlp_model = load_nlp_model()
	content_analyzer = ContentAnalyzer(nlp_model)
	infobox_analyzer = InfoboxAnalyzer(nlp_model)


def process_document(json_file_path):
	info = DocumentInfo.from_json_file(json_file_path)

	try:
		infobox_rel = infobox_analyzer.analyze_infobox(info.title, info.infobox)
	except Exception as e:
		return {"error": f"[INFOBOX]", "file": info.title, "message": str(e).split("\n")[0]}

	try:
		content_rel = content_analyzer.analyse_content(info.content)
	except Exception as e:
		return {"error": f"[CONTENT]", "file": info.title, "message": str(e).split("\n")[0]}

	try:
		return ProcessedDocument(info, relation_infobox=infobox_rel, relation_content=content_rel)
	except Exception as e:
		return {"error": f"[DOCBUILD]", "file": info.title, "message": str(e).split("\n")[0]}



class SemanticAnalyzer:
	def __init__(self, batch_size = 500, data_dir="data/raw", output_dir="data/processed", db_path="database/medical_knowledge.db", max_workers=4):
		self.data_dir = Path(data_dir)
		self.output_dir = Path(output_dir)
		self.db_path = Path(db_path)
		self.max_workers = max_workers
		self.batch_size = batch_size

		self.output_dir.mkdir(parents=True, exist_ok=True)
		clear_directory(output_dir)

	def yield_batch_files(self):
		batch = []
		for json_file in self.data_dir.glob("*.json"):
			batch.append(json_file)
			if len(batch) == self.batch_size:
				yield batch
				batch = []
		if batch:
			yield batch

	def analyze_corpus(self):
		all_errors = []
		total_processed = 0
		batch_num = 0

		for batch_files in self.yield_batch_files():
			batch_num += 1
			with tqdm(total=len(batch_files), desc=f"Batch {batch_num}", unit="file", colour='green') as pbar:
				with multiprocessing.Pool(
					processes=self.max_workers,
					initializer=initializer
				) as pool:
					for result in pool.imap_unordered(process_document, map(str, batch_files)):
						if isinstance(result, dict) and "error" in result:
							all_errors.append(result)
						else:
							result.save_to_database(self.db_path)
							total_processed += 1
						pbar.update(1)

		print(f"\n✅ Total documents analysés : {total_processed}")
		print(f"❌ Total erreurs : {len(all_errors)}")

		return {
			"analyzed_count": total_processed,
			"error_count": len(all_errors),
			"errors": all_errors
		}

	# 	Threads pool executor + batch 1k page (paramaters : batched_limit = 1000)
	#		- [x] Traitement processus parallèles par batch
	#		- [x] Sauvegarde au fur et à mesure
	# 	Analyse sémantique
	#		- [x] Analyse complète de infobox (key analyse: pattern matching) --> tres simple et con
	#		- [x] Analyse complète de content (preprocessing, dep parsin, balise)
	# 			- [x] Dependency Parsing
	# 			- [x] POS
	# 			- [x] Rule-Matching classification -> 
	# 	Inférence pour evaluations des relations
	#		- [ ] Importer le projet inférence
	#		- [ ] Adapter le projet pour l'inférence de masse / Optimization
	

