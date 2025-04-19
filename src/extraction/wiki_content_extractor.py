from __future__ import annotations
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class Section:
	title: str
	level: str
	id: str = ""
	content: str = ""

class WikiContentExtractor:
	def __init__(self):
		self.exclude_titles = {
			'Références', 'Voir aussi', 'Liens externes', 'Bibliographie',
			'Notes et références', 'Notes', "Sources de l'article", 'Articles connexes',
			'Publications','Documentaire','Annexes','Biographie','Sources'
		}

	def scrape_summary(self, soup : BeautifulSoup) -> list[Section]:
		sections = [Section(title="Root", level="0")]

		exclude_level = []
		summary = soup.find(id="mw-panel-toc-list")

		if not summary:
			return sections
			
		for item in summary.find_all("a"):
			hierachy = item.find("span", class_="vector-toc-numb")

			if not hierachy:
				continue

			title = hierachy.find_next("span").get_text()
			hierachy_text = hierachy.get_text(strip=True)
			sectionId = item.get("href", "").lstrip("#")
			if hierachy_text.startswith(tuple(exclude_level)):
				continue

			if title in self.exclude_titles:
				exclude_level.append(hierachy_text)
			
			section = Section(id=sectionId, title=title, level=hierachy_text)
			sections.append(section)
		return sections

	def extract_intro(self, soup, sections):
		content_div = soup.find("div", class_="mw-parser-output")
		
		if not content_div:
			return ""
		
		content = []

		element:BeautifulSoup
		for element in content_div.children:
			if not getattr(element, "name", None):
				continue
				
			if element.get("class") and any("bandeau" in c for c in element.get("class", [])):
				continue

			if "mw-heading" in element.get("class", []):
				break
				
			if element.name in ["p", "ul", "ol"] and (text := self.process_text(element)):
				content.append(self.clean(text))
		
		return "\n".join(content)
		
	def populate_content(self, sections : list[Section], soup : BeautifulSoup) -> str:
		corpus = []
		for idx, section in enumerate(sections):
			
			if section.title in self.exclude_titles:
				continue

			if section.title == "Root":
				corpus.append(self.extract_intro(soup, sections))
				continue

			start_tag = soup.find(id=section.id) 
			if not start_tag:
				continue
			
			content = []
			for sibling in start_tag.find_all_next():
				if getattr(sibling, 'name', None) is None or any("bandeau" in c for c in sibling.get("class", [])):
					continue

				if idx + 1 < len(sections) and sibling.get("id") == sections[idx + 1].id:
					break

				if sibling.name in ["p", "ul", "ol"] and (text := self.process_text(sibling)):
					content.append(self.clean(text))

			section.content = " ".join(content)
			corpus.append(f"{section.title}\n{section.content}")

		return "\n\n".join(corpus)
	
	def clean(self, text):
		text = re.sub(r"\(.*?\)", '', text)			# parenthèses
		text = re.sub(r'\[\s*\]', '', text)			# crochets vides

		lines = text.splitlines()
		cleaned = [re.sub(r'\s+', ' ', line).strip() for line in lines if line.strip()]

		return "\n".join(cleaned)
	
	def process_text(self, soup: BeautifulSoup):
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
	
	def extract(self, page_soup : BeautifulSoup):
		sections = self.scrape_summary(page_soup)
		return self.populate_content(sections, page_soup)
