
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import unittest
from src.semantic_analysis.content_analyser import CauseExtractor, ContentAnalyzer, Relation
from src.utils.helper import load_nlp_model
from rich import print

class TestCauseExtraction(unittest.TestCase):
	   
	def setUp(self):
		self.analyser = ContentAnalyzer(nlp_model= load_nlp_model(), extractors=[CauseExtractor()])

	def test_extraction(self):
		text = "L'adénolymphite mésentérique est plus généralement due à une infection virale."
		expected = [
			"adénolymphite mésentérique → r_has_causatif → infection viral",
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
