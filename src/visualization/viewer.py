from flask import Flask, render_template, request, jsonify
from src.utils.helper import open_localhost
from src.utils.database import get_pages
from collections import defaultdict
from src.semantic_analysis.document import ProcessedDocument, Relation
import sqlite3
import re

app = Flask(
	__name__,
)

# Configuration
DB_PATH = "database/medical_knowledge.db"
PROCESSED_DATA_PATH = "data/processed/_visualization_data.json"

def get_db_connection() -> sqlite3.Connection:
	"""Établir une connexion à la base de données SQLite."""
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn

@app.route('/')
def index():
	"""Page d'accueil avec la liste des articles."""
	conn = get_db_connection()
	pages = get_pages(conn)
	conn.close()
	return render_template('index.html', pages=pages)

@app.route('/page/<int:page_id>')
def page(page_id):
	"""Afficher une page avec ses mots-clés surlignés et ses relations."""
	conn = get_db_connection()
	
	try:
		document: ProcessedDocument = ProcessedDocument.from_database(conn, page_id)
		similar_pages = document.get_similar_pages(conn)
	except Exception as e:
			return str(e), 404
	
	conn.close()
	return render_template('page.html', 
							page= document.info,
							relation_infobox = document.relation_infobox,
							relation_content= document.relation_content,
							similar_pages=similar_pages)
@app.route('/search')
def search():
	"""Recherche de pages par mot-clé (dans le titre ou les mots-clés)."""
	query = request.args.get('q', '').strip()
	if not query:
		return jsonify([])

	conn = get_db_connection()

	results = conn.execute('''
		SELECT DISTINCT p.id, p.title, k1.keyword AS sujet, k2.keyword AS object
		FROM pages p
		INNER JOIN page_relations pr ON pr.page_id = p.id
		INNER JOIN relations r ON pr.relation_id = r.id
		INNER JOIN keywords k1 ON k1.id = r.source_id
		INNER JOIN keywords k2 ON k2.id = r.target_id
		WHERE k1.keyword LIKE ?
		OR k2.keyword LIKE ?
		ORDER BY p.title
		LIMIT 15
	''', (f'%{query}%', f'%{query}%')).fetchall()

	conn.close()

	filtered_result = [row for row in results if row['sujet'] or row['object']]

	return jsonify([
		{"id": row["id"], "title": row["title"], "keyword": f"{row['sujet'] or ''} / {row['object'] or ''}".strip(" /") }
		for row in filtered_result
	])

@app.template_filter('highlight_infobox')
def highlight_infobox(infobox : dict, relations : list[Relation]):
    
	# rejoindre chaque object (repartie a travers les relations) vers un seul pattern (key)
	pattern_to_objets = defaultdict(list)
	pattern_to_relation_types = defaultdict(set)  # Pour stocker les types de relations uniques

	for relation in relations:
		pattern_to_objets[relation.pattern].append(relation.objet)
		pattern_to_relation_types[relation.pattern].add(relation.relation_type)

	pattern_to_objets = dict(pattern_to_objets)
	pattern_to_relation_types = {k: list(v) for k, v in pattern_to_relation_types.items()}
    
	html = ""
	for key, value in infobox.items():
		if not value:
			html += f"<h3> {key} </h3>"
			continue

		html += "<li><strong>"
		if key in pattern_to_objets:
			tooltip_content = pattern_to_relation_types[key]
			html += (
				f'<span class="relation-tooltip">'
				f'<span class="relation-underline">{key} : </span>'
				f'<span class="tooltip">{tooltip_content}</span>'
				f'</span></strong>'
			)
			for objet in pattern_to_objets[key]:
				html += (
					f'<span class="highlight" data-selected="0">'
					f'{objet}'
					f'</span>'
				)
		else :
			html += key + " : </strong>"
			html += value +"</li>"

	return html

@app.template_filter('highlight_content')
def highlight_content(content : str, relations : list[Relation]):
	"""Insère des balises HTML autour des relations textuelles à des positions précises."""
	relations = sorted(relations, key=lambda r: r['start_char'], reverse=True)

	for rel in relations:
		start = rel['start_char']
		end = rel['end_char']
		relation_text = content[start:end]

		relation_type = f"[{rel['relation']}]"
		tooltip_html = (
			f"{rel['source']} {rel['relation_text']} {relation_type if(rel['relation']) else ''} {rel['target']}"
		)

		html = (
			f'<span class="relation-tooltip">'
			f'<span class="relation-underline">{relation_text}</span>'
			f'<span class="tooltip">{tooltip_html}</span>'
			f'</span>'
		)

		# Remplacer dans le texte à la bonne position
		content = content[:start] + html + content[end:]

	return content


@app.template_filter('highlight_brackets')
def highlight_brackets(text):
    return re.sub(r'\[(.*?)\]', r'<b>\1</b>', text)


def launch_localhost(debug=False):
	app.run(debug=debug)

if __name__ == '__main__':
	launch_localhost(True)
	open_localhost()
	