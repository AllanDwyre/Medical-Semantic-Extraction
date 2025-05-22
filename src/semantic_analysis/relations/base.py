from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token

class BaseRelationExtractor:
	relation_name = "undefined"
	relation_source = "content"

	def _get_composite_words(self, tree: Dependency) -> CompositeToken | Token | BasicToken:
		"""Extrait les mots composés formés par un nom et ses modificateurs adjectivaux ou nominaux, récursivement"""
		if isinstance(tree, BasicToken):
			return tree
		
		if ('amod' in tree.children or 'nmod' in tree.children) and not ('cop' in tree.children):
			main_token = tree.token
			modifier_tokens = []

			for rel in ('amod', 'nmod'):
				if rel in tree.children:
					for child_dep in tree.children[rel]:
						# appel récursif pour gérer les modificateurs imbriqués
						mod_token = self._get_composite_words(child_dep)
						modifier_tokens.append(mod_token)

			return CompositeToken(main_token, modifier_tokens)

		else:
			# pas de modificateurs, on retourne juste le token simple
			return tree.token
	
	def create_relation(self, sujet: Dependency, pattern: Dependency, objet: Dependency, relation_type: str) -> Relation:
		
		sujet_token 	: CompositeToken | Token | BasicToken	= self._get_composite_words(sujet)
		objet_token 	: CompositeToken | Token | BasicToken	= self._get_composite_words(objet)
		pattern_token 	: CompositeToken | Token | BasicToken	= self._get_composite_words(pattern)

		rel = Relation(
			sujet=sujet_token.text,
			objet=objet_token.text,
			pattern=pattern_token.text,
			relation_type=relation_type,
			source = self.relation_source,
		)

		rel.set_start_and_end(
			sujet	= self._get_position(sujet_token),
			pattern	= self._get_position(pattern_token),
			objet	= self._get_position(objet_token)
		)

		return rel
		

	def _get_position(self, token: CompositeToken | Token) -> tuple[int,int]:
		if isinstance(token, CompositeToken):
			return (token.idx, token.end_idx)
		else:
			return (token.idx, token.idx + len(token.text))

	def _check_children_keys(self, keys: set, tree: Dependency) -> bool:
		if tree is None or not hasattr(tree, 'children'):
			return False
		return keys.issubset(tree.children.keys())

	def extract(self, tree: Dependency, known_relations : list[Relation]) -> list[Relation] | None:
		"""
		Extrait les relations de la phrase pour une relation donnée.
		"""
		raise NotImplementedError

