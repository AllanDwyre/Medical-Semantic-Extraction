from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder


class ConsequenceExtractor(BaseRelationExtractor):
	relation_name = "r_has_conseq"
	
	lemma_pattern = {'induire'}

	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj'}).check_pos({'NOUN'}).build(),
			pattern = PatternBuilder().check_pos({'VERB'}).check_lemma(lemma_pattern).build(),
			objet = PatternBuilder().child_has_tag({'obj'}).build(),
		),
		]
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations
