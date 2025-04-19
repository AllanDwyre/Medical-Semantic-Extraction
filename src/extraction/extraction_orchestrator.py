
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
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

class WikiOrchestrator:
	def __init__(self, limit=50000, recursive=True, extract_threads=10, search_threads=5, delay=0.2):
		self.limit = limit
		self.output_directory = os.path.join("data", "raw")
		self.page_cache = {}
		self.content = WikiContentExtractor()
		self.infobox = WikiInfoboxExtractor()
		self.searcher = WikiPageSearcher(recursive, search_threads, delay, limit)
		self.extract_threads = extract_threads
		self.progress_lock = threading.Lock()

	def extract_content_from_page(self, page_title: str):
		if page_title in self.page_cache:
			return self.page_cache[page_title]

		url = f"https://fr.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
		try:
			response = requests.get(url, timeout=10)
			soup = BeautifulSoup(response.text, 'lxml')
			infobox = self.infobox.extract(soup)
			main_text = self.content.extract(soup)

			content = {
				"url": url,
				"titre": page_title,
				"infobox": infobox,
				"contenu": main_text
			}
			self.page_cache[page_title] = content
			return content
		except Exception as e:
			print(f"Erreur lors de l'extraction de {page_title}: {e}")
			self.page_cache[page_title] = None
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

	def process_page(self, page_title, progress_bar):
		content = self.extract_content_from_page(page_title)
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

		progress_bar = tqdm(total=len(all_pages), desc="📄 Traitement des pages", unit="page", colour='cyan')
		success_count = 0
		with ThreadPoolExecutor(max_workers=self.extract_threads) as executor:
			futures = [
				executor.submit(self.process_page, title, progress_bar)
				for title in all_pages
			]
			for future in futures:
				if future.result():
					success_count += 1

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
	parser.add_argument("--delay", type=float, default=0.2)
	args = parser.parse_args()

	orchestrator = WikiOrchestrator(
		limit=args.limit,
		recursive=not args.fast,
		extract_threads=args.extract_threads,
		search_threads=args.search_threads,
		delay=args.delay
	)
	orchestrator.run()