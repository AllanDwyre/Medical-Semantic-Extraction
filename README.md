# Projet d'extraction sémantique de données médical

## Utilisation : 
- pour mettre a jour les package a utilisé : ` pip install -r requirements.txt` 
- pour lancer le web-scrapper pour extraire les documents : `python3 -m src.extraction.extract_documents`
- pour lancer l'analyse et l'extraction sémantique des documents: `python3 main.py`
- pour lancer seulement la visualisation `python3 -m src.visualization.viewer`
- pour lancer les tests d'api `python3 -m unittest tests.jdm_test`