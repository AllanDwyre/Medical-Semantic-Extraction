from __future__ import annotations
import json
import sqlite3
from sqlite3 import Cursor, Connection
from dataclasses import dataclass, field 


@dataclass
class DocumentInfo :
	title:		str
	url:		str
	infobox:	dict	= field(default_factory=dict)
	content:	str		= ""
	page_id: 	int		= -1

	@staticmethod
	def from_json_file(json_file_path) -> "DocumentInfo":
		with open(json_file_path, 'r', encoding='utf-8') as f:
			data: dict = json.load(f)

		return DocumentInfo(
			title=data.get('titre', 'Sans titre'),
			content=data.get('contenu', ''),
			infobox=data.get('infobox', {}),
			url=data.get('url', '')
		)

@dataclass
class Relation:
	pattern:		str
	relation_type:	str
	sujet:			str
	objet:			str
	start:			str = '' # only content source
	end:			str = '' # only content source
	source:			str = '' # infobox ou content
	id:				int = -1

	# TODO : confidence score + normalized pattern ? 
	
	def set_start_and_end(self, sujet : tuple[int,int], pattern: tuple[int,int], objet: tuple[int,int]) -> None:
		self.start += f"{sujet[0]};{pattern[0]};{objet[0]}"
		self.end   += f"{sujet[1]};{pattern[1]};{objet[1]}"
		
	def get_start_end(self, attribute:str) -> tuple[int,int]: 
		"""Get the start & end of a attribute : (sujet, objet or pattern)"""
		st_suj, st_rel, st_obj = tuple(map(int, self.start.split(';')))
		end_suj, end_rel, end_obj = tuple(map(int, self.end.split(';')))
		match attribute:
			case "sujet":
				return (st_suj, end_suj)
			case "pattern":
				return (st_rel, end_rel)
			case "objet":
				return (st_obj, end_obj)
			
@dataclass
class ProcessedDocument:
	info:				DocumentInfo
	relation_content:	list[Relation]	= field(default_factory=list)
	relation_infobox:	list[Relation]	= field(default_factory=list)

	def save_to_database(self, db_path: str) -> None:
		conn = sqlite3.connect(db_path)
		cursor: Cursor = conn.cursor()

		def get_or_create_keyword(term: str) -> int:
			cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (term,))
			res = cursor.fetchone()
			if res:
				cursor.execute("UPDATE keywords SET frequency = frequency + 1 WHERE id = ?", (res[0],))
				return res[0]
			cursor.execute("INSERT INTO keywords (keyword) VALUES (?)", (term,))
			return cursor.lastrowid

		def get_or_create_pattern(text: str) -> int:
			cursor.execute("SELECT id FROM patterns WHERE pattern = ?", (text,))
			res = cursor.fetchone()
			if res:
				return res[0]
			cursor.execute("INSERT INTO patterns (pattern) VALUES (?)", (text,))
			return cursor.lastrowid

		def get_relation_type_id(name: str) -> int:
			cursor.execute("SELECT id FROM relations_type WHERE name = ?", (name,))
			res = cursor.fetchone()
			if res:
				return res[0]
			raise ValueError(f"[ERREUR] Type de relation inconnu : {name}")

		# Ajouter la page
		cursor.execute(
			"""
			INSERT INTO pages (title, content, infobox, url)
			VALUES (?, ?, ?, ?)
			""",
			(self.info.title, self.info.content, json.dumps(self.info.infobox), self.info.url)
		)
		page_id = cursor.lastrowid

		# Gerer les relations infobox pour la page
		for rel in self.relation_infobox:
			try:
				source_id = get_or_create_keyword(rel.sujet)
				target_id = get_or_create_keyword(rel.objet)
				pattern_id = get_or_create_pattern(rel.pattern)
				relation_type_id = get_relation_type_id(rel.relation_type)

				# Ajouter la relation
				cursor.execute(
					"""
					INSERT INTO relations (source_id, target_id, pattern_id, predicted_relation_type, confidence_score, source)
					VALUES (?, ?, ?, ?, ?, ?)
					""",
					(source_id, target_id, pattern_id, relation_type_id, None, rel.source)
				)
				relation_id = cursor.lastrowid

				# Lier la relation à la page
				cursor.execute(
					"""
					INSERT INTO page_relations (page_id, relation_id)
					VALUES (?, ?)
					""",
					(page_id, relation_id)
				)

			except Exception as e:
				print(f"[ERREUR DB : infobox] {e} – relation: {rel}")

		# Gerer les relations infobox pour la page
		for rel in self.relation_content:
			try:
				source_id = get_or_create_keyword(rel.sujet)
				target_id = get_or_create_keyword(rel.objet)
				pattern_id = get_or_create_pattern(rel.pattern)
				relation_type_id = get_relation_type_id(rel.relation_type)

				# Ajouter la relation
				cursor.execute(
					"""
					INSERT INTO relations (source_id, target_id, pattern_id, predicted_relation_type, confidence_score, source)
					VALUES (?, ?, ?, ?, ?, ?)
					""",
					(source_id, target_id, pattern_id, relation_type_id, None, rel.source)
				)
				relation_id = cursor.lastrowid

				# Lier la relation à la page
				cursor.execute(
					"""
					INSERT INTO page_relations (page_id, relation_id, start_rel, end_rel)
					VALUES (?, ?, ?, ?)
					""",
					(page_id, relation_id, rel.start, rel.end)
				)

			except Exception as e:
				print(f"[ERREUR DB : content] {e} – relation: {rel}")
		conn.commit()
		conn.close()

		# [x] enregistrer la table dans la DB
		# [x] Loop les relations infobox avec relation source = 'infobox'
		#		[x] enregistrer les keywords si il n'existent pas
		#		[x] recupérer leur ids (gerer dans le cas qu'il existe déja)
		#		[x] recupérer leur insérer leur relations sans les start et end
		# [x] Loop les relations content avec relation source = 'content'
		#		[x] enregistrer les keywords si il n'existent pas
		#		[x] recupérer leur ids (gerer dans le cas qu'il existe déja)
		#		[x] recupérer leur insérer leur relations
		
		# [ ] Ajouter les confidence score pour tout type de relation
	
	@staticmethod
	def from_database(conn: Connection, page_id: int) -> "ProcessedDocument":
		cursor = conn.cursor()

		# 1. Récupérer les infos de la page
		row = cursor.execute(
			"SELECT title, content, infobox, url FROM pages WHERE id = ?", (page_id,)
		).fetchone()

		if not row:
			raise ValueError(f"[ERREUR] Aucune page avec l'id {page_id}")

		title, content, infobox_json, url = row
		info = DocumentInfo(
			title=title,
			content=content,
			infobox=json.loads(infobox_json),
			url=url,
			page_id= page_id
		)

		# 2. Récupérer les relations liées à cette page
		cursor.execute(
			"""
			SELECT k1.keyword, k2.keyword, rt.name, p.pattern, pr.start_rel, pr.end_rel, r.source, r.id
			FROM page_relations pr
			JOIN relations r ON pr.relation_id = r.id
			JOIN keywords k1 ON r.source_id = k1.id
			JOIN keywords k2 ON r.target_id = k2.id
			JOIN relations_type rt ON r.predicted_relation_type = rt.id
			JOIN patterns p ON r.pattern_id = p.id
			WHERE pr.page_id = ?
			""",
			(page_id,)
		)

		relations = []
		for k1, k2, rel_type, pattern, start, end, source, id in cursor.fetchall():
			relations.append(Relation(
				sujet=k1,
				objet=k2,
				relation_type=rel_type,
				pattern=pattern,
				start=start,
				end=end,
				source=source,
				id=id,
			))

		# 3. Séparer infobox / content (selon start/end vides ou non)
		relation_infobox = [r for r in relations if r.source == "infobox"]
		relation_content = [r for r in relations if r.source == "content"]

		return ProcessedDocument(info, relation_infobox=relation_infobox, relation_content=relation_content)
	
	def get_similar_pages(self, conn: Connection) -> list:
		similar_pages = conn.execute('''
			WITH current_keywords AS (
				SELECT k.id
				FROM page_relations pr
				JOIN relations r ON pr.relation_id = r.id
				JOIN keywords k ON k.id IN (r.source_id, r.target_id)
				WHERE pr.page_id = ?
			)
			SELECT p.id, p.title, COUNT(*) as common_keywords
			FROM pages p
			JOIN page_relations pr2 ON p.id = pr2.page_id
			JOIN relations r2 ON pr2.relation_id = r2.id
			JOIN keywords k2 ON k2.id IN (r2.source_id, r2.target_id)
			WHERE k2.id IN (SELECT id FROM current_keywords)
			AND p.id != ?
			GROUP BY p.id
			ORDER BY common_keywords DESC
			LIMIT 5
		''', (self.info.page_id, self.info.page_id)).fetchall()

		return similar_pages
