# API-Parking-Velo-Montpellier-
SAE15 : Collecte et analyse des données d'occupation des parkings voitures et vélos (Open Data Montpellier).

# Collecteur de Données de Mobilité - Montpellier (SAE 15)

Ce projet a été réalisé dans le cadre de la **SAE 15** (Département R&T). Il s'agit d'un script Python permettant de collecter, traiter et sauvegarder les données d'occupation des parkings et des stations de vélos de la métropole de Montpellier en temps réel.

## 📋 Description

L'application interroge les API Open Data de Montpellier pour récupérer :
1.  **L'occupation des parkings** (OffStreet Parking)
2.  **La disponibilité des vélos** (Bike Station)

Les données sont ensuite parsées (analysées) et sauvegardées dans un fichier CSV historique (`historique_parkings.csv`), formaté pour être facilement exploitable sous Excel (séparateur `;`).

## 🛠️ Prérequis

Le projet nécessite **Python 3.x** et la librairie externe `requests`.

### Installation des dépendances
Pour installer la librairie nécessaire à la gestion des requêtes HTTP :
```bash
pip install requests
