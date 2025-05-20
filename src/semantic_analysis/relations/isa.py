from src.semantic_analysis.relations.base import BaseRelationExtractor
from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token


class GenericExtractor(BaseRelationExtractor):
	relation_name = "r_isa"
	
	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		
		if self._check_children_keys({'nsubj', 'cop'}, tree):
			objet = tree

			sujet = tree.children['nsubj'][0]
			pattern = tree.children['cop'][0]

			rel = self.create_relation(sujet, pattern, objet, self.relation_name)
			return [rel]
		return None
