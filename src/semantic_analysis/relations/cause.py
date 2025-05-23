from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder


class CauseExtractor(BaseRelationExtractor):
	relation_name = "r_has_causatif"
	
	lemma_pattern = {'devoir'}

	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj'}).check_pos({'NOUN'}).build(),
			pattern = PatternBuilder().check_lemma(lemma_pattern).build(),
			objet = PatternBuilder().child_has_tag({'obj', 'obl:arg'}).build(),
		),
		]
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations
