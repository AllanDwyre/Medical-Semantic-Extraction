from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, BasicToken

class HeritageExtractor(BaseRelationExtractor):

	def _get_element_from_rel(self, new_term, rel_term, parent_term, pos):
		# Pour illuster : 	rel_term	= "changement dans la colonne"
		#					parent_term = "colonne"
		#					rel_term	= "bassin"
		#					
		#					On va donc regarder si "colonne" est dans "changement dans la colonne"

		if parent_term in rel_term:
			return new_term
		
		return BasicToken(rel_term, int(pos[0]), int(pos[1]))

	def extract(self, tree: Dependency, known_relations : list[Relation], verbose = False) -> list[Relation] | None:
		if tree.head is None:
			return None
		
		parent = tree
		term = tree.get_child('conj')
		if not term:
			return [] 
		
		cc = term.get_child('cc')
		if not cc or not cc.check_lemma("et"):
			return []
		
		infered_rels = [rel for rel in known_relations if rel.sujet == parent.token.text or rel.objet == parent.token.text]
		relations = []

		for infered_rel in infered_rels:	
				sujet_pos = infered_rel.get_start_end("sujet")
				objet_pos = infered_rel.get_start_end("sujet")
				pattern_pos = infered_rel.get_start_end("pattern")

				sujet = self._get_element_from_rel(term, infered_rel.sujet, parent.token.text, sujet_pos)
				objet = self._get_element_from_rel(term, infered_rel.objet, parent.token.text, objet_pos)
				pattern = self._get_element_from_rel(term, infered_rel.pattern, parent.token.text, pattern_pos)
				
				
				self.create_relation(sujet, pattern, objet, infered_rel.relation_type, relations)
		return relations