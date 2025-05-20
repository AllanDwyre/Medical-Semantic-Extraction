import threading
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from src.utils.console import print_color

class WikiPageSearcher:
	def __init__(self, recursive=True, max_threads=5, api_delay=0.2, limit=50000):
		self.recursive = recursive
		self.max_threads = max_threads
		self.api_delay = api_delay
		self.page_cache = {}
		self.page_cache = {}
		self.category_cache = {}
		self.session = requests.Session()
		self.visited_lock = threading.Lock()
		self.limit = limit
		self.exclude_categories = self._get_excludes_category()

	def _get_excludes_category(self):
		excluded = set()
		url = "https://fr.wikipedia.org/w/api.php"
		params = {
			"action": "query",
			"format": "json",
			"list": "categorymembers",
			"cmtitle": "Catégorie:Médecin par spécialité",
			"cmtype": "subcat",
			"cmlimit": "max"
		}
		try:
			while True:
				response = self.session.get(url, params=params, timeout=10)
				data = response.json()
				for member in data.get("query", {}).get("categorymembers", []):
					# Extrait juste le nom de la sous-catégorie
					cat_name = member["title"].replace("Catégorie:", "")
					excluded.add(cat_name.lower())
				
				if "continue" in data:
					params["cmcontinue"] = data["continue"]["cmcontinue"]
				else:
					break

		except Exception as e:
			print_color(f"Erreur lors de la récupération des sous-catégories à exclure : {e}", "error")

		return excluded

	def _get_categories(self):
		base = [
			"Page utilisant P492",  "Page utilisant P699", "Page utilisant P557", 
			"Page utilisant P3201", "Page utilisant P780",
			"Médecine", "Maladie", "Anatomie humaine", "Physiologie", "Pharmacologie",
			"Symptôme", "Diagnostic médical", "Traitement médical", "Chirurgie",
			"Spécialité médicale", "Médecine d'urgence", "Pathologie",
			"Psychiatrie", "Neurologie", "Cardiologie", "Cancérologie", "Immunologie",
			"Épidémiologie", "Terme médical",
		]
		recursive = [
			"Page utilisant P492",  "Page utilisant P699", "Page utilisant P557", 
			"Page utilisant P3201", "Page utilisant P780",
			"Patient", "Classification utilisée en médecine", "Physiologie", "Dépistage et diagnostic",
			"Génétique humaine", "Maladie", "Syndrome", "Traitement", "Terme médical", "Code ATC", "Sémiologie médicale",
			"Médecine d'urgence", "Pathologie", "Spécialité en médecine", "Soins de santé", "Physiologie humaine", "Symptôme", "Diagnostic médical",
			"Biologie médicale"
		]
		return recursive if self.recursive else base

	def _get_pages_recursive_mt(self, category, depth=0, limit=1000, shared_visited=None, shared_pages=None):
		if shared_visited is None:
			shared_visited = set()
		if shared_pages is None:
			shared_pages = []

		with self.visited_lock:
			if category in shared_visited or depth < 0:
				return
			shared_visited.add(category)

		if category in self.category_cache:
			with self.visited_lock:
				shared_pages.extend(self.category_cache[category])
			return

		
		url = "https://fr.wikipedia.org/w/api.php"
		pages, subcategories = [], []
		continue_param = ""

		while True:
			params = {
				"action": "query", "format": "json", "list": "categorymembers",
				"cmtitle": f"Catégorie:{category}", "cmlimit": "500", "cmtype": "page|subcat"
			}
			if continue_param:
				params["cmcontinue"] = continue_param

			try:
				response = self.session.get(url=url, params=params, timeout=10)
				data = response.json()
				for member in data.get("query", {}).get("categorymembers", []):
					if member["ns"] == 0:
						pages.append(member["title"])
					elif member["ns"] == 14:
						sub_name = member["title"].split("Catégorie:", 1)[-1]
						if sub_name.lower() not in self.exclude_categories and sub_name.lower() not in ["institut", "étude"]:
							subcategories.append(sub_name)
						# else:
						# 	print_color(f"Catégorie exclu : {sub_name}", "debug")
				if "continue" in data:
					continue_param = data["continue"]["cmcontinue"]
				else:
					break
			except Exception as e:
				print(f"Erreur dans {category}: {e}")
				break

			time.sleep(self.api_delay)

		print_color(f"{category} : {len(pages)} pages trouvées.", "muted", end='\r', same_line=True)

		self.category_cache[category] = pages
		with self.visited_lock:
			shared_pages.extend(pages)

		if depth > 0:
			with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
				futures = [
					executor.submit(self._get_pages_recursive_mt, subcat, depth - 1, limit, shared_visited, shared_pages)
					for subcat in subcategories
				]
				for future in futures:
					future.result()

	def run(self):
		all_pages, visited = [], set()

		print_color("Démarrage de la collecte de pages...", "info")
		
		depth = 2 if self.recursive else 0
		with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
			futures = [
				executor.submit(self._get_pages_recursive_mt, cat, depth, self.limit, visited, all_pages)
				for cat in self._get_categories()
			]
			for future in futures:
				future.result()

		all_pages = list(set(all_pages))
		print_color(f"Total de pages uniques trouvées: {len(all_pages)}", "success")
		
		return all_pages