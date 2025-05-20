from pathlib import Path
import sqlite3
from src.api.jdm_api import JdmApi, RelationType

def init_database(db_path: str, sql_file: str = "database/schema.sql"):
	db_file = Path(db_path)

	if db_file.exists():
		db_file.unlink()

	db_file.parent.mkdir(parents=True, exist_ok=True)

	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	with open(sql_file, 'r', encoding='utf-8') as f:
		sql_script = f.read()

	cursor.executescript(sql_script)

	conn.commit()
	conn.close()

def populate_relation_types(db_path: str):
	api = JdmApi()
	relation_types: list[RelationType] = api.fetch_relations_types().values()

	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	cursor.executemany(
		"""
		INSERT INTO relations_type (id, id_opposé, name, gp_name, help)
		VALUES (?, ?, ?, ?, ?)
		""",
		[
			(rel.id, rel.oppos, rel.name, rel.gpname, rel.help)
			for rel in relation_types
		]
	)

	conn.commit()
	conn.close()

def get_pages(db_conn:sqlite3.Connection) -> list[any]:
	return db_conn.execute('SELECT id, title FROM pages ORDER BY id').fetchall()
