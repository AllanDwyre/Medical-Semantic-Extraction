
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import unittest
from src.semantic_analysis.pattern_matching import CompositeToken
from src.semantic_analysis.content_analyser import BaseRelationExtractor, ContentAnalyzer, Dependency 
from src.utils.helper import load_nlp_model, get_result
from rich import print as rprint

def get_composite_result(words, composite_callback, return_index = 1):
	results = []
	for word in words:
		return_value = composite_callback(word)
		if not isinstance(return_value[0], CompositeToken): # On sait qu'il y a toujours une valeur de retour
			continue
		results.append(str(return_value[return_index]))
	return results

class TestBase(unittest.TestCase):
	  
	def setUp(self):
		self.extractor = BaseRelationExtractor()
		self.nlp = load_nlp_model()
		self.analyser = ContentAnalyzer(self.nlp)

	def test_composite(self):
		text = self.nlp("L'abcès artificiel est une technique médicale.")
		tree = self.analyser.build_dependency_tree(text)

		words = tree.search_in_tree(lambda dep : dep.token.text in ('abcès', 'technique') )
		result = get_composite_result(words, self.extractor.get_composite_words)

		expected = [
			"abcès artificiel",
			"technique médicale",
		]
		
		self.assertCountEqual(result, expected)

	def test_composite_avec_case(self):
		text = self.nlp("Ce terme est également utilisé dans le domaine de la sécurité informatique.")
		tree = self.analyser.build_dependency_tree(text)

		words = tree.search_in_tree(lambda dep : dep.token.text in ('terme', 'utilisé', 'domaine', 'sécurité') )
		result = get_composite_result(words, self.extractor.get_composite_words)

		expected = [
			"domaine sécurité informatique",
			"sécurité informatique", 
		]
		
		self.assertCountEqual(result, expected)

	def test_composite_avec_case1(self):
		text = self.nlp("L'anorexie mentale, ou anorexia nervosa, est un trouble des conduites alimentaires.")
		tree = self.analyser.build_dependency_tree(text)

		words = tree.search_in_tree(lambda dep : dep.token.text in ('anorexie', 'anorexia', 'trouble', 'conduites') )
		result = get_composite_result(words, self.extractor.get_composite_words)

		expected = [
			"anorexie mentale",
			"anorexia nervosa",
			"trouble conduites alimentaires",
			"conduites alimentaires",
		]
		
		self.assertCountEqual(result, expected)

	def test_composite_nmod_only(self):
		text = self.nlp("La Grippe, ou Influenza est une maladie infectieuse et contagieuse fréquente.")
		tree = self.analyser.build_dependency_tree(text)

		words = tree.search_in_tree(lambda dep : dep.token.text in ('maladie', 'contagieuse') )

		result = get_composite_result(words, self.extractor.get_composite_words, return_index=0)
		expected = ['maladie']
		
		self.assertCountEqual(result, expected)

	def test_creation_relations(self):
		text = "L'acrodermatite papuleuse infantile ou syndrome de Gianotti_Crosti est une maladie bénigne."
		tree = self.analyser.build_dependency_tree(self.nlp(text))


		sujet = tree.search_in_tree(lambda dep : dep.token.text == 'acrodermatite' )[0]
		objet = tree.search_in_tree(lambda dep : dep.token.text == 'syndrome' )[0]
		pattern = tree.search_in_tree(lambda dep : dep.token.text == 'ou' )[0]

		result = []
		self.extractor.create_relation(sujet, pattern, objet, "r_base_test", result)

		expected = [
			"acrodermatite papuleux infantile → r_base_test → syndrome Gianotti-Crosti",
			"acrodermatite → r_base_test → syndrome Gianotti-Crosti"
		]
		self.assertCountEqual( list(map(str, result)), expected)
		

if __name__ == '__main__':
	unittest.main()
