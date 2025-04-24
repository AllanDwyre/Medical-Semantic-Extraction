from src.semantic_analysis.relations.base import BaseRelationExtractor

class SynonymExtractor(BaseRelationExtractor):
	relation_name = "r_syn"
	
	def extract(self, text: str, context: dict = {}) -> list[tuple[str, str]]:
		"""
		Extrait des tuples (sujet, objet) pour une relation donnée.
		"""
		raise NotImplementedError
