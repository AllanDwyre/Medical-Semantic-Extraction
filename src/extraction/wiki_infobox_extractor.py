import re
from bs4 import BeautifulSoup

class WikiInfoboxExtractor:
	def __init__(self):
		self.ignored_classes = {"hidden", "navigation-only", "entete"}

	def is_ignored(self, tag) -> bool:
		classes = tag.get("class", [])
		return any(c in self.ignored_classes for c in classes)

	def clean(self, text: str) -> str:
		return re.sub(r"\(.*?\)", "", text).strip()

	def extract(self, soup: BeautifulSoup) -> dict:
		infobox_data = {}

		# Collect all infobox tables (direct or nested in divs)
		tables = soup.select("table.infobox")
		for div in soup.select("div.infobox"):
			tables.extend(div.select("table"))

		# Deduplicate tables
		tables = list({id(t): t for t in tables}.values())

		for table in tables:
			# Handle caption as title if needed
			caption = table.find("caption")
			if caption and not self.is_ignored(caption):
				title = caption.get_text(" ", strip=True)
				if title:
					infobox_data[title] = ""

			# Extract key-value pairs
			for row in table.find_all("tr"):
				if self.is_ignored(row):
					continue

				cols = row.find_all(["th", "td"])
				if len(cols) == 2:
					key = cols[0].get_text(" ", strip=True)
					val = cols[1].get_text(" ", strip=True)
					if key and val and not key.startswith("Voir/Editer") and not val.startswith("Voir/Editer"):
						infobox_data[key] = self.clean(val)

				elif len(cols) == 1 and cols[0].has_attr("colspan") and cols[0]["colspan"] == "2":
					if self.is_ignored(cols[0]):
						continue
					title = cols[0].get_text(" ", strip=True)
					if title:
						infobox_data[title] = ""

		return infobox_data