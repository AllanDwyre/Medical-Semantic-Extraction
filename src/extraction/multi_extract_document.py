import requests
import time
import os
import re
from bs4 import BeautifulSoup
import wikipediaapi
import random
import json
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor

from src.utils.console import print_color
from src.utils.helper import clear_directory, create_directory
import argparse

# Cache global pour les pages et catégories déjà visitées
page_cache = {}
category_cache = {}

# Limites et paramètres pour l'API
MAX_WORKERS_EXTRACT = 10  # Nombre maximum de threads pour l'extraction du contenu
MAX_WORKERS_RECURSIVE = 5  # Nombre maximum de threads pour la recherche récursive
API_DELAY = 0.2  # Délai entre les requêtes API pour éviter les blocages (à ajuster)
REQUEST_TIMEOUT = 10  # Timeout pour les requêtes HTTP

# Lock pour protéger les mises à jour de la barre de progression et d'autres ressources partagées
progress_lock = threading.Lock()
visited_lock = threading.Lock()

RECURSIVE_SEARCH = True

def get_medical_categories() -> list[str]:
	"""Récupère une liste de catégories médicales sur Wikipédia."""
	categories = [
		"Médecine", "Maladie", "Anatomie humaine", "Physiologie", "Pharmacologie",
		"Symptôme", "Diagnostic médical", "Traitement médical", "Chirurgie", 
		"Spécialité médicale", "Médecine d'urgence", "Pathologie",
		"Psychiatrie", "Neurologie", "Cardiologie", "Cancérologie", "Immunologie",
		"Épidémiologie", "Santé publique", "Terme médical"
	]
	categories_recursive = [
		"Patient", "Classification utilisée en médecine", "Physiologie", "Dépistage et diagnostic",
		"Génétique humaine", "Maladie", "Syndrome", "Traitement", "Terme médical", "Code ATC", "Santé publique", "Sémiologie médicale",
		"Médecine d'urgence", "Pathologie", "Spécialité en médecine", "Soins de santé", "Physiologie humaine", "Symptôme", "Diagnostic médical",
	]
	return categories_recursive if(RECURSIVE_SEARCH) else categories

def get_pages_in_category(category: str, limit: int = 1000) -> list[str]:
	"""Récupère des pages dans une catégorie donnée."""
	# Vérifier le cache
	if category in category_cache:
		return category_cache[category][:limit]
	
	session = requests.Session()
	url = "https://fr.wikipedia.org/w/api.php"
	
	pages = []
	continue_param = ""
	
	while len(pages) < limit:
		params = {
			"action": "query",
			"format": "json",
			"list": "categorymembers",
			"cmtitle": f"Catégorie:{category}",
			"cmlimit": "500",
			"cmtype": "page"
		}
		
		if continue_param:
			params["cmcontinue"] = continue_param
			
		try:
			response = session.get(url=url, params=params, timeout=REQUEST_TIMEOUT)
			data = response.json()
			
			if "query" in data and "categorymembers" in data["query"]:
				for page in data["query"]["categorymembers"]:
					pages.append(page["title"])
					if len(pages) >= limit:
						break
			
			if "continue" in data and len(pages) < limit:
				continue_param = data["continue"]["cmcontinue"]
			else:
				break
				
		except Exception as e:
			print(f"Erreur lors de la récupération des pages pour {category}: {e}")
			break
			
		time.sleep(API_DELAY)
	
	# Mettre en cache les résultats
	category_cache[category] = pages
	return pages[:limit]

