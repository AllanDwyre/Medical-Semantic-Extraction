from __future__ import annotations
from dataclasses import dataclass, field 
from spacy.tokens.token import Token
from typing import Any, Callable, Dict, List, Optional, Set
from src.utils.console import print_color

@dataclass
class Dependency:
	token		: Token					= None
	head		: Dependency			= None
	children	: dict[str, list[Dependency]] = field(default_factory=dict)

	def afficher_arbre(self: Dependency, niveau=0):
		indent = "  " * niveau  # Indentation selon le niveau de profondeur
		token_str = str(self.token) if self.token is not None else "None"
		print(f"{indent}{token_str}")

		for label, enfants in self.children.items():
			for enfant in enfants:
				print(f"{indent}  {label}:")
				self.afficher_arbre(enfant, niveau + 2)

	def __str__(self):
		return self.afficher_arbre()
	
	def has_tags(self, *labels):
		"""retourne vrai si il a tout les labels (xcomp, ...)"""
		return all(label in self.children for label in labels)
	
	def get_children(self, label):
			"""retourne tout les dependance qui on ce label"""
			return self.children[label] if label in self.children else None
	
	def get_child(self, label, index = 0):
		"""retourne la dependance à l'index qui on ce label"""
		return self.children[label][index] if label in self.children else None


class PatternMatchException(Exception):
	def __init__(self, message):
		super().__init__(message)


	def __str__(self):
		return (
			f"[PatternMatchException] {self.args[0]}\n"
	
		)
	

@dataclass
class PatternCondition:
	"""Représente une condition sur un nœud de l'arbre syntaxique"""
	validator: Callable[[Any], List[Dependency]]
	required: bool = True
	description: str = ""



class PatternBuilder:
	def __init__(self):
		self.conditions: List[PatternCondition] = []
		self._start_from = None

	def child_has_tag(self, *tag_levels: Set[str]):
		"""
		Ex: has_tag({"xcomp"}, {"cc"}) = chercher un chemin enfant xcomp → cc
		Ex: has_tag({"xcomp", "cc"}) = chercher un enfant avec tag xcomp OU cc
		"""
		def validator(nodes: List[Dependency]) -> List[Dependency]:
			def match_level(nodes: List[Dependency], level: int) -> List[Dependency]:
				if level >= len(tag_levels):
					return nodes

				next_tags = tag_levels[level]
				next_nodes = []
				for node in nodes:
					for tag in next_tags:
						if (c := node.get_child(tag)):
							next_nodes.append(c)

				if not next_nodes:
					return []

				return match_level(next_nodes, level + 1)
			return match_level(nodes, 0)

		description = " -> ".join(f"[{','.join(t)}]" for t in tag_levels)
		self.conditions.append(PatternCondition(validator, description=f"has_tag path {description}"))
		return self
	
	def check_pos(self, possible_pos: Set[str]):
		def validator(nodes: List[Dependency]) -> List[Dependency]:
			return [node for node in nodes if node.token.pos_ in possible_pos]
			
		self.conditions.append(PatternCondition(validator, description=f"has no childrens with this pos {possible_pos}"))
		return self
	
	def check_lemma(self, possible_lemma: Set[str]):
		def validator(nodes: List[Dependency]) -> List[Dependency]:
			return [node for node in nodes if node.token.lemma_ in possible_lemma]
			
		self.conditions.append(PatternCondition(validator, description=f"has no childrens with this lemma {possible_lemma}"))
		return self
	
	def start_from(self, starter_point : str):
		if len(self.conditions) > 0 :
			raise Exception("start_from need to be the first condition")
		
		if starter_point not in {"pattern", "sujet", "objet"}:
			raise Exception("start_from need to be on of theses : pattern, sujet, objet")
		
		self._start_from = starter_point
		def _noop(nodes): return nodes
			
		self.conditions.append(PatternCondition(_noop, description=starter_point))
		return self
	

	def add__custom(self):
		return self
	

	def build(self) -> Pattern:
		return Pattern(self.conditions, self._start_from)

class Pattern:
	def __init__(self, conditions: List[PatternCondition], start_from: Optional[str] = None):
		self.conditions = conditions
		self.start_from = start_from

	def find(self, node: Dependency):
		nodes = [node]
		for cond in self.conditions:
			nodes = cond.validator(nodes)
			if not nodes:
				raise PatternMatchException(message=cond.description)
		if nodes:
			return nodes[0]
		return None

@dataclass
class PatternMatch:
	sujet: Pattern
	pattern: Pattern
	objet: Pattern

	def match(self, tree: Dependency, verbose=False) -> tuple[Dependency, Dependency, Dependency]:
		node = {"sujet": None, "pattern": None, "objet": None}
		patterns = {
			"sujet": self.sujet,
			"pattern": self.pattern,
			"objet": self.objet
		}

		dependencies = {key: [] for key in patterns}
		for key, pattern in patterns.items():
			if pattern.start_from:
				dependencies[key].append(pattern.start_from)

		order = self._topological_sort(dependencies)

		try:
			for key in order:
				pattern = patterns[key]
				if pattern.start_from:
					start_node = node[pattern.start_from]
					if not start_node:
						raise PatternMatchException(f"Missing start node for {key}")
					node[key] = pattern.find(start_node)
				else:
					node[key] = pattern.find(tree)
				if not node[key]:
					break # early break car pas de relation
			return node["sujet"], node["pattern"], node["objet"]

		except PatternMatchException as e:
			if verbose:
				print_color(f"[DEBUG] Erreur lors du match : {e}", "debug")
			return None, None, None

		except Exception as e:
			raise e


	def _topological_sort(self, dependencies: dict) -> list:
		visited = set()
		order = []

		def visit(node):
			if node in visited:
				return
			visited.add(node)
			for dep in dependencies[node]:
				visit(dep)
			order.append(node)

		for node in dependencies:
			visit(node)

		return order

		

@dataclass
class BasicToken:
	text	: str
	idx		: int
	
	def __len__(self):
		return len(self.text)

@dataclass
class CompositeToken:
	main_token		: Token
	modifier_tokens	: List[Token]

	_composite_word : str			= ""
	
	def _compute_text(self):
		"""Calcule le texte complet du token composé"""
		tokens = [self.main_token] + self.modifier_tokens
		tokens.sort(key=lambda t: t.idx)
		
		return " ".join([t.text for t in tokens])
	
	@property
	def idx(self):
		return self.main_token.idx
	
	@property
	def end_idx(self):
		"""Position de fin = fin du dernier token (chronologiquement)"""
		all_tokens = [self.main_token] + self.modifier_tokens
		last_token = max(all_tokens, key=lambda t: t.idx)
		return last_token.idx + len(last_token.text)

	
	@property
	def text(self):
		if(len(self._composite_word) > 0):
			return self._composite_word
		
		self._composite_word =  self._compute_text()
		return self._composite_word
	
	@property
	def lemma_(self):
		"""Renvoie le lemme composé"""
		return " ".join([self.main_token.lemma_] + [t.lemma_ for t in self.modifier_tokens])
	
	@property
	def pos_(self):
		"""Renvoie la partie du discours du token principal"""
		return self.main_token.pos_
	
	@property
	def tag_(self):
		"""Renvoie le tag du token principal"""
		return self.main_token.tag_
	
	def __len__(self):
		return len(self.text)
	def __str__(self):
		return self.text

