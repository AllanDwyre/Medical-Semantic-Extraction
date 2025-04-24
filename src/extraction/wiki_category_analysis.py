import re
from bs4 import BeautifulSoup

class WikiCategoryAnalysis :
	def __init__(self):
			# contain only hidden class that we dont want (person, institut)
			# * Mettre en minuscule
			self.ignored_classes = {
				"p106",						# Occupations (donc personne avec un travail)
				"p569",						# Contenant une Date de naissance
				"p27",						# Contenant une pays de nationalité
				"biographie",
				"article biographique",
				"organisation",				# pour enlever les organisation / institue
				"p3608", 					# contenant un numéro européen de TVA (lié au entreprise et organisation)
				"p1320", 					# contenant identifiant OpenCorporates d'une entreprise(lié au entreprise et organisation)
				"p1616", 					# contenant une numéro SIREN
				"p1454", 					# contenant une forme juridique
				"p1562", 					# contenant un identifiant de film (on ne veut pas de film)
				} 
			 # contain only hidden class that we find an value to put
			self.important_classes = {
				"p699" :  "Disease Ontology",
				"P557" :  "Disease DB",
				}
			self.hidden_categories_id = "mw-hidden-catlinks"
			self.public_categories_id = "mw-normal-catlinks"

	def _check_hidden(self, hidden_soup : BeautifulSoup) -> bool:
		if hidden_soup is None:
			return True
		
		for a in hidden_soup.find_all('a'):
			text = a.get_text().lower()

			# Check if any ignored_class matches exactly or as a word
			for ignored in self.ignored_classes:
				# If it's a property like p106 and we need a perfect match
				if re.fullmatch(r'p\d+', ignored):
					if text.strip() == ignored:
						return False
				else:
					# Otherwise do substring match (partial match)
					if ignored in text:
						return False
		return True

	def _extract_categories(self, public_soup : BeautifulSoup, hidden_soup : BeautifulSoup) -> list[str]:
		categories = []

		if public_soup is None:
			return categories
		
		for a in public_soup.find_all('a'):
			categories.append(a.get_text())

		if hidden_soup is None:
			return categories
		
		for a in hidden_soup.find_all('a'):
			if a.get_text().lower() in self.important_classes :
				categories.append(self.important_classes[a.get_text().lower()])

		return categories


	def extract(self, soup: BeautifulSoup) -> tuple[list[str], bool]:
		hidden_soup = soup.find(id = self.hidden_categories_id)
		public_soup = soup.find(id = self.public_categories_id)

		is_ok = self._check_hidden(hidden_soup)

		if not is_ok:
			return ([], False)
		
		return (self._extract_categories(public_soup, hidden_soup), True)