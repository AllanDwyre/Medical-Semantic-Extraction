from src.semantic_analysis.relations.base import BaseRelationExtractor
from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token

class SynonymeExtractor(BaseRelationExtractor):
	relation_name = "r_syn"
	
	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		
		if self._check_children_keys({'conj'}, tree):
			objet = tree

			sujet = tree.children['conj'][0]

			if 'cc' not in sujet.children:
				return
			
			pattern = sujet.children['cc'][0]

			if pattern.token.text.lower() != "ou":
				return

			rel = self.create_relation(sujet, pattern, objet, self.relation_name)
			return [rel]
		return None
