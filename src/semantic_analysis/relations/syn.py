from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder


class SynonymeExtractor(BaseRelationExtractor):
	relation_name = "r_syn"
	possible_patterns = {'désigner'}

	rules = [
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'nsubj'}).build(),
			pattern = PatternBuilder().child_has_tag({'xcomp'}).check_lemma(possible_patterns).build(),
			objet = PatternBuilder().start_from("pattern").child_has_tag({'obl:agent'}).build(),
		),
		PatternMatch(
			sujet = PatternBuilder().child_has_tag({'conj'}).build(),
			pattern = PatternBuilder().start_from("sujet").child_has_tag({'cc'}).check_lemma({"ou"}).build(),
			objet = PatternBuilder().build(),
		),
		]
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose=False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations
