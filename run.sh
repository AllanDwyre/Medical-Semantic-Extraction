#!/bin/bash

echo ">> Étape 1 : Lancement de l'analyse sémantique..."
python3 main.py

echo ">> Étape 2 : Démarrage du serveur Flask pour visualisation..."
python3 -m "src.visualization.viewer"
echo ">> Tout est en place ! 🚀"
