from flask import Flask, render_template, request, jsonify
from src.utils.helper import open_localhost
from src.utils.database import get_pages, get_page_by_id, get_page_data
import json
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
	
	# Récupérer la page
	page_data = get_page_by_id(conn, page_id)
	if not page_data:
		return "Page non trouvée", 404
	
	keywords, relations, similar_pages, total_pages = get_page_data(conn, page_id)
	conn.close()

	infobox = json.loads(page_data['infobox']) if page_data['infobox'] else {}

	return render_template('page.html', 
							page=page_data,
							infobox=infobox,
							keywords=keywords,
							relations=relations,
							similar_pages=similar_pages,
							total_pages=total_pages)
@app.route('/search')
def search():
	"""Recherche de pages par mot-clé."""
	query = request.args.get('q', '')
	if not query:
		return jsonify([])
	
	conn = get_db_connection()
	results = conn.execute('''
		SELECT p.id, p.title, k.keyword, pk.importance_score
		FROM pages p
		JOIN page_keywords pk ON p.id = pk.page_id
		JOIN keywords k ON pk.keyword_id = k.id
		WHERE k.keyword LIKE ? OR p.title LIKE ?
		ORDER BY pk.importance_score DESC
		LIMIT 20
	''', (f'%{query}%', f'%{query}%')).fetchall()
	
	conn.close()
	
	# Formater les résultats
	formatted_results = []
	for row in results:
		formatted_results.append({
			'id': row['id'],
			'title': row['title'],
			'keyword': row['keyword'],
			'score': row['importance_score']
		})
	
	return jsonify(formatted_results)


def highlight_keywords(text, keywords):
	"""Surligne les mots-clés dans le texte."""
	# Trier les mots-clés par longueur (décroissante) pour éviter les problèmes de sous-chaînes
	sorted_keywords = sorted(keywords, key=lambda x: len(x['keyword']), reverse=True)
	
	# Remplacer les occurrences des mots-clés
	for kw in sorted_keywords:
		keyword = kw['keyword']
		pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
		text = pattern.sub(f'<span class="highlight" data-selected="0">{keyword}</span>', text)
	
	return text

def highlight_infobox_relation_key(key, relations):
	"""Ajoute une infobulle HTML aux clés de l'infobox si elles correspondent à une relation connue."""
	key_lower = key.lower()
	matching = [rel for rel in relations if rel['relation_text'] and rel['relation_text'].lower() == key_lower]

	if not matching:
		return key 

	# Création du contenu en ligne
	src_rel = ""
	objects = []
	for rel in matching:
		src_rel = f"{rel['source']} {rel['relation_text']}"
		objects.append(rel['target'])
	if len(objects)>1:
		tooltip_content = src_rel + " [" + ", ".join(objects) + "]"
	else: 
		tooltip_content = src_rel + " " + objects[0]
		

	html = (
		f'<span class="relation-tooltip">'
		f'<span class="relation-underline">{key}</span>'
		f'<span class="tooltip">{tooltip_content}</span>'
		f'</span>'
	)

	return html


def highlight_relations(text, relations):
	"""Insère des balises HTML autour des relations textuelles à des positions précises."""
	relations = sorted(relations, key=lambda r: r['start_char'], reverse=True)

	for rel in relations:
		start = rel['start_char']
		end = rel['end_char']
		relation_text = text[start:end]

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
		text = text[:start] + html + text[end:]

	return text



# Rendre les fonctions disponibles dans les templates
app.jinja_env.filters['highlight_keywords'] = highlight_keywords
app.jinja_env.filters['highlight_relations'] = highlight_relations
app.jinja_env.filters['highlight_infobox_key'] = highlight_infobox_relation_key



def launch_localhost(debug=False):
	app.run(debug=debug)

if __name__ == '__main__':
	launch_localhost(True)
	open_localhost()
	