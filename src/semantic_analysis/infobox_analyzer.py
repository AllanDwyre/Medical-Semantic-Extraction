import re
import spacy
from src.semantic_analysis.document import Relation

class InfoboxRelationDetector:
	def __init__(self):
		self.relations = [
			self._is_symptom,
			self._is_cause,
			self._is_transmission,
			self._is_medication,
			self._is_domain
		]
	
	def detect(self, key: str) -> str | None:
		for rel_check in self.relations:
			result = rel_check(key)
			if result:
				return result
		return None

	def _is_symptom(self, key: str) -> str | None:
		norm_key = self._normalize(key)
		if norm_key in {"symptome", "symptômes", "symptom"}:
			return "r_has_symptomes"
		return None

	def _is_cause(self, key: str) -> str | None:
		if "cause" in key.lower():
			return "r_has_causatif"
		return None

	def _is_transmission(self, key: str) -> str | None:
		if "transmission" in key.lower():
			return "r_processus>agent"
		return None

	def _is_medication(self, key: str) -> str | None:
		if "médicament" in key.lower() or "traitement" in key.lower():
			return "r_against"
		return None

	def _is_domain(self, key: str) -> str | None:
		if {"spécialité", "domaine"} in key.lower():
			return "r_domain"
		return None

	def _normalize(self, key: str) -> str:
		# Ta logique de normalisation ici, tu peux même appeler celle de l’InfoboxAnalyzer
		return key.strip().lower()


class InfoboxAnalyzer:
	def __init__(self, nlp_model: spacy.Language):
		self.nlp = nlp_model
		self.relation_detector = InfoboxRelationDetector()
	
	def _get_clean_value(self, dirty_value: str) -> list[str]:
		"""Remplace les 'et' par des virgules, puis split sur les virgules"""
		# trouve les liste et les transformes
		cleaned = re.split(r',|\s+et\s+', dirty_value)
		return [v.strip() for v in cleaned if v.strip()]
	
	def _normalize_key(self, key: str):
		"""Normalise et lemmatise la clé de la relation"""
		key = key.lower()
		key = re.sub(r'[^a-zàâçéèêëîïôûùüÿñæœ0-9\s_]', '', key)  # garde les accents si besoin
		doc = self.nlp(key)
		lemmatized = "_".join([token.lemma_ for token in doc if not token.is_punct])
		return re.sub(r'_+', '_', lemmatized).strip('_')

	def analyze_infobox(self, title, infobox) -> list[Relation]:
		if not isinstance(infobox, dict):
			return []
		
		relations: list[Relation] = []
		value :str
		for key, value in infobox.items():
			if len(value) == 0:
				continue
			rel_type = self.relation_detector.detect(key)
			if not rel_type:
				continue
			values = self._get_clean_value(value)
			for objet in values:
				relations.append(Relation(
					pattern			= key,
					relation_type	= rel_type,
					sujet			= title,
					objet			= objet,
					source			= "infobox"
				))

		return relations
			
