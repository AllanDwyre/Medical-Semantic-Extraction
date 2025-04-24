class BaseRelationExtractor:
	relation_name = "undefined"

	def extract(self, text: str, context: dict = {}) -> list[tuple[str, str]]:
		"""
		Extrait des tuples (sujet, objet) pour une relation donnée.
		"""
		raise NotImplementedError