def get_pages_recursive_mt(category: str, depth: int = 2, limit: int = 1000, 
						 shared_visited=None, shared_pages=None) -> None:
	"""Version multithread de la recherche récursive de pages."""
	if shared_visited is None:
		shared_visited = set()
	if shared_pages is None:
		shared_pages = []
	
	# Vérifier si la catégorie a déjà été visitée
	with visited_lock:
		if category in shared_visited or depth < 0:
			return
		shared_visited.add(category)
	
	# Vérifier le cache pour cette catégorie
	if category in category_cache:
		with visited_lock:
			shared_pages.extend(category_cache[category])
		print_color(f"Cache hit pour {category}: {len(category_cache[category])} pages")
		
		# Traiter les sous-catégories seulement si la profondeur le permet
		if depth > 0:
			subcategories = []
			# Code pour récupérer les sous-catégories...
			with ThreadPoolExecutor(max_workers=MAX_WORKERS_RECURSIVE) as executor:
				futures = [
					executor.submit(get_pages_recursive_mt, subcat, depth-1, limit, 
								   shared_visited, shared_pages)
					for subcat in subcategories
				]
				for future in futures:
					future.result()
		return
	
	# Si pas dans le cache, faire la requête API
	pages = []
	subcategories = []
	
	session = requests.Session()
	url = "https://fr.wikipedia.org/w/api.php"
	continue_param = ""

	while True:
		params = {
			"action": "query",
			"format": "json",
			"list": "categorymembers",
			"cmtitle": f"Catégorie:{category}",
			"cmlimit": "500",
			"cmtype": "page|subcat"
		}
		
		if continue_param:
			params["cmcontinue"] = continue_param

		try:
			response = session.get(url=url, params=params, timeout=REQUEST_TIMEOUT)
			data = response.json()

			if "query" in data:
				for member in data["query"]["categorymembers"]:
					if member["ns"] == 0:  # page
						pages.append(member["title"])
					elif member["ns"] == 14:  # subcategory
						sub_name = member["title"].split("Catégorie:", 1)[-1]
						subcategories.append(sub_name)

			if "continue" in data:
				continue_param = data["continue"]["cmcontinue"]
			else:
				break

		except Exception as e:
			print(f"Erreur dans {category}: {e}")
			break

		time.sleep(API_DELAY)
	
	# Mettre à jour le cache
	category_cache[category] = pages
	
	# Ajouter les pages trouvées au résultat partagé
	with visited_lock:
		shared_pages.extend(pages)
		page_count = len(shared_pages)
	
	print_color(f"{category} : {len(pages)} pages trouvées. Total actuel: {page_count}")
	
	# Traiter récursivement les sous-catégories en parallèle
	if depth > 0:
		with ThreadPoolExecutor(max_workers=MAX_WORKERS_RECURSIVE) as executor:
			futures = [
				executor.submit(get_pages_recursive_mt, subcat, depth-1, limit, 
							   shared_visited, shared_pages)
				for subcat in subcategories
			]
			for future in futures:
				future.result()

def extract_useful_sections(page):
	exclude_titles = {
		'Références', 'Voir aussi', 'Liens externes', 'Bibliographie',
		'Notes et références', 'Notes', "Sources de l'article", 'Articles connexes'
	}

	def traverse_sections(sections):
		content = []
		for section in sections:
			if section.title not in exclude_titles:
				content.append(f"{section.title}\n{section.text}")
				content.extend(traverse_sections(section.sections))
		return content

	main_content = [page.summary]
	main_content.extend(traverse_sections(page.sections))
	return "\n\n".join(main_content)

def clean(text):
	return re.sub("\(.*?\)", '', text)

def is_ignored_infobox_class(tag) -> bool:
	classes = tag.get("class", [])
	return bool({"hidden", "navigation-only", "entete"}.intersection(classes))

def extract_infobox_data(soup):
	infobox_data = {}

	tables = soup.find_all("table", class_=lambda c: c and "infobox" in c)
	for div in soup.find_all("div", class_=lambda c: c and "infobox" in c):
		tables.extend(div.find_all("table"))

	tables = list({id(t): t for t in tables}.values())

	for table in tables:
		if (caption := table.find("caption")) and not is_ignored_infobox_class(caption):
			title = caption.get_text(" ", strip=True)
			if title:
				infobox_data[title] = ""

		for row in table.find_all("tr"):
			if is_ignored_infobox_class(row):
				continue

			cols = row.find_all(["th", "td"])
			if len(cols) == 2:
				key = cols[0].get_text(" ", strip=True)
				value = cols[1].get_text(" ", strip=True)
				if key and value:
					infobox_data[key] = clean(value)
			elif len(cols) == 1 and cols[0].has_attr("colspan") and cols[0]["colspan"] == "2":
				if is_ignored_infobox_class(cols[0]):
					continue
				title = cols[0].get_text(" ", strip=True)
				if title:
					infobox_data[title] = ""

	return infobox_data

def extract_content_from_page(page_title: str, debugging: bool = False) -> dict:
	"""Extrait le contenu (texte et infobox) d'une page Wikipédia."""
	# Vérifier le cache
	if page_title in page_cache:
		return page_cache[page_title]
	
	wiki_wiki = wikipediaapi.Wikipedia(
		language='fr',
		user_agent='medical-nlp-project/1.0 (allan.golding-dwyre@etu.umontpellier.fr)'
	)
	page = wiki_wiki.page(page_title)
	
	if not page.exists():
		page_cache[page_title] = None
		return None
	
	# Récupérer le HTML pour extraire l'infobox
	url = f"https://fr.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
	try:
		response = requests.get(url, timeout=REQUEST_TIMEOUT)
		soup = BeautifulSoup(response.text, 'lxml')
		
		infobox_data = extract_infobox_data(soup)
		main_text = extract_useful_sections(page)
		
		full_content = {
			"url": url,
			"titre": clean(page_title),
			"infobox": infobox_data,
			"contenu": clean(main_text)
		}
		
		page_cache[page_title] = full_content
		return full_content
		
	except Exception as e:
		print(f"Erreur lors de l'extraction de {page_title}: {e}")
		page_cache[page_title] = None
		return None

