from requests_cache import CachedSession
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class EndpointParams:
	types_ids: Optional[List[int]] = None
	not_types_ids: Optional[List[int]] = None
	min_weight: Optional[int] = None
	max_weight: Optional[int] = None
	relation_fields: Optional[List[str]] = None
	node_fields: Optional[List[str]] = None
	limit: Optional[int] = 0
	without_nodes: bool = False

	def to_query_params(self):
		def serialize(value):
			if isinstance(value, list):
				return ",".join(map(str, value))
			return value

		return {
			key: serialize(value)
			for key, value in asdict(self).items()
			if value is not None
		}

@dataclass
class RelationType:
	id: int
	name: str
	gpname: str
	help: str
	oppos: int
	posyes: str
	posno: str

class Jdm_api:
	def __init__(self, base_url="https://jdm-api.demo.lirmm.fr/v0"):
		self.base_url = base_url
		self.session = CachedSession('jdm_api_cache', expire_after=3600)

	def _getEndpoint(self, endpoint: str):
		return f"{self.base_url}/{endpoint}"

	def _fetch(self, endpoint: str, params=None):
		return self.session.get(self._getEndpoint(endpoint), params=params)

	def fetch_term_by_name(self, term):
		"""
		Récupère les informations d'un terme (mot) en le cherchant par son nom.
		"""
		response = self._fetch(f"node_by_name/{term}")
		if response.status_code == 200:
			return response.json()
		else:
			response.raise_for_status()

	def fetch_term_by_id(self, term_id):
		"""
		Récupère les informations d'un terme (mot) en le cherchant par son identifiant numérique.
		"""
		response = self._fetch(f"node_by_id/{term_id}")
		if response.status_code == 200:
			return response.json()
		else:
			response.raise_for_status()

	def fetch_relation_between(self, sujet, objet, params: Optional[EndpointParams] = None):
		"""
		Fetch relations between two specific terms (sujet -> objet).
		Accepts EndpointParams for filtering.
		"""
		endpoint = f"relations/from/{sujet}/to/{objet}"
		query_params = params.to_query_params() if params else {}

		response = self._fetch(endpoint, params=query_params)
		if response.status_code == 200:
			return response.json()
		else:
			response.raise_for_status()

	def fetch_relation(self, term, inverted=False, params: Optional[EndpointParams] = None):
		"""
		Récupère les relations d'un terme donné.
		Si `inverted` est False, récupère les relations sortantes (to),
		sinon récupère les relations entrantes (from).
		Prend en option des filtres via `EndpointParams`.
		"""
		endpoint = f"relations/to/{term}" if inverted else f"relations/from/{term}"
		query_params = params.to_query_params() if params else {}

		response = self._fetch(endpoint, params=query_params)
		if response.status_code == 200:
			return response.json()
		else:
			response.raise_for_status()

	def fetch_relations_types(self):
		"""
		Récupère la liste des types de relations disponibles dans l'API JDM.
		Retourne une liste d'objets `RelationType`.
		"""
		response = self._fetch("relations_types")
		if response.status_code == 200:
			raw_data = response.json()
			return [RelationType(
				id=item["id"],
				name=item["name"],
				gpname=item["gpname"],
				help=item["help"],
				oppos=item["oppos"],
				posyes=item["posyes"],
				posno=item["posno"]
			) for item in raw_data]
		else:
			response.raise_for_status()

