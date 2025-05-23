
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import unittest
from src.semantic_analysis.content_analyser import GenericExtractor, ContentAnalyzer, Relation
from src.utils.helper import load_nlp_model
from rich import print


class TestGeneriqueExtraction(unittest.TestCase):
	   
	def setUp(self):
		self.analyser = ContentAnalyzer(nlp_model= load_nlp_model(), extractors=[GenericExtractor()])

	def test_extraction(self):
		text = "L'abcès artificiel est une technique médicale."
		expected = [
			"abcès artificiel → r_isa → technique",
		]
		result = list(map(str,self.analyser.analyse_content(text, True)))
		self.assertEqual(result, expected)

	def test_extraction_avec_pronon(self):
		text = "L'abdominoplastie est l'une des techniques utilisées dans la chirurgie esthétique abdominale."
		expected = [
			"abdominoplastie → r_isa → technique",
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
