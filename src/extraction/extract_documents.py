import requests
import time
import os
import re
from bs4 import BeautifulSoup
import wikipediaapi
import random
import json
from tqdm import tqdm

from src.utils.console import print_color
from src.utils.helper import clear_directory, create_directory
import argparse


RECURSIVE_SEARCH = True

# https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:M%C3%A9decine
# ? on peut faire une extraction récursive des catégories, on choisissant des catégories spécifique en root, et laisser l'algorithme decendre dans les sous catégories
# ? Si on fait ça on devra suprimé Médecine (qui à des catégorie pas intéressantes malheureusement)
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
			response = session.get(url=url, params=params)
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
			
		time.sleep(1)  # Respecter les limites de l'API
	
	return pages[:limit]
def get_pages_recursive(category: str, depth: int = 2, limit: int = 1000, visited=None) -> list[str]:
	if visited is None:
		visited = set()
	
	if category in visited or depth < 0:
		return []
	
	visited.add(category)
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
			response = session.get(url=url, params=params)
			data = response.json()

			if "query" in data:
				for member in data["query"]["categorymembers"]:
					if member["ns"] == 0:  # page
						pages.append(member["title"])
					elif member["ns"] == 14:  # subcategory
						sub_name = member["title"].split("Catégorie:", 1)[-1]
						subcategories.append(sub_name)
						print_color(f"Nouvelles sous catégorie trouvée : {sub_name}")

			if "continue" in data:
				continue_param = data["continue"]["cmcontinue"]
			else:
				break

		except Exception as e:
			print(f"Erreur dans {category}: {e}")
			break

		time.sleep(1)
		print("\n")
		print_color(f"{category} : {len(pages)} pages trouvées.")
	# Recurse into subcategories
	for subcat in subcategories:
		pages.extend(get_pages_recursive(subcat, depth=depth - 1, limit=limit, visited=visited))

	return pages[:limit]

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
				# Appel récursif pour les sous-sections
				content.extend(traverse_sections(section.sections))
		return content

	main_content = [page.summary]
	main_content.extend(traverse_sections(page.sections))
	return "\n\n".join(main_content)


def clean_main(text):
	return re.sub("\(.*\)", '', text)

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
					infobox_data[key] = value
			elif len(cols) == 1 and cols[0].has_attr("colspan") and cols[0]["colspan"] == "2":
				if is_ignored_infobox_class(cols[0]):
					continue
				title = cols[0].get_text(" ", strip=True)
				if title:
					infobox_data[title] = ""

	return infobox_data


def extract_content_from_page(page_title: str, debugging: bool = False) -> dict:
	"""Extrait le contenu (texte et infobox) d'une page Wikipédia."""
	wiki_wiki = wikipediaapi.Wikipedia(
		language='fr',
		user_agent='medical-nlp-project/1.0 (allan.golding-dwyre@etu.umontpellier.fr)'
	)
	page = wiki_wiki.page(page_title)
	
	if not page.exists():
		return None
	
	# Récupérer le HTML pour extraire l'infobox
	url = f"https://fr.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
	try:
		response = requests.get(url)
		soup = BeautifulSoup(response.text, 'html.parser')
		
		# Extraire l'infobox (table avec classe infobox)
		infobox_data = extract_infobox_data(soup)
		#debugging stuff
		# if debugging:
		# 	for table in soup.find_all("table"):
		# 		classes = table.get("class",[])
		# 		if classes and any("infobox" in c for c in classes):
		# 			print(f"✅✅✅✅✅✅✅✅ Infobox détectée pour la page : {page_title} (classes : {classes})")
				
		# infobox_data = {}
		# infobox_tables = soup.find_all("table", class_=lambda x: x and "infobox" in x)
		# for table in infobox_tables:
		# 	for row in table.find_all("tr"):
		# 		if th:=row.find("th") and row.find("td"):
		# 			if th.get("colspan") != "2":
		# 				key = th.get_text(strip=True)
		# 				value = row.find("td").get_text(strip=True)
		# 				if key and value:  # S'assurer que ni la clé ni la valeur ne sont vides
		# 					infobox_data[key] = value
		# 					# print(f"Ajout à l'infobox: {key} = {value}")
				

		# Extraire le texte principal
		main_text = extract_useful_sections(page)
		
		full_content = {
			"url": url,
			"titre": page_title,
			"infobox": infobox_data,
			"contenu": clean_main(main_text)
		}
		
		return full_content
		
	except Exception as e:
		print(f"Erreur lors de l'extraction de {page_title}: {e}")
		return None

def save_to_file(content: dict, page_title: str, directory: str) -> bool:
	"""Sauvegarde le contenu dans un fichier."""
	if not content:
		return False
	
	# Nettoyer le titre pour en faire un nom de fichier valide
	safe_title = re.sub(r'[\\/*?:"<>|]', "_", page_title)
	file_path = os.path.join(directory, f"{safe_title}.json")
	
	try:
		with open(file_path, 'w', encoding='utf-8') as file:
			json.dump(content, file, ensure_ascii=False, indent=4)
		return True
	except Exception as e:
		print(f"Erreur lors de la sauvegarde de {page_title}: {e}")
		return False
	
def main(limit = 50000) -> None:
	"""Fonction principale pour extraire les pages médicales de Wikipédia."""
	output_directory = os.path.join("data", "raw")
	create_directory(output_directory)
	clear_directory(output_directory)
	
	categories = get_medical_categories()
	all_pages = []
	
	# Collecter des pages de chaque catégorie
	for category in categories:
		pages = get_pages_recursive(category) if(RECURSIVE_SEARCH) else get_pages_in_category(category)
		all_pages.extend(pages)
		print_color(f" {category} : {len(pages)} pages trouvées.")
		
	# Supprimer les doublons
	all_pages = list(set(all_pages))
	print_color(f"Total de pages uniques trouvées: {len(all_pages)}", "success")
	
	# Si plus de 50000 pages, sélectionner un échantillon aléatoire
	if len(all_pages) > limit:
		all_pages = random.sample(all_pages, limit)
	
	# Traiter chaque page
	success_count = 0
	progress_bar = tqdm(all_pages, desc="📄 Traitement des pages", unit="page", colour='cyan')

	for page_title in progress_bar:
		progress_bar.set_description("📄 Traitement de la page " + page_title[:50])  
		content = extract_content_from_page(page_title)
		if save_to_file(content, page_title, output_directory):
			success_count += 1
		
		# Attendre entre les requêtes pour respecter les limites de l'API
		time.sleep(1)
	
	print_color(f"Extraction terminée. {success_count} pages sauvegardées avec succès.", "success")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Programme principal avec option de visualisation")
	parser.add_argument("-F", "--fast", action="store_true", help="Fast search (not recursive categories search)")
	parser.add_argument("limit", help="Fast search (not recursive categories search)", type=int, default=200)
	args = parser.parse_args()

	RECURSIVE_SEARCH = not args.fast
	main(args.limit)