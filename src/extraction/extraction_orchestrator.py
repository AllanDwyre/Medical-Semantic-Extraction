
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import random
import json
import requests
import threading
import time
import os
import re

from src.utils.console import print_color
from src.utils.helper import clear_directory, create_directory
from src.extraction.wiki_content_extractor import WikiContentExtractor
from src.extraction.wiki_page_searcher import WikiPageSearcher
from src.extraction.wiki_infobox_extractor import WikiInfoboxExtractor
from src.extraction.wiki_category_analysis import WikiCategoryAnalysis

class WikiOrchestrator:
	def __init__(self, limit=50000, recursive=True, extract_threads=10, search_threads=5, delay=0.2):
		self.limit = limit
		self.output_directory = os.path.join("data", "raw")
		self.content = WikiContentExtractor()
		self.infobox = WikiInfoboxExtractor()
		self.category = WikiCategoryAnalysis()
		self.searcher = WikiPageSearcher(recursive, search_threads, delay, limit)
		self.extract_threads = extract_threads
		self.progress_lock = threading.Lock()
		self.session = requests.Session()

	def extract_content_from_page(self, page_title: str):
		url = f"https://fr.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
		try:
			response = self.session.get(url, timeout=10)
			soup = BeautifulSoup(response.text, 'lxml')

			categories, is_ok = self.category.extract(soup)

			if not is_ok:
				return None
			
			infobox = self.infobox.extract(soup)
			main_text = self.content.extract(soup)

			content = {
				"url": url,
				"titre": page_title,
				"categories": categories,
				"infobox": infobox,
				"contenu": main_text
			}
			return content
		except Exception as e:
			print(f"Erreur lors de l'extraction de {page_title}: {e}")
			return None

	def save_to_file(self, content, page_title):
		if not content:
			return False
		safe_title = re.sub(r'[\\/*?:"<>|]', "_", page_title)
		file_path = os.path.join(self.output_directory, f"{safe_title}.json")
		try:
			with open(file_path, 'w', encoding='utf-8') as file:
				json.dump(content, file, ensure_ascii=False, indent=4)
			return True
		except Exception as e:
			print(f"Erreur lors de la sauvegarde de {page_title}: {e}")
			return False

	def process_page(self, page_title, progress_bar: tqdm):
		content = self.extract_content_from_page(page_title)
		if not content:
			progress_bar.total = progress_bar.total - 1
			# progress_bar.write(f"{page_title} à été exlu")
			return False
		success = self.save_to_file(content, page_title)
		with self.progress_lock:
			progress_bar.update(1)
			progress_bar.set_description(f"{'✅' if success else '❌'} {page_title[:30]}")
		return success

	def run(self):
		create_directory(self.output_directory)
		clear_directory(self.output_directory)

		start_time = time.time()

		all_pages = self.searcher.run()
		extracted_pages = set()
		success_count = 0
		remaining = min(len(all_pages), self.limit)
		while (remaining > 0) :
			
			batch_success_count = 0
			batch = all_pages[:remaining]
			if len(all_pages) > remaining:
				batch = random.sample(all_pages, remaining)
				print_color(f"Total de pages aléatoirement sélectionner: {len(batch)}", "info")
				
			progress_bar = tqdm(total=len(batch), desc="📄 Traitement des pages", unit="page", colour='cyan')
			with ThreadPoolExecutor(max_workers=self.extract_threads) as executor:
				futures = {
							executor.submit(self.process_page, title, progress_bar) : title
							for title in batch
					}
				for future in futures:
					title = futures[future]
					extracted_pages.add(title)
					if future.result():
						success_count += 1
						batch_success_count += 1

			all_pages = [p for p in all_pages if p not in extracted_pages]
			remaining = remaining - batch_success_count
			if len(all_pages) == 0:
				break

		elapsed = time.time() - start_time
		print_color(f"{success_count} pages sauvegardées avec succès.", "success")
		print_color(f"Temps total: {elapsed:.2f}s", "info")
		print_color(f"Performance: {success_count / elapsed:.2f} pages/s", "info")


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description="Scraper médical Wikipédia")
	parser.add_argument("-F", "--fast", action="store_true", help="Recherche non récursive")
	parser.add_argument("--limit", type=int, default=50000, help="Nombre max de pages")
	parser.add_argument("--extract-threads", type=int, default=10)
	parser.add_argument("--search-threads", type=int, default=5)
	parser.add_argument("--delay", type=float, default=0.05)
	args = parser.parse_args()

	orchestrator = WikiOrchestrator(
		limit=args.limit,
		recursive=not args.fast,
		extract_threads=args.extract_threads,
		search_threads=args.search_threads,
		delay=args.delay
	)
	orchestrator.run()