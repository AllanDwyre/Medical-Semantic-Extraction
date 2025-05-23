from typing import List
from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, PatternMatch, PatternBuilder, PatternCondition

def check_adjective(nodes: List[Dependency]) -> List[Dependency]:
	"""
		L’acrodermatite papuleuse infantile ou syndrome de Gianotti-Crosti est une maladie bénigne
		Sans cette fonction : infantile r_syn syndrome Gianotti-Crosti
		AVEC cette fonction : L’acrodermatite papuleuse infantile r_syn syndrome Gianotti-Crosti
	"""
	result = [node for node in nodes if node.token.pos_ != "ADJ"]
	
	adj_nodes = adj_nodes = [node for node in nodes if node not in result]

	for adj_node in adj_nodes:
		if not adj_node.head:
			return None
		
		if adj_node.head.token.pos_ != "ADJ":
			return adj_node.head
		
		check_adjective(adj_node.head)

	return result

class SynonymeExtractor(BaseRelationExtractor):
	relation_name = "r_syn"
	possible_patterns = {'désigner'}

	adjectif_condition = PatternCondition(step_name="adjective_condition", validator=check_adjective, description="Permet de récupérer le mot exacte")

	rules = [
			PatternMatch(
				match_name = "",
				sujet = PatternBuilder().child_has_tag({'nsubj'}).build(),
				pattern = PatternBuilder().child_has_tag({'xcomp'}).check_lemma(possible_patterns).build(),
				objet = PatternBuilder().start_from("pattern").child_has_tag({'obl:agent'}).build(),
			),
			PatternMatch(
				match_name = "",
				sujet = PatternBuilder().child_has_tag({'conj'}).check_pos({"not DET"}).add__custom(adjectif_condition).build(),
				pattern = PatternBuilder().start_from("sujet").child_has_tag({'cc'}).check_lemma({"ou"}).build(),
				objet = PatternBuilder().check_pos({"not DET"}).build(),
			),
		]