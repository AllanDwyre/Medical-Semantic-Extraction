
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import unittest
from src.semantic_analysis.content_analyser import SynonymeExtractor, ContentAnalyzer, Relation
from src.utils.helper import load_nlp_model
from rich import print


class TestSynonymeExtraction(unittest.TestCase):
	   
	def setUp(self):
		self.analyser = ContentAnalyzer(nlp_model= load_nlp_model(), extractors=[SynonymeExtractor()])

	def test_synonym_extraction(self):
		text = "L'abcès artificiel peut aussi être désigné par « abcès de Fochier » ou encore « abcès de fixation »."
		expected = [Relation(
					pattern='ou',
					relation_type='r_syn',
					sujet='abcès fixation',
					objet='abcès Fochier',
					start='80;68;49',
					end='97;70;65',
					source='content',
					id=-1
				)
			]
		result = self.analyser.analyse_content(text, True)
		self.assertEqual(result, expected)

	def test_no_match(self):
		text = "Ceci est une phrase sans relation sémantique claire."
		expected = []
		result = self.analyser.analyse_content(text, True)
		self.assertEqual(result, expected)

if __name__ == '__main__':
	unittest.main()
