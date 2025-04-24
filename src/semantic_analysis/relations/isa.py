from src.semantic_analysis.relations.base import BaseRelationExtractor

class GenericExtractor(BaseRelationExtractor):
	relation_name = "r_isa"
	
	def extract(self, text: str, context: dict = {}) -> list[tuple[str, str]]:
		"""
		Extrait des tuples (sujet, objet) pour une relation donnée.
		"""
		raise NotImplementedError
