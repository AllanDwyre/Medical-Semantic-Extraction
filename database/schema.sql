-- Supprimer les tables si elles existent
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS page_keywords;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS relations_type;
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS page_relations;
DROP TABLE IF EXISTS pages;

-- Table des pages
CREATE TABLE IF NOT EXISTS pages (
	id INTEGER PRIMARY KEY,
	title TEXT NOT NULL,
	content TEXT NOT NULL,
	infobox TEXT,
	url TEXT,
	extraction_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des types de relation
CREATE TABLE IF NOT EXISTS relations_type (
	id INTEGER PRIMARY KEY,
	id_opposé INTEGER,
	name TEXT,
	gp_name TEXT,
	help TEXT
);

-- Table des mots-clés
CREATE TABLE IF NOT EXISTS keywords (
	id INTEGER PRIMARY KEY,
	jdm_d INTEGER, -- ID du mot dans jdm (peut etre nul si jdm n'a pas ce mot)
	keyword TEXT NOT NULL UNIQUE,
	frequency INTEGER DEFAULT 0
);

-- Liaison entre pages et mots-clés
CREATE TABLE IF NOT EXISTS page_keywords (
	page_id INTEGER,
	keyword_id INTEGER,
	importance_score FLOAT,
	PRIMARY KEY (page_id, keyword_id),
	FOREIGN KEY (page_id) REFERENCES pages (id),
	FOREIGN KEY (keyword_id) REFERENCES keywords (id)
);

-- Table des relations entre mots-clés
CREATE TABLE IF NOT EXISTS relations (
	id INTEGER PRIMARY KEY,
	source_id INTEGER,
	target_id INTEGER,
	relation_id INTEGER,
	relation_text TEXT,
	confidence_score FLOAT,
	source_type TEXT,
	FOREIGN KEY (source_id) REFERENCES keywords (id),
	FOREIGN KEY (target_id) REFERENCES keywords (id),
	FOREIGN KEY (relation_id) REFERENCES relations_type (id)
);

-- Liaison entre pages et relations
CREATE TABLE IF NOT EXISTS page_relations (
	page_id INTEGER,
	relation_id INTEGER,
	start_char INTEGER,
	end_char INTEGER,
	PRIMARY KEY (page_id, relation_id, start_char),
	FOREIGN KEY (page_id) REFERENCES pages (id),
	FOREIGN KEY (relation_id) REFERENCES relations (id)
);