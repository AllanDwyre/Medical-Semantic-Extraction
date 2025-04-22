-- Supprimer les tables si elles existent
DROP TABLE IF EXISTS page_relations;
DROP TABLE IF EXISTS relation_patterns;
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS patterns;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS relations_type;
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
	keyword TEXT NOT NULL UNIQUE, -- normalized
	frequency INTEGER DEFAULT 0
);

-- Table des chaine de mot representant une relation (est une; est sur; fait partie de; ...)
CREATE TABLE IF NOT EXISTS patterns (
	id INTEGER PRIMARY KEY,
	pattern TEXT NOT NULL UNIQUE, -- normalized
);

-- Table des relations entre mots-clés
CREATE TABLE IF NOT EXISTS relations (
	id INTEGER PRIMARY KEY,
	source_id INTEGER,
	target_id INTEGER,
	pattern_id INTEGER,
	predicted_relation_type INTEGER,
	confidence_score FLOAT,
	FOREIGN KEY (source_id) REFERENCES keywords (id),
	FOREIGN KEY (target_id) REFERENCES keywords (id),
	FOREIGN KEY (pattern_id) REFERENCES patterns (id),
	FOREIGN KEY (predicted_relation_type) REFERENCES relations_type (id)
);

-- Table des relations_type et patterns (est une : r_isa= 50, r_data = 2, ...)
CREATE TABLE IF NOT EXISTS relation_patterns (
	relation_type_id INTEGER,
	pattern_id INTEGER,
	frequency INTEGER,
	PRIMARY KEY (relation_type_id, pattern_id),
	FOREIGN KEY (relation_type_id) REFERENCES relations_type (id),
	FOREIGN KEY (pattern_id) REFERENCES patterns (id),
);

-- Liaison entre pages et mots-clés
CREATE TABLE IF NOT EXISTS page_relations (
	page_id INTEGER,
	relation_id INTEGER,
	start_rel TEXT, -- Start k1; Start rel; Start k2; 
	end_rel TEXT, -- End k1; End rel; End k2; 
	PRIMARY KEY (page_id, keyword_id),
	FOREIGN KEY (page_id) REFERENCES pages (id),
	FOREIGN KEY (relation_id) REFERENCES relations (id)
);