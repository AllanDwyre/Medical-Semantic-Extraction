from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder

class AgainstExtractor(BaseRelationExtractor):
	relation_name = "r_against"
	
	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj'}).build(),
			objet = PatternBuilder().child_has_tag({'obj'}).build(),
			pattern = PatternBuilder().check_pos({'VERB'}).check_lemma({'contre'}).build(),
		),
		]
	
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations