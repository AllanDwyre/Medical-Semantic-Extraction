from src.semantic_analysis.document import Relation
from src.semantic_analysis.pattern_matching import CompositeToken, BasicToken, Dependency, Token, PatternMatch, PatternCondition, PatternBuilder

class BaseRelationExtractor:
	relation_name = "undefined"
	relation_source = "content"
	rules : list[PatternMatch] = []

	
	def get_pattern(self, tree: Dependency):
		if isinstance(tree, BasicToken):
			return tree
		return tree.token
		

	def get_composite_words(self, tree: Dependency, isNmodOnly = None) -> CompositeToken | Token | BasicToken:
		"""Extrait les mots composés formés par un nom et ses modificateurs adjectivaux ou nominaux.
		"""
		if isinstance(tree, BasicToken):
			return [tree]
		
		# pas de modificateurs, on retourne juste le token simple
		if ('nmod' not in tree.children and 'amod' not in tree.children):	
			return [tree.token] if isNmodOnly is None else tree.token
		
		# Si nmmodOnly est none alors on est la racine de la récursion
		if isNmodOnly is None:
			nmod_composite = self.get_composite_words(tree, isNmodOnly = True)
			enriched_composite = self.get_composite_words(tree, isNmodOnly = False)

			return [nmod_composite, enriched_composite]


		# Sinon on est dans une récursion
		main_token = tree.token
		modifiers_tokens = []

		for rel, children in tree.children.items():
			if rel == 'nmod':
				for child in children:
					modifiers_tokens.append(self.get_composite_words(child, isNmodOnly = isNmodOnly))
					
			elif rel == 'amod'and not isNmodOnly:
				for child in children:
					modifiers_tokens.append(self.get_composite_words(child, isNmodOnly = isNmodOnly))

		return CompositeToken(main_token, modifiers_tokens)
			
		
	def _get_tiret_union_back(self, text:str):
		return text.replace('_', '-')
		
	def create_relation(self, sujet_dep: Dependency, pattern_dep: Dependency, objet_dep: Dependency, relation_type: str, relations: list[Relation] = []) -> Relation:
		if not sujet_dep or not pattern_dep or not objet:
			return None

		sujet_tokens	: list[CompositeToken | Token | BasicToken]	= self.get_composite_words(sujet)
		objet_tokens 	: list[CompositeToken | Token | BasicToken]	= self.get_composite_words(objet)
		pattern_token 	: Token | BasicToken	= pattern_dep.token
		
		for sujet in sujet_tokens:
			for objet in objet_tokens:
				rel = Relation(
					sujet= self._get_tiret_union_back(sujet.lemma_),
					objet= self._get_tiret_union_back(objet.lemma_),
					pattern= self._get_tiret_union_back(pattern_token.lemma_),
					relation_type=relation_type,
					source = self.relation_source,
				)

				rel.set_start_and_end(
					sujet	= self._get_position(sujet),
					pattern	= self._get_position(pattern_token),
					objet	= self._get_position(objet)
				)

				relations.append(rel)
		return relations

	def _get_position(self, token: CompositeToken | Token) -> tuple[int,int]:
		if isinstance(token, (CompositeToken, BasicToken)):
			return (token.idx, token.end_idx)
		else:
			return (token.idx, token.idx + len(token.text))

	def _check_children_keys(self, keys: set, tree: Dependency) -> bool:
		if tree is None or not hasattr(tree, 'children'):
			return False
		return keys.issubset(tree.children.keys())

	def extract(self, tree: Dependency, known_relations : list[Relation], verbose=False) -> list[Relation] | None:
		"""
		Extrait les relations de la phrase pour une relation donnée.
		"""
		relations = []
		for i,rule in enumerate(self.rules):
			rule.match_name = rule.match_name or f"rule-{i}"
			sujet, pattern, objet = rule.match(tree, verbose)
			self.create_relation(sujet, pattern, objet, self.relation_name, relations)
		return relations

