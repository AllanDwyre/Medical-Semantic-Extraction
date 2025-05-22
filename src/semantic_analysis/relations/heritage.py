from src.semantic_analysis.relations.base import BaseRelationExtractor, Relation, Dependency, BasicToken

class HeritageExtractor(BaseRelationExtractor):

	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		if tree.head is None:
			return None
		
		if self._check_children_keys({'conj'}, tree):
			parent = tree

			et_child_dep = tree.children['conj'][0]

			if 'cc' not in et_child_dep.children:
				return
			
			cc = et_child_dep.children['cc'][0]
			if cc.token.text.lower() != "et":
				return
			
			infered_rels = [rel for rel in known_relations if rel.sujet == parent.token.text or rel.objet == parent.token.text]
			relations = []
			for infered_rel in infered_rels:
				sujet = et_child_dep if infered_rel.sujet == parent.token.text else BasicToken(infered_rel.sujet, int(infered_rel.get_start_end("sujet")[0]))
				objet = et_child_dep if infered_rel.objet == parent.token.text else BasicToken(infered_rel.objet, int(infered_rel.get_start_end("objet")[0]))
				pattern = BasicToken(infered_rel.pattern, int(infered_rel.get_start_end("pattern")[0]))
				
				
				rel = self.create_relation(sujet, pattern, objet, infered_rel.relation_type)
				relations.append(rel)

			return relations
		return None
