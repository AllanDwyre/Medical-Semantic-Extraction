from src.semantic_analysis.relations.base import BaseRelationExtractor
from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token

class CaracteristicExtractor(BaseRelationExtractor):
	relation_name = "r_caract"
	
	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		"""
		Extrait les relations de la phrase pour une relation donnée.
		"""
		
		if self._check_children_keys({'amod', 'nsubj', 'cop'}, tree):

			sujet = tree.children['nsubj'][0]
			pattern = tree.children['cop'][0] # le verbe 'être' aussi
			
			relations = []
			for objet in tree.children['amod']:

				rel = self.create_relation(sujet, pattern, objet, self.relation_name)
				relations.append(rel)

			return relations
		return None
