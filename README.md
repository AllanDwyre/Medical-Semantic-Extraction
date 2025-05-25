
# Extraction de relations sémantiques dans wikipedia

## Résumé :
L'informatisation des professions de santé et le développement du dossier médical personnalisé (DMP) entraîne une progression rapide du volume d'information médicale numérique. Les systèmes informatiques médicaux permettent de stocker de l'information (dossier médical, résultats d'examens complémentaires, images et comptes rendus radiologiques par exemple), d'y accéder en vue d'améliorer la prise en charge des patients, de découvrir de nouvelles informations ou de fournir une aide à la décision pour l'amélioration de la qualité des soins. Or, cette information est souvent consultée de façon individuelle et manuelle alors que le format numérique permettrait une analyse informatisée. L'information à exploiter est en grande partie sous forme textuelle et il s'agit alors de pouvoir extraire de façon automatique des données sémantiques. Le besoin de convertir toute cette information sous forme structurée est donc un enjeu majeur. Pour réaliser cette tâche il est nécessaire d'avoir une base de connaissance de spécialité structurée et dynamique (apprentissage permanent).

Pour ce sujet de TER, il s'agira de travailler sur l'extraction de relations sémantiques (synonymie, hyperonymie, causatif, caractéristique..) à partir d'articles médicaux issus de l'encyclopédie Wikipedia et du site sur les maladies rares Orphanet. Cette extraction aura pour but de consolider un réseau lexico-sémantique de spécialité inclus dans le réseau de connaissance générale JeuxDeMots. Il faudra utiliser les ressources et travaux de recherches à votre disposition afin d'élaborer des algorithmes pertinents. Le travail sera composé des tâches suivantes:

* état de l'art sur l'extraction de relations sémantiques à partir de textes non structurés.
* récupérer les pages wikipédia (voire d'autres sites comme orphanet).
* proposer un algorithme d'extraction de relations.
* création d'une base de données susceptible d'être intégrée au réseau.

## Utilisation : 
- pour mettre a jour les package a utilisé : ` pip install -r requirements.txt` 
- pour lancer le web-scrapper pour extraire les documents : `python3 -m src.extraction.extract_documents`
- pour lancer l'analyse et l'extraction sémantique des documents: `python3 main.py`
- pour lancer seulement la visualisation `python3 -m src.visualization.viewer`
- pour lancer les tests d'api `python3 -m unittest tests`