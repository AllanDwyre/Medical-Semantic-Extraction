from src.semantic_analysis.relations.base import BaseRelationExtractor
from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token

class RoleTelicExtractor(BaseRelationExtractor):
	"""
	r_telic_role : 
	Le rôle télique indique la fonction du nom ou du verbe.
	
		pénicillines sont utilisées dans le traitement d'infections bactériennes.
		pénicillines r_telic_role traitement infections bactériennes
	"""
	relation_name = "r_telic_role"
	
	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		if tree.token.pos_ not in {"VERB", "NOUN"}:
			return None
		
		if self._check_children_keys({'nsubj:pass', 'obl:mod'}, tree):

			sujet = tree.children['nsubj:pass'][0]
			objet = tree.children['obl:mod'][0]
			pattern = tree # le verbe 'utilisé, servir, destiner'
			rel = self.create_relation(sujet, pattern, objet, self.relation_name)
			return [rel]
		return None
	