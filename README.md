# 🅿️ Observatoire Mobilité Montpellier (SAE 1.5)

> **Projet d'analyse de données : Occupation des Parkings & Vélos** > *IUT de Béziers - R&T - Janvier 2026*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Data](https://img.shields.io/badge/OpenData-Montpellier-green)
![Status](https://img.shields.io/badge/Maintenu-Oui-success)

## 📋 Contexte de la Mission

Mandatés par la **Mairie de Montpellier**, nous avons réalisé une étude double sur l'utilisation des infrastructures de stationnement de la métropole. Ce projet s'inscrit dans la politique de développement de la ville et vise à répondre aux questions stratégiques de Monsieur le Maire concernant :

1.  **Le stationnement automobile :** Taux de remplissage, saturation et dimensionnement.
2.  **Le stationnement cycliste :** Disponibilité des vélos en libre-service.
3.  **L'intermodalité :** Le bon fonctionnement du relais "Voiture / Vélo" (P+R).

## 🎯 Objectifs de l'Analyse

Ce dépôt contient les scripts de collecte, les jeux de données et l'analyse permettant de répondre aux problématiques suivantes :
* Les parkings sont-ils bien dimensionnés ?
* Quand saturent-ils ? (Identification des pics d'affluence).
* Existe-t-il une corrélation entre l'usage de la voiture et celui du vélo ?
* Quel est l'impact du Tramway sur le choix modal ?

## ⚙️ Architecture Technique

### 1. Collecte Automatisée (`main.py`)
Le script Python principal interroge l'API **Open Data Montpellier** en temps réel.
* **Sources de données :**
    * Flux Parking Voitures (`TAM_MMM_COURS`)
    * Flux Stations Vélos (`TAM_MMM_VELOMAG`)
* **Traitement :** Parsing des données brutes, extraction des places libres/totales, calcul du pourcentage d'occupation.
* **
