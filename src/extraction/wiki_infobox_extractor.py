import re
from bs4 import BeautifulSoup

class WikiInfoboxExtractor:
	def __init__(self):
		pass

	def is_ignored_infobox_class(self, tag) -> bool:
		classes = tag.get("class", [])
		return bool({"hidden", "navigation-only", "entete"}.intersection(classes))

	def clean(self, text) -> str:
		return re.sub("\(.*?\)", '', text)

	def extract(self, soup: BeautifulSoup) -> dict:
		infobox_data = {}
		tables = soup.find_all("table", class_=lambda c: c and "infobox" in c)
		for div in soup.find_all("div", class_=lambda c: c and "infobox" in c):
			tables.extend(div.find_all("table"))
		tables = list({id(t): t for t in tables}.values())

		for table in tables:
			if (caption := table.find("caption")) and not self.is_ignored_infobox_class(caption):
				title = caption.get_text(" ", strip=True)
				if title:
					infobox_data[title] = ""

			for row in table.find_all("tr"):
				if self.is_ignored_infobox_class(row):
					continue
				cols = row.find_all(["th", "td"])
				if len(cols) == 2:
					key = cols[0].get_text(" ", strip=True)
					value = cols[1].get_text(" ", strip=True)
					if key and value and not key.startswith("Voir/Editer") and not value.startswith("Voir/Editer"):
						infobox_data[key] = self.clean(value)
				elif len(cols) == 1 and cols[0].has_attr("colspan") and cols[0]["colspan"] == "2":
					if self.is_ignored_infobox_class(cols[0]):
						continue
					title = cols[0].get_text(" ", strip=True)
					if title:
						infobox_data[title] = ""

		return infobox_data