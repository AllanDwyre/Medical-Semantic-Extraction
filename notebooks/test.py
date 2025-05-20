import spacy
from dataclasses import dataclass, field 
import re

@dataclass
class Relation:
	pattern:		str
	relation_type:	str
	sujet:			str
	objet:			str
	start:			str = '' # only content source
	end:			str = '' # only content source
	source:			str = '' # infobox ou content

	def set_start_and_end(self, subjet : tuple[int,int], pattern: tuple[int,int], objet: tuple[int,int]) -> None:
		self.start += subjet[0] + ";" + pattern[0] + ";" +  objet[0]
		self.end += subjet[1] + ";" + pattern[1] + ";" +  objet[1]
	def get_start_end(self, attribute:str) -> tuple[int,int]: 
		"""Get the start & end of a attribute : (sujet, objet or pattern)"""
		st_suj, st_rel, st_obj = self.start.split(';')
		end_suj, end_rel, end_obj = self.end.split(';') 
		match attribute:
			case "sujet":
				return (st_suj, end_suj)
			case "pattern":
				return (st_rel, end_rel)
			case "objet":
				return (st_obj, end_obj)


class ContentAnalyzer:
	def __init__(self, nlp_model):
		self.nlp = nlp_model
		self.rejected_dep = ("DET", "CCONJ")

	def _extract_marked_entities(text):
		return re.findall(r"\[([^\[\]]+)\]", text)

	def analyse_content(self, content: str) -> list[Relation]:
		doc = self.nlp(content)

		for sent in doc.sents:
			for token in sent:
				if token.pos_ in self.rejected_dep:
					continue
				children = [(child, child.dep_) for child in token.children if child.pos_ not in self.rejected_dep]

				print(token, children)
		
		return []

nlp = spacy.load("fr_core_news_lg")  # Modèle français de grande taille
analyzer = ContentAnalyzer(nlp)

text = """
L'aspirine inhibe l'agrégation plaquettaire. Les plaquettes jouent un rôle essentiel dans la coagulation sanguine.
La pénicilline détruit la paroi cellulaire des bactéries, ce qui entraîne leur mort.
"""

relations = analyzer.analyse_content(text)
for relation in relations:
    print(f"{relation.subject} → {relation.predicate} → {relation.object}")