def save_to_file(content: dict, page_title: str, directory: str) -> bool:
	"""Sauvegarde le contenu dans un fichier."""
	if not content:
		return False
	
	safe_title = re.sub(r'[\\/*?:"<>|]', "_", page_title)
	file_path = os.path.join(directory, f"{safe_title}.json")
	
	try:
		with open(file_path, 'w', encoding='utf-8') as file:
			json.dump(content, file, ensure_ascii=False, indent=4)
		return True
	except Exception as e:
		print(f"Erreur lors de la sauvegarde de {page_title}: {e}")
		return False

def process_page(page_title, output_directory, progress_bar):
	"""Traite une seule page pour l'extraction multithreaded."""
	content = extract_content_from_page(page_title)
	success = save_to_file(content, page_title, output_directory)
	
	with progress_lock:
		progress_bar.update(1)
		if success:
			progress_bar.set_description(f"✅ {page_title[:30]}")
		else:
			progress_bar.set_description(f"❌ {page_title[:30]}")
	
	return success
	
def main(limit=50000) -> None:
	"""Fonction principale pour extraire les pages médicales de Wikipédia."""
	output_directory = os.path.join("data", "raw")
	create_directory(output_directory)
	clear_directory(output_directory)
	
	categories = get_medical_categories()
	
	# Structure de données pour le partage entre threads
	all_pages = []
	visited_categories = set()
	
	start_time = time.time()
	
	# Collecter des pages de chaque catégorie
	if RECURSIVE_SEARCH:
		# Version multithreaded pour la recherche récursive
		with ThreadPoolExecutor(max_workers=MAX_WORKERS_RECURSIVE) as executor:
			futures = [
				executor.submit(get_pages_recursive_mt, category, depth=2, limit=limit,
							  shared_visited=visited_categories, shared_pages=all_pages)
				for category in categories
			]
			for future in futures:
				future.result()
	else:
		# Version simple pour la recherche non récursive
		for category in categories:
			pages = get_pages_in_category(category)
			all_pages.extend(pages)
			print_color(f"{category} : {len(pages)} pages trouvées.")
	
	# Supprimer les doublons
	all_pages = list(set(all_pages))
	
	search_time = time.time() - start_time
	print_color(f"Recherche terminée en {search_time:.2f} secondes.", "info")
	print_color(f"Total de pages uniques trouvées: {len(all_pages)}", "success")
	
	# Si plus que la limite, sélectionner un échantillon aléatoire
	if len(all_pages) > limit:
		all_pages = random.sample(all_pages, limit)
		print_color(f"Sélection aléatoire de {limit} pages pour traitement.", "info")
	
	# Traiter chaque page avec ThreadPoolExecutor
	success_count = 0
	progress_bar = tqdm(total=len(all_pages), desc="📄 Traitement des pages", unit="page", colour='cyan')
	
	extract_start_time = time.time()
	
	with ThreadPoolExecutor(max_workers=MAX_WORKERS_EXTRACT) as executor:
		# Soumettre tous les travaux
		futures = [
			executor.submit(process_page, page_title, output_directory, progress_bar)
			for page_title in all_pages
		]
		
		# Collecter les résultats au fur et à mesure
		for future in futures:
			if future.result():
				success_count += 1
	
	extract_time = time.time() - extract_start_time
	total_time = time.time() - start_time
	
	print_color(f"Extraction terminée en {extract_time:.2f} secondes.", "info")
	print_color(f"Temps total d'exécution: {total_time:.2f} secondes.", "info")
	print_color(f"{success_count} pages sauvegardées avec succès sur {len(all_pages)} tentées.", "success")
	
	# Afficher des statistiques d'efficacité
	pages_per_second = success_count / extract_time if extract_time > 0 else 0
	print_color(f"Performance: {pages_per_second:.2f} pages par seconde", "info")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Programme principal avec option de visualisation")
	parser.add_argument("-F", "--fast", action="store_true", help="Fast search (not recursive categories search)")
	parser.add_argument("--limit", help="Maximum number of pages to extract", type=int)

	# Ajout de nouveaux paramètres pour contrôler le multithreading
	parser.add_argument("--extract-threads", type=int, default=MAX_WORKERS_EXTRACT, 
						help=f"Number of threads for content extraction (default: {MAX_WORKERS_EXTRACT})")
	parser.add_argument("--search-threads", type=int, default=MAX_WORKERS_RECURSIVE, 
						help=f"Number of threads for category search (default: {MAX_WORKERS_RECURSIVE})")
	parser.add_argument("--delay", type=float, default=API_DELAY, 
						help=f"Delay between API requests in seconds (default: {API_DELAY})")

	args = parser.parse_args()

	# Appliquer les paramètres de ligne de commande
	RECURSIVE_SEARCH = not args.fast
	MAX_WORKERS_EXTRACT = args.extract_threads
	MAX_WORKERS_RECURSIVE = args.search_threads
	API_DELAY = args.delay

	main(args.limit)