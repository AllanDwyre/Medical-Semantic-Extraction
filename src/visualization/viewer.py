from flask import Flask, render_template, request, jsonify
from src.utils.helper import open_localhost
from src.utils.database import get_pages
from collections import defaultdict
from src.semantic_analysis.document import ProcessedDocument, Relation
import sqlite3
import re
import hashlib
import colorsys
import html
import src.semantic_analysis.content_analyser as analyser
import src.utils.helper as helper
from spacy import displacy
from rich import print as rprint

app = Flask(
	__name__,
)

# Configuration
DB_PATH = "database/medical_knowledge.db"
PROCESSED_DATA_PATH = "data/processed/_visualization_data.json"
nlp = helper.load_nlp_model()

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
	
	relation_content_json = [rel.to_dict() for rel in document.relation_content]

	conn.close()
	return render_template('page.html', 
							page= document.info,
							relation_infobox = document.relation_infobox,
							relation_content= document.relation_content,
							relation_content_json=relation_content_json,
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

@app.route('/tool')
def tool():
	"""Permet de travailler les patterns"""
	text = request.args.get('texte', '')

	doc = nlp(text)
	dependency_html = displacy.render(doc, style="dep", page=False)

	return render_template('tool.html', text=text, dependency_html=dependency_html)

@app.template_filter('tokenize_interactive')
def tokenize_interactive(text: str):
	doc = nlp(text)
	html = ""

	for token in doc:
		if token.text.strip() == "":
			html += token.text  # conserve les espaces
		else:
			html += (
				f'<span class="token" data-state="none" onclick="cycleTokenState(this)" data-pos="{token.i}">'
				f'{token.text}</span>'
			)

	return html

def get_path(ancestors: list[analyser.Dependency]) -> list[dict]:
	"""
	Transforme une liste d'ancêtres en une liste JSON-friendly
	avec des infos essentielles pour chaque noeud.
	"""
	return " -> ".join(f"({node.token.pos_}) {node.token.dep_}" for node in ancestors)

def formalize_path(paths: dict[str, str]) -> dict[str, str]:
	last_segments = {}
	for key, path in paths.items():
		segments = [seg.strip() for seg in path.split('->')]
		last_segments[key] = segments[-1] if segments else ''

	result = {}

	for key, path in paths.items():
		segments = [seg.strip() for seg in path.split('->')]

		for other_key, last_seg in last_segments.items():
			if other_key != key and segments[0] == last_seg:
				segments[0] = other_key
				break

		result[key] = ' -> '.join(segments)
	return result



	
@app.route('/search_pattern')
def search_pattern():
	pos = list(map(int, request.args.get('pos', '').strip().split(',')))
	if not pos:
		return jsonify([])
	sujet_pos, pattern_pos, objet_pos = pos
	text = request.args.get('text', '').strip()
	if not text:
		return jsonify([])

	processed_text = nlp(text)
	content_analyser = analyser.ContentAnalyzer(nlp_model=nlp, extractors=[])
	tree = content_analyser.build_dependency_tree(processed_text)

	sujet	: analyser.Dependency = tree.search_in_tree(lambda n: n.token.i == sujet_pos)[0]
	pattern	: analyser.Dependency = tree.search_in_tree(lambda n: n.token.i == pattern_pos)[0]
	objet	: analyser.Dependency = tree.search_in_tree(lambda n: n.token.i == objet_pos)[0]

	sujet_ancestors		: list[analyser.Dependency] = sujet.get_ancestor_chain(stop_at= (pattern, objet))
	pattern_ancestors	: list[analyser.Dependency] = pattern.get_ancestor_chain(stop_at= (sujet, objet))
	objet_ancestors		: list[analyser.Dependency] = objet.get_ancestor_chain(stop_at= (pattern, sujet))

	# Si le la root des ancetres n'est pas un autre des mots chercher, alors on trouve leur encetre commun : 
	if sujet_ancestors[0].head == None: 
		sujet_ancestors = sujet.get_ancestor_chain(stop_at=[sujet.find_lca_three(pattern, objet)])

	if pattern_ancestors[0].head == None: 
		pattern_ancestors = pattern.get_ancestor_chain(stop_at=[pattern.find_lca_three(sujet, objet)])

	if objet_ancestors[0].head == None: 
		objet_ancestors = objet.get_ancestor_chain(stop_at=[objet.find_lca_three(sujet, pattern)])

	sujet_path = get_path(sujet_ancestors)
	pattern_path = get_path(pattern_ancestors)
	objet_path = get_path(objet_ancestors)

	return jsonify(formalize_path({"sujet": sujet_path, "pattern": pattern_path, "objet": objet_path}))




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

def get_color_for_relation(relation_type):
	"""Génère une couleur pastel basée sur le hash du type de relation"""
	# Hash du type de relation
	hash_object = hashlib.md5(relation_type.encode())
	hash_int = int(hash_object.hexdigest(), 16)

	# Génère une teinte entre 0 et 360°
	hue = (hash_int % 360) / 360.0  # Normalisé entre 0–1

	# Pastel = saturation faible, luminosité haute
	saturation = 0.4   # entre 0.3 et 0.5 = doux
	lightness = 0.65   # très clair, mais encore visible

	r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)

	# Convertir en hex
	rgb = (int(r * 255), int(g * 255), int(b * 255))
	return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def ajouter_relation_id(match: re.Match, id: int):
	ancien = match.group(1)
	nouveau = f'{ancien}_{id}'
	return f'data-relation-id="{nouveau}"'


def ajouter_relation(match: re.Match, rel: str):
	ancien = match.group(1)
	rel = html.escape(rel)
	nouveau = f'{ancien} | {rel}'
	return f'<span class="tooltip">{nouveau}</span>'

def remove_brackets(text):
	return re.findall(r"\[([^\[\]]+)\]", text), re.sub(r"\[([^\[\]]+)\]", r"\1", text)

def clean_titles(text):
	"""Rajoute un point a chaque titre pour ne pas détruire le dep parsing"""
	pattern = r'\n([A-Z][^\n\.]*)\n'
	def clean(match : re.Match):
		return f"\n{match.group(1)}.\n"
	return re.findall(pattern, text) , re.sub(pattern, clean ,text)

@app.template_filter('highlight_content')
def highlight_content(content: str, relations: list[Relation]):
	titles, _ = clean_titles(content)
	bold_texts, content = remove_brackets(content)

	elements_to_highlight = []
	
	for i, rel in enumerate(relations):
		sujet_start, sujet_end = rel.get_start_end("sujet")
		pattern_start, pattern_end = rel.get_start_end("pattern")
		objet_start, objet_end = rel.get_start_end("objet")

		
		elements_to_highlight.append((sujet_start, sujet_end, rel.sujet, rel.relation_type, "sujet", rel.id, rel))
		elements_to_highlight.append((pattern_start, pattern_end, rel.pattern, rel.relation_type, "pattern", rel.id, rel))
		elements_to_highlight.append((objet_start, objet_end, rel.objet, rel.relation_type, "objet", rel.id, rel))
	
	elements_to_highlight.sort(key=lambda x: (x[0], -x[1]))

	fragments = []
	last_end = last_fragment_index = 0

	
	rel : Relation
	for (start, end, term, relation_type, element_type, relation_id, rel) in elements_to_highlight:
		
		fragments.append(content[last_end:start])
		alt_title = f"{html.escape(rel.sujet)} {html.escape(rel.relation_type)} {html.escape(rel.objet)}"


		if end <= last_end:
			fragments[last_fragment_index] = re.sub(
				r'<span class="tooltip">([^<]+)</span>',
				lambda match: ajouter_relation(match, alt_title),
				fragments[last_fragment_index]
			)

			fragments[last_fragment_index] = re.sub(
				r'data-relation-id="([^"]+)"',
				lambda match: ajouter_relation_id(match, relation_id),
				fragments[last_fragment_index]
			)
			continue

		color = get_color_for_relation(relation_type)
		
		fragments.append(
			f'<span class="relation-tooltip">'
			f'<span class="highlight-term" '
			f'data-relation-id="{relation_id}" '
			f'style="--term-color: {color};"'
			f'data-relation-type="{relation_type}" '
			f'data-element-type="{element_type}">'
			f'{content[start:end]}</span>'
			f'<span class="tooltip">{alt_title}</span>'
			f'</span>'
		)
		last_fragment_index = len(fragments) - 1
		last_end = end
	fragments.append(content[last_end:])	
	
	highlighted_content = ''.join(fragments)
	
	

	# On separe le texte par des paragraphes et formate les listes
	final = ""
	in_list = False
	for paragraph in highlighted_content.split('\n'):
		match = re.match(r"-\s*(.+)", paragraph)
		if match:
			if not in_list:
				final += "<ul>"
			final += f"<li>{match.group(1)}</li>"
			in_list = True
		else:
			if in_list:
				final += "</ul>"
				in_list = False
			final += f"<p>{paragraph}</p>"

	if in_list:
		final += "</ul>"

	for title in titles:
		pattern = r'<p>(' + re.escape(title) + r')</p>' # \.
		final = re.sub(pattern, r'<h2 style="font-weight: 500;">\1</h2>', final, flags=re.IGNORECASE)

	for term in bold_texts:
		pattern = r'\b(' + re.escape(term) + r')\b'
		final = re.sub(pattern, r'<b style="font-weight: 600;">\1</b>', final, flags=re.IGNORECASE)
	return final


def launch_localhost(debug=False):
	app.run(debug=debug)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description="Lance l'analyse sémantique.")
	parser.add_argument(
		"--debug", "-D",
		action="store_true",
		help="Activer le mode debug (pas de suppression de la DB, logs supplémentaires)"
	)

	args = parser.parse_args()
	launch_localhost(args.debug)
	open_localhost()
	