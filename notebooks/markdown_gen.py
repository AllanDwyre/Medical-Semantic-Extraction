import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.jdm_api import Jdm_api, RelationType

api = Jdm_api()
l:list[RelationType] = api.fetch_relations_types()

print("# Cheat sheet des relations de JDM :")
for item in l:
	if "interne" in item.help:
		continue

	opposers = list(filter(lambda x: item.oppos == x.id , l))

	definition, _, example = item.help.partition('Par exemple,')

	print(f"* **{item.name}** ({item.gpname}) ^{item.id}^:")
	print(f"\t➤ Définition :\t*{definition}*")
	if example:
		print(f"\t➤ Example :\t*{example.strip()}*")
	if opposers:
		opposer: RelationType = opposers[0]
		print(f"\t➤ Inverse :\t*{opposer.name}*")
	print()