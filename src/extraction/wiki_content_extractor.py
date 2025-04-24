import re
from bs4 import BeautifulSoup


class WikiContentExtractor:
	def __init__(self):
		self.exclude_titles = {
			'Références', 'Voir aussi', 'Liens externes', 'Lien externe', 'Bibliographie',
			'Notes et références', 'Notes', "Sources de l'article", 'Articles connexes',
			'Publications','Documentaire','Annexes','Biographie','Sources', 'Galerie',
			'Articles'
		}

	def extract_sections(self, soup: BeautifulSoup) -> str:
		content_div = soup.find("div", class_="mw-parser-output")
		if not content_div:
			return []

		content = ""
		in_excluded_section = False
		
		element:BeautifulSoup
		for element in content_div.children:
			if not getattr(element, "name", None) or any("bandeau" in c for c in element.get("class", [])):
				continue

			if "mw-heading" in element.get("class", []):
				header: BeautifulSoup = element.find(["h2", "h3", "h4", "h5", "h6"])
				title = header.get_text().strip()

				in_excluded_section = title in self.exclude_titles
				if not in_excluded_section:
					content += title + "\n"

				continue

			if not in_excluded_section and element.name in ["p", "ul", "ol"] and (text := self.process_text(element)):
				content += self.clean(text) + "\n"

		return content

	def clean(self, text):
		text = re.sub(r"\(.*?\)", '', text)			# parenthèses
		text = re.sub(r'\[\s*\]', '', text)			# crochets vides

		lines = text.splitlines()
		cleaned = [re.sub(r'\s+', ' ', line).strip() for line in lines if line.strip()]

		return "\n".join(cleaned)
	
	def process_text(self, soup: BeautifulSoup):

		for b in soup.find_all('b'):
			balisage = f"[{b.get_text()}]"
			b.replace_with(balisage)

		for a in soup.find_all('a'):
			href = a.get('href', '')
			text = a.get_text()
			if href.startswith('/wiki/') and ':' not in href:
				balisage = f"[{text}]"
				a.replace_with(balisage)
			else:
				a.replace_with("")

		for li in soup.find_all('li'):
			li.replace_with(f"- {li.get_text()}\n")
		
		return soup.get_text()
	
	def extract(self, page_soup: BeautifulSoup):
		return self.extract_sections(page_soup)
