# TNBC Clinical Trials Watcher  
### Veille clinique automatisée — Europe élargie + biomarqueurs + historique

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![ClinicalTrials.gov](https://img.shields.io/badge/source-ClinicalTrials.gov-orange)
![Europe](https://img.shields.io/badge/coverage-Europe%20élargie-purple)
![TNBC](https://img.shields.io/badge/focus-TNBC-red)
## 📌 Description

**TNBC Clinical Trials Watcher** est un outil de veille clinique avancée permettant de :

- analyser automatiquement les essais cliniques TNBC (Triple Negative Breast Cancer),
- couvrir **toute l’Europe élargie** (France + 30 pays),
- intégrer **tous les centres européens pertinents** (plus de 80 centres),
- détecter les biomarqueurs clés (NECTIN4, BRCA1/2, PD‑L1, PIK3CA, AKT1/2, TMB, MSI…),
- calculer un **score de pertinence clinique**,
- estimer la distance depuis **Pontcharra (Isère)** vers le centre le plus proche,
- générer des fichiers de résultats exploitables,
- conserver un **historique daté complet**,
- identifier les **pays sans essais TNBC** à une date donnée.

Ce projet est conçu pour fonctionner **dans GitHub Codespaces**, sans dépendances cloud, sans API payante, sans services externes.
## 🚀 Fonctionnalités

### 🔍 Analyse des essais TNBC
- Récupération automatique via ClinicalTrials.gov  
- Filtrage TNBC intelligent (détection "triple", "tnbc")  
- Extraction des phases, statuts, résumés, pays  

### 🌍 Europe élargie (activée en permanence)
Pays inclus :  
France, Belgique, Suisse, Allemagne, Italie, Espagne, Pays‑Bas, Royaume‑Uni,  
Suède, Danemark, Norvège, Finlande, Islande,  
Pologne, Tchéquie, Hongrie, Roumanie, Bulgarie,  
Croatie, Serbie, Bosnie, Monténégro, Macédoine du Nord, Slovénie,  
Estonie, Lettonie, Lituanie.

### 🏥 Centres européens complets (80+ centres)
Tous les centres majeurs d’oncologie sont intégrés, avec coordonnées GPS exactes et tri automatique.

### 🧬 Scoring biomarqueurs
Pondérations :
- **NECTIN4** (pondération maximale)
- Phase de l’essai
- Pays
- Bonus biomarqueurs (BRCA1/2, PD‑L1, PIK3CA, AKT1/2, TMB, MSI, HER2, NTRK, FGFR, MET…)

### 📁 Export automatique
- `results.txt`
- `results.csv`
- `summary_for_oncologist.md`

### 🕒 Historique daté
Chaque exécution génère :
- `history/YYYY-MM-DD_results.txt`
- `history/YYYY-MM-DD_summary.md`
- `history/YYYY-MM-DD_empty_countries.txt`

### 📉 Log cumulatif des pays sans essais
- `history/empty_log.txt`
## 📂 Arborescence du projet
watcher.py results.txt results.csv summary_for_oncologist.md history/ 2026-07-28_results.txt 2026-07-28_summary.md 2026-07-28_empty_countries.txt empty_log.txt
## 🛠️ Installation (GitHub Codespaces)

1. Ouvrir un Codespace dans GitHub.
2. Ajouter le fichier `watcher.py` dans le projet.
3. Installer la dépendance :pip install requests
4. Lancer le script :python watcher.py
5. Les fichiers générés apparaissent automatiquement dans le dossier du projet.
## ▶️ Utilisation

Lancer simplement :python watcher.py
Le script :
- récupère les essais,
- filtre TNBC + Europe élargie,
- calcule les scores,
- génère les fichiers,
- met à jour l’historique,
- enregistre les pays sans essais TNBC.
## 📄 Fichiers générés

### Résultats principaux
- `results.txt` — liste des essais triés par score  
- `results.csv` — version tableur  
- `summary_for_oncologist.md` — résumé lisible  

### Historique daté
- `history/YYYY-MM-DD_results.txt`  
- `history/YYYY-MM-DD_summary.md`  
- `history/YYYY-MM-DD_empty_countries.txt`  

### Log cumulatif
- `history/empty_log.txt`
## 👤 Auteur

Projet développé par **Michaël**,  
dans le cadre d’une veille clinique avancée TNBC.