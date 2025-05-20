import re
from src.semantic_analysis.document import Relation, CompositeToken, BasicToken, Dependency, Token, Dict

from src.semantic_analysis.relations.base import BaseRelationExtractor
from src.semantic_analysis.relations.isa import GenericExtractor
from src.semantic_analysis.relations.syn import SynonymeExtractor
from src.semantic_analysis.relations.caract import CaracteristicExtractor
from src.semantic_analysis.relations.heritage import HeritageExtractor
from src.semantic_analysis.relations.role_telic import RoleTelicExtractor
from src.semantic_analysis.relations.against import AgainstExtractor



class ContentAnalyzer:
	def __init__(self, nlp_model):
		self.nlp = nlp_model
		self.rejected_pos = ("PUNCT", "DET")
		self.extractors: list[BaseRelationExtractor] = [GenericExtractor(), SynonymeExtractor(), CaracteristicExtractor(), HeritageExtractor(), RoleTelicExtractor(), AgainstExtractor() ]

	def _extract_marked_entities(text):
		return re.findall(r"\[([^\[\]]+)\]", text)
	
	def build_dependency_tree(self, sent) -> Dict[Token, Dependency]:
		"""Construit un arbre de dépendances pour une phrase."""
		token_to_dep = {}
		root = None
		
		# Première passe : créer les objets Dependency pour chaque token
		for token in sent:
			if token.pos_ in self.rejected_pos:
				continue
			
			if token not in token_to_dep:
				token_to_dep[token] = Dependency(token=token)
		
		# Deuxième passe : établir les relations head/children
		for token in sent:
			if token not in token_to_dep:
				continue

			dep_obj = token_to_dep[token]

			# Détecter le ROOT
			if token.dep_ == "ROOT":
				root = dep_obj

			# Établir la relation avec le head
			if token.head != token and token.head in token_to_dep:
				dep_obj.head = token_to_dep[token.head]

			# Établir les enfants
			for child in token.children:
				if child.pos_ in self.rejected_pos:
					continue
				if child in token_to_dep:
					child_dep = token_to_dep[child]
					dep_obj.children.setdefault(child.dep_, []).append(child_dep)
			
		return root
	
	def walk_tree(self, tree: Dependency, known_relations=None) -> list[Relation]:
		results = []
		known_relations = known_relations or []

		for extractor in self.extractors:
			rels = extractor.extract(tree, known_relations)
			if rels:
				results.extend(rels)
				known_relations.extend(rels)

		for children in tree.children.values():
			for child in children:
				results.extend(self.walk_tree(child, known_relations))

		return results
	
	def analyse_content(self, content: str, verbose = False) -> list[Relation]:
		doc = self.nlp(content)
		relations = []
		for sent in doc.sents:
			sent_root = self.build_dependency_tree(sent)
			sent_relations = self.walk_tree(sent_root)
			relations.extend(sent_relations)
			if verbose:
				print(f"[green bold]{sent}[/green bold]")
				print(sent_root)
				for relation in sent_relations:
					print(f"{relation.sujet} → {relation.relation_type} → {relation.objet}")
		return relations