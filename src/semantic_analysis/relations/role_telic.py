from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder
class RoleTelicExtractor(BaseRelationExtractor):
	"""
	r_telic_role : 
	Le rôle télique indique la fonction du nom ou du verbe.
	
		pénicillines sont utilisées dans le traitement d'infections bactériennes.
		pénicillines r_telic_role traitement infections bactériennes
	"""
	relation_name = "r_telic_role"
	
	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj:pass'}).build(),
			objet = PatternBuilder().child_has_tag({'obl:mod'}).build(),
			pattern = PatternBuilder().check_pos({'VERB', 'NOUN'}).build(),
		),
		]
	
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations