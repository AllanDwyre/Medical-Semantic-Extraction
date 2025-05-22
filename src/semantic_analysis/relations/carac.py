from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder

class CaracteristicExtractor(BaseRelationExtractor):
	relation_name = "r_carac"
	
	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj'}).build(),
			objet = PatternBuilder().child_has_tag({'amod'}).build(),
			pattern = PatternBuilder().child_has_tag({'cop'}).build(),
		),
		]
	
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations