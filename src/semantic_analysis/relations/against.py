from src.semantic_analysis.relations.base import BaseRelationExtractor
from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token

class AgainstExtractor(BaseRelationExtractor):
	relation_name = "r_against"
	
	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		if tree.token.pos_ != "VERB":
			return None

		if self._check_children_keys({'nsubj', 'obj'}, tree):

			sujet = tree.children['nsubj'][0]
			pattern = tree # le verbe 'detruit' aussi
			objet = tree.children['obj'][0]
			
			rel = self.create_relation(sujet, pattern, objet, self.relation_name)

			return [rel]
		return None
	