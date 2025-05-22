from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder


class GenericExtractor(BaseRelationExtractor):
	relation_name = "r_isa"
	
	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj'}).build(),
			pattern = PatternBuilder().child_has_tag({'cop'}).check_lemma({"être"}).build(),
			objet = PatternBuilder().build(),
		),
		]
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations
