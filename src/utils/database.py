import sqlite3
import json
from pathlib import Path

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

def save_to_database(db_path: str, analyzed_documents: list[dict]) -> None:
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	for doc in analyzed_documents:
		title = doc['title']
		content = doc['content']
		url = doc['url']
		infobox = doc['infobox']
		keywords = doc['keywords']
		relations = doc['relations_text'] + doc['relations_infobox']

		json_infobox = json.dumps(infobox, ensure_ascii=False)

		# Insert page
		cursor.execute("INSERT INTO pages (title, content, url, infobox) VALUES (?, ?, ?, ?)",
					   (title, content, url, json_infobox))
		page_id = cursor.lastrowid

		keyword_ids = {}

		# Insert keywords and page-keywords
		for kw in keywords:
			keyword = kw['keyword']
			score = kw['score']
			
			cursor.execute("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", (keyword,))
			cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
			keyword_id = cursor.fetchone()[0]
			keyword_ids[keyword.lower()] = keyword_id

			cursor.execute("INSERT INTO page_keywords (page_id, keyword_id, importance_score) VALUES (?, ?, ?)",
						   (page_id, keyword_id, score))
		
		# Insert relations (if both ends exist in keywords)
		for rel in relations:
			source = rel['source'].lower()
			target = rel['target'].lower()
			rel_text = rel['relation_text'].lower()
			conf = rel.get('confidence', 1.0)
			src_type = rel.get('source_type', 'texte')
			start_char = rel.get('start_char')
			end_char = rel.get('end_char')

			source_id = keyword_ids.get(source)
			target_id = keyword_ids.get(target)

			if source_id and target_id:
				cursor.execute('''
					INSERT INTO relations (
						source_id, target_id, relation_text, confidence_score,
						source_type, start_char, end_char
					) VALUES (?, ?, ?, ?, ?, ?, ?)''',
					(source_id, target_id, rel_text, conf, src_type, start_char, end_char)
				)

				
				relation_id = cursor.lastrowid

				cursor.execute('''
					INSERT INTO page_relations (page_id, relation_id)
					VALUES (?, ?)''',
					(page_id, relation_id))

	conn.commit()
	conn.close()

def get_pages(db_conn:sqlite3.Connection) -> list[any]:
	return db_conn.execute('SELECT id, title FROM pages ORDER BY title').fetchall()

def get_page_by_id(db_conn:sqlite3.Connection, id:int) -> list[any]:
	return db_conn.execute('SELECT id, title, content, infobox, url FROM pages WHERE id = ?', (id,)).fetchone()

def get_page_data(db_conn:sqlite3.Connection, page_id:int) -> list[any]:
	# Récupérer les mots-clés liés à cette page
	keywords = db_conn.execute('''
		SELECT k.keyword, pk.importance_score 
		FROM page_keywords pk
		JOIN keywords k ON pk.keyword_id = k.id
		WHERE pk.page_id = ?
		ORDER BY pk.importance_score DESC
	''', (page_id,)).fetchall()
	
	# Récupérer les relations pour cette page
	relations = db_conn.execute('''
		SELECT
			k1.keyword AS source,
			k2.keyword AS target,
			rt.name AS relation,
			r.relation_text,
			r.confidence_score,
			r.source_type
		FROM page_relations pr
		JOIN relations r ON pr.relation_id = r.id
		JOIN keywords k1 ON r.source_id = k1.id
		JOIN keywords k2 ON r.target_id = k2.id
		LEFT JOIN relations_type rt ON r.relation_id = rt.id
		WHERE pr.page_id = ?
	''', (page_id,)).fetchall()

	
	# Récupérer les pages similaires (qui partagent des mots-clés)
	similar_pages = db_conn.execute('''
		SELECT p.id, p.title, COUNT(*) as common_keywords
		FROM pages p
		JOIN page_keywords pk1 ON p.id = pk1.page_id
		JOIN page_keywords pk2 ON pk1.keyword_id = pk2.keyword_id
		WHERE pk2.page_id = ? AND p.id != ?
		GROUP BY p.id
		ORDER BY common_keywords DESC
		LIMIT 5
	''', (page_id, page_id)).fetchall()

	total_pages = db_conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
	
	return (keywords, relations, similar_pages, total_pages)