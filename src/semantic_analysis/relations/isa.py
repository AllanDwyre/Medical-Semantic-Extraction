from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder


class GenericExtractor(BaseRelationExtractor):
	relation_name = "r_isa"
	
	rules = [
		PatternMatch(
			match_name= "Sujet COP NOM",
			sujet = PatternBuilder().child_has_tag({'nsubj'}).check_pos({'NOUN'}).build(),
			pattern = PatternBuilder().child_has_tag({'cop'}).check_lemma({"être"}).build(),
			objet = PatternBuilder().check_pos({'NOUN'}).build(),
		),
		PatternMatch(
			match_name= "Traversal pronom (permet de chosir le mot apres le pronom)",
			sujet = PatternBuilder().child_has_tag({'nsubj'}).check_pos({'NOUN'}).build(),
			pattern = PatternBuilder().child_has_tag({'cop'}).check_lemma({"être"}).build(),
			objet = PatternBuilder().check_pos({'PRON'}).child_has_tag({'nmod'}).check_pos({'NOUN'}).build(),
		),
		]
	
	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		relations = []
		for rule in self.rules:
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations
