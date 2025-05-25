
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


import unittest
from src.semantic_analysis.content_analyser import ContentAnalyzer
from src.utils.helper import load_nlp_model
from rich import print

class TestContentAnalyzer(unittest.TestCase):
	   
	def setUp(self):
		self.analyser = ContentAnalyzer(nlp_model= load_nlp_model(), extractors=[])

	def test_normalize_hyphenated_names(self):
		text = "L’acrodermatite papuleuse infantile ou syndrome de Gianotti-Crosti est une maladie bénigne."
		expected = "L’acrodermatite papuleuse infantile ou syndrome de Gianotti_Crosti est une maladie bénigne."
		result = self.analyser.normalize_hyphenated_names(text)
		self.assertCountEqual(result, expected)

	def test_normalize_hyphenated_no_match(self):
		text = "- Ceci est une liste donc pas de normalisation."
		expected = "- Ceci est une liste donc pas de normalisation."
		result = self.analyser.normalize_hyphenated_names(text)
		self.assertCountEqual(result, expected)


if __name__ == '__main__':
	unittest.main()
