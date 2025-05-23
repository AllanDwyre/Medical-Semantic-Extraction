
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import unittest
from src.semantic_analysis.content_analyser import ConsequenceExtractor, ContentAnalyzer, Relation
from src.utils.helper import load_nlp_model
from rich import print


class TestConsequenceExtraction(unittest.TestCase):
	   
	def setUp(self):
		self.analyser = ContentAnalyzer(nlp_model= load_nlp_model(), extractors=[ConsequenceExtractor()])

	def test_extraction(self):
		text = "En outre, des effets de la grossesse induisent des changements dans la colonne."
		expected = [
			"effet grossesse → r_has_conseq → changement colonne",
		]
		result = list(map(str,self.analyser.analyse_content(text, True)))
		self.assertEqual(result, expected)

	def test_no_match(self):
		text = "Ceci est une phrase sans relation sémantique claire."
		expected = []
		result = self.analyser.analyse_content(text, True)
		self.assertEqual(result, expected)

if __name__ == '__main__':
	unittest.main()
