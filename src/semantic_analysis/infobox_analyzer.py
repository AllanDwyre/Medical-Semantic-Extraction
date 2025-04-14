import re

class InfoboxAnalyzer:
	def __init__(self, nlp_model):
		self.nlp = nlp_model
	
	def _get_clean_value(self, dirty_value: str):
		"""Remplace les " et " par des virgules, puis split sur les virgules"""
		cleaned = re.split(r',|\s+et\s+', dirty_value)
		return [v.strip() for v in cleaned if v.strip()]

	def analyze_infobox(self, title, infobox):
		relations = []
		infobox_keywords = []
		if not isinstance(infobox, dict):
			return relations

		for key, value in infobox.items():
			if not (isinstance(value, str) and value):
				continue
			for clean_value in self._get_clean_value(value):
				relation = {
					'source': title,
					'relation_text': key,
					'target': clean_value,
					'confidence': 1.0,
					'source_type': 'infobox',
					'start_char' : None,
					'end_char' : None,
				}
				infobox_keywords.append(clean_value)
				relations.append(relation)
		return (relations, infobox_keywords)