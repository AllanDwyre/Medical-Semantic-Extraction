
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import unittest
from src.semantic_analysis.content_analyser import SynonymeExtractor, ContentAnalyzer
from src.utils.helper import load_nlp_model
from rich import print


def get_result(text, analyse_callback):
		return list(map(str, analyse_callback(text)))

class TestSynonymeExtraction(unittest.TestCase):
	   
	def setUp(self):
		self.analyser = ContentAnalyzer(nlp_model= load_nlp_model(), extractors=[SynonymeExtractor()])

	def test_synonym_extraction(self):
		text = "L'abcès artificiel peut aussi être désigné par « abcès de Fochier » ou encore « abcès de fixation »."
		expected = [
			"abcès artificiel → r_syn → abcès Fochier",
			"abcès fixation → r_syn → abcès Fochier"
		]
		result = get_result(text, self.analyser.analyse_content)
		self.assertEqual(result, expected)

	def test_no_match_det(self):
		"""les determinants ne peuvent etre des syn"""

		text = "L'allergie au lait est une réaction immunitaire défavorable à une ou plusieurs protéines dans le lait de vache."
		expected = []
		result = get_result(text, self.analyser.analyse_content)
		self.assertEqual(result, expected)


	def test_no_match_choix(self):
		"""Exprime un choix et non une similarité des mots"""

		text = "Le dernier peut prendre des heures ou des jours à apparaître."\
		"L'agénésie est l'absence de formation d'un organe ou d'un membre lors de l'embryogenèse."


		expected = []
		result = get_result(text, self.analyser.analyse_content)
		self.assertEqual(result, expected)
			
	def test_no_match(self):
		text = "Ceci est une phrase sans relation sémantique claire."
		expected = []
		result = get_result(text, self.analyser.analyse_content)
		self.assertEqual(result, expected)

if __name__ == '__main__':
	unittest.main()
