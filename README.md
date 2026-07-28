TNBC Clinical Trials Watcher — Multi‑sources & Personalized Medical Cross‑Analysis

Veille clinique avancée pour Céline — Europe élargie, USA, registres scientifiques, biomarqueurs & centres spécialisés

    

1. 🎯 Objectif du projet

Le TNBC Clinical Trials Watcher est un système de veille clinique avancée conçu pour :

identifier automatiquement les essais cliniques pertinents pour Céline,

croiser ses données médicales personnelles (biomarqueurs, traitements, toxicités, évolution, contraintes),

interroger un ensemble très large de sources cliniques internationales,

fusionner, normaliser, filtrer et scorer les essais,

produire des exports professionnels pour les oncologues,

maintenir un historique daté,

détecter les nouveaux essais,

détecter les essais disparus,

surveiller les pays sans essais TNBC,

prioriser les essais selon la pertinence médicale et la faisabilité géographique.

Ce projet ne remplace aucune décision médicale.Il vise à faire gagner du temps aux oncologues et à ne jamais rater un essai potentiellement utile.

2. 🧬 Croisement des données médicales de Céline

(via medical_report.md)

Le fichier medical_report.md est la source centrale pour personnaliser la veille clinique.

Le watcher extrait automatiquement :

🔬 Biomarqueurs

NECTIN4

BRCA1 / BRCA2

PD‑L1

PIK3CA

AKT1 / AKT2

HER2 / HER2‑low

TMB

MSI

NTRK

FGFR

MET

HRD

AR

TP53

💊 Traitements déjà reçus

chimiothérapie

immunothérapie

ADC (ex : sacituzumab govitecan)

thérapies ciblées

radiothérapie

⚠️ Toxicités / tolérance

neuropathies

toxicités hématologiques

toxicités cardiaques

fatigue sévère

🩻 Imagerie / évolution

progression

stabilité

réponse partielle

nouvelles localisations métastatiques

📅 Dates clés

diagnostic

rechute

progression

début / fin de traitement

🧭 Contraintes personnelles

distance maximale acceptable

centres préférés

centres à éviter

fréquence des visites possible

🏥 Centres déjà consultés

Curie

Gustave Roussy

Léon Bérard

IPC

Lacassagne

Grenoble

3. 🔗 Logique de croisement (Céline ↔ essais ↔ sources)

Le watcher croise :

1. Les données médicales de Céline

2. Les données des essais cliniques

3. Les contraintes géographiques

4. Les biomarqueurs

5. Les lignes de traitement

6. Les toxicités

7. Les sources multiples (14 sources)

Pour produire un score de pertinence personnalisé.

4. 🌍 Sources interrogées (14 sources)

🟩 Déjà intégrées

ClinicalTrials.gov (API JSON + fallback)

EUCTR (scraping HTML + fallback)

🟦 Intégrables immédiatement (faisables techniquement)

CTIS (EU Clinical Trials Information System)

INCa (France)

AccessTrial (France)

Centres français (Curie, GR, Léon Bérard, IPC, Lacassagne…)

MBC Alliance (API JSON)

BreastCancerTrials.org

LBBC Trial Finder

🟧 Veille scientifique proactive

PubMed

ESMO

ASCO

🟪 Bonus (optionnel)

WHO ICTRP

NIH RePORTER

5. 🧠 Scoring personnalisé (médical + géographique + source)

Le score final est :

Score = Biomarqueurs + Phase + Pays + Distance + Source + Compatibilité_médicale

🔬 Pondération biomarqueurs

NECTIN4 → +50

BRCA → +20

PD‑L1 → +15

HER2‑low → +10

PIK3CA / AKT → +10

TMB / MSI → +8

NTRK / FGFR / MET → +8

🧪 Pondération phase

Phase II → +30

Phase I → +20

Phase III → +10 (selon contexte TNBC)

🌍 Pondération pays

France → +20

Europe élargie → +15

USA → +10

📍 Distance

< 100 km → +20

100–300 km → +10

300 km → +5

🧬 Compatibilité médicale

évite les molécules toxiques si toxicités

évite les taxanes si neuropathies

évite les anthracyclines si toxicité cardiaque

priorise les essais ciblés biomarqueurs

6. 🏗️ Architecture technique (modulaire PRO)

watcher/
│
├── watcher.py                # Point d'entrée principal
│
├── sources/                  # Tous les fetchers multi-sources
│   ├── clinicaltrials.py     # ClinicalTrials.gov (API JSON + fallback)
│   ├── euctr.py              # EUCTR (HTML scraping + fallback)
│   ├── ctis.py               # CTIS (HTML scraping)
│   ├── inca.py               # INCa (HTML scraping)
│   ├── accesstrial.py        # AccessTrial (API JSON)
│   ├── centers_france.py     # Centres français (HTML scraping)
│   ├── mbc_alliance.py       # MBC Alliance (API JSON)
│   ├── breastcancertrials.py # BreastCancerTrials (HTML scraping)
│   ├── lbbc.py               # LBBC Trial Finder (HTML scraping)
│   ├── pubmed.py             # PubMed (scraping ciblé)
│   ├── esmo.py               # ESMO abstracts (scraping)
│   ├── asco.py               # ASCO abstracts (scraping)
│
├── merge.py                  # Fusion multi-sources + déduplication
├── normalize.py              # Normalisation des champs essais
├── scoring.py                # Scoring biomarqueurs + phase + pays + source
├── geography.py              # Centres européens + distances + Europe élargie
├── export.py                 # TXT, CSV, JSON, résumé oncologue
├── history.py                # Historique daté + log des pays sans essais
├── profile_celine.py         # Profil médical de Céline (extraction automatique)
├── medical_report.md         # Données médicales de Céline

7. 📂 Fichiers générés

Résultats

results.txt

results.csv

results.json

summary_for_oncologist.md

Historique

history/YYYY-MM-DD_results.txt

history/YYYY-MM-DD_summary.md

history/YYYY-MM-DD_empty_countries.txt

history/empty_log.txt

8. 🧭 Workflow complet

Charger medical_report.md

Extraire biomarqueurs, traitements, toxicités

Interroger 14 sources cliniques

Fusionner les essais

Normaliser les champs

Filtrer TNBC

Appliquer scoring personnalisé

Trier par pertinence

Exporter TXT / CSV / JSON / MD

Mettre à jour l’historique

Détecter nouveaux essais

Détecter essais disparus

Log des pays sans essais TNBC

9. 🧭 Roadmap

Intégration CTIS

Intégration INCa

Intégration AccessTrial

Intégration centres français

Intégration MBC Alliance

Intégration BreastCancerTrials

Intégration LBBC

Intégration PubMed / ESMO / ASCO

Mode “diff J‑1”

Mode “essais disparus”

Export PDF

Interface web minimaliste

10. 👤 Auteur & contexte

Projet conçu par Michaël,pour Céline,dans le cadre d’une veille clinique TNBC avancée,avec l’objectif de ne jamais rater un essai pertinent,et de faire gagner du temps aux oncologues.

11. 🔗 Liens internes (Guided Links)

Profil Céline

Sources cliniques

Architecture du watcher

Scoring biomarqueurs

Historique