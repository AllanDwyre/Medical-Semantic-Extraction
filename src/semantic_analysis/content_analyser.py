from src.semantic_analysis.document import Relation
from spacy.tokens import Doc
import re

class ContentAnalyzer:
	def __init__(self, nlp_model):
		self.nlp = nlp_model

	def _extract_marked_entities(text):
		return re.findall(r"\[([^\[\]]+)\]", text)
	
	def _extract_entities(self, doc: Doc):
		return [{'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char}
				for ent in doc.ents]
	
	def _extract_dep(self, doc: Doc):
		return [{'text': token.text, 'dep': token.dep_, 'head': token.head}
				for token in doc]

	def analyse_content(self, content: str) -> list[Relation]:
		doc = self.nlp(content)
		return []
