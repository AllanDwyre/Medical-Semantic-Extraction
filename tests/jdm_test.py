import unittest
from unittest.mock import patch, MagicMock
from src.api.jdm_api import Jdm_api, EndpointParams, RelationType


class TestJdmApi(unittest.TestCase):

	def setUp(self):
		self.api = Jdm_api()

	@patch('src.api.jdm_api.CachedSession.get')
	def test_fetch_term_by_name_success(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {"id": 1, "name": "chat"}
		mock_get.return_value = mock_response

		result = self.api.fetch_term_by_name("chat")
		self.assertEqual(result["name"], "chat")

	@patch('src.api.jdm_api.CachedSession.get')
	def test_fetch_term_by_id_success(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {"id": 123, "name": "chien"}
		mock_get.return_value = mock_response

		result = self.api.fetch_term_by_id(123)
		self.assertEqual(result["id"], 123)

	@patch('src.api.jdm_api.CachedSession.get')
	def test_fetch_relation_with_params(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {"result": "ok"}
		mock_get.return_value = mock_response

		params = EndpointParams(min_weight=10, max_weight=100)
		result = self.api.fetch_relation(1, 2,params=params)

		self.assertEqual(result["result"], "ok")
		mock_get.assert_called()
		called_url = mock_get.call_args[1]['params']
		self.assertEqual(called_url["min_weight"], 10)
		self.assertEqual(called_url["max_weight"], 100)

	@patch('src.api.jdm_api.CachedSession.get')
	def test_fetch_relations_types_parsing(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = [
			{
				"id": 19,
				"name": "r_lemma",
				"gpname": "r_lemma",
				"help": "Lemme info",
				"oppos": -1,
				"posyes": "",
				"posno": ""
			}
		]
		mock_get.return_value = mock_response

		result = self.api.fetch_relations_types()
		self.assertEqual(len(result), 1)
		self.assertIsInstance(result[0], RelationType)
		self.assertEqual(result[0].name, "r_lemma")


if __name__ == '__main__':
	unittest.main()
