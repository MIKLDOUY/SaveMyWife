#!/usr/bin/env python3
"""
watcher.py — Version stable pour GitHub Codespaces
--------------------------------------------------
Ce script :
- Récupère les essais cliniques TNBC depuis ClinicalTrials.gov
- Filtre les essais pertinents (France + Europe élargie)
- Analyse les biomarqueurs (NECTIN4, BRCA, PD-L1, etc.)
- Calcule un score de pertinence
- Calcule la distance depuis Pontcharra vers le centre le plus proche
- Génère :
    - results.txt
    - results.csv
    - summary_for_oncologist.md
"""

import requests
import csv
import math
from datetime import datetime
# ------------------------------------------------------------
# CONFIGURATION GÉOGRAPHIQUE
# ------------------------------------------------------------

BASE_LOCATION = {"lat": 45.333, "lon": 5.866}  # Pontcharra

# Europe élargie activée systématiquement
ALLOWED_COUNTRIES = {
    # Europe de l'Ouest
    "france": "FR",
    "belgium": "BE",
    "switzerland": "CH",
    "germany": "DE",
    "italy": "IT",
    "spain": "ES",
    "netherlands": "NL",
    "united kingdom": "GB",

    # Europe du Nord
    "sweden": "SE",
    "denmark": "DK",
    "norway": "NO",
    "finland": "FI",
    "iceland": "IS",

    # Europe de l'Est
    "poland": "PL",
    "czech republic": "CZ",
    "hungary": "HU",
    "romania": "RO",
    "bulgaria": "BG",

    # Balkans
    "croatia": "HR",
    "serbia": "RS",
    "bosnia": "BA",
    "montenegro": "ME",
    "north macedonia": "MK",
    "slovenia": "SI",

    # Baltique
    "estonia": "EE",
    "latvia": "LV",
    "lithuania": "LT"
}
# ------------------------------------------------------------
# CENTRES EUROPÉENS PERTINENTS
# ------------------------------------------------------------

CENTERS = [
    # France
    ("Gustave Roussy, Villejuif", "France", 48.792, 2.357),
    ("Institut Curie, Paris", "France", 48.840, 2.315),
    ("Centre Léon Bérard, Lyon", "France", 45.748, 4.855),
    ("IPC, Marseille", "France", 43.296, 5.369),
    ("Centre Antoine Lacassagne, Nice", "France", 43.703, 7.266),

    # Belgique
    ("Institut Jules Bordet, Bruxelles", "Belgium", 50.835, 4.352),
    ("UZ Leuven, Leuven", "Belgium", 50.879, 4.700),

    # Suisse
    ("CHUV Lausanne", "Switzerland", 46.521, 6.632),
    ("HUG Genève", "Switzerland", 46.201, 6.145),

    # Allemagne
    ("Charité, Berlin", "Germany", 52.520, 13.405),

    # Italie
    ("Istituto Europeo di Oncologia, Milan", "Italy", 45.462, 9.190),

    # Espagne
    ("Hospital Clinic Barcelona", "Spain", 41.385, 2.173),

    # Pays-Bas
    ("Netherlands Cancer Institute, Amsterdam", "Netherlands", 52.355, 4.912),

    # Royaume-Uni
    ("Royal Marsden, London", "United Kingdom", 51.403, -0.168)
]
# ------------------------------------------------------------
# BIOMARQUEURS ET PONDÉRATIONS
# ------------------------------------------------------------

WEIGHT_NECTIN4 = 50.0
WEIGHT_PHASE = 30.0
WEIGHT_COUNTRY = 20.0

BONUS_KEYWORDS = {
    "brca1": 8.0, "brca2": 8.0,
    "pd-l1": 6.0, "pdl1": 6.0,
    "pik3r1": 5.0, "pik3ca": 5.0,
    "akt1": 5.0, "akt2": 4.0,
    "tmb": 4.0, "msi": 4.0,
    "her2": 4.0,
    "ntrk": 6.0, "fgfr": 4.0, "met": 4.0,
    "hrd": 3.0, "ar": 2.0, "tp53": 2.0
}
def safe_get_list_field(obj, key):
    """Retourne toujours une liste, même si l’API renvoie une string."""
    v = obj.get(key, "")
    return v if isinstance(v, list) else [str(v)]

def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points géographiques."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def nearest_center_distance(country_name):
    """Trouve le centre le plus proche de Pontcharra dans le pays donné."""
    best = (None, 99999.0)

    for name, ctry, lat, lon in CENTERS:
        if ctry.lower() == country_name.lower():
            d = haversine(BASE_LOCATION["lat"], BASE_LOCATION["lon"], lat, lon)
            if d < best[1]:
                best = (name, d)

    if best[0] is None:
        for name, ctry, lat, lon in CENTERS:
            d = haversine(BASE_LOCATION["lat"], BASE_LOCATION["lon"], lat, lon)
            if d < best[1]:
                best = (name, d)

    return best
def fetch_clinicaltrials():
    """Récupère les essais TNBC depuis ClinicalTrials.gov."""
    url = (
        "https://clinicaltrials.gov/api/query/study_fields?"
        "expr=triple+negative+breast+cancer&"
        "fields=NCTId,BriefTitle,Condition,OverallStatus,Phase,LocationCountry,BriefSummary&"
        "min_rnk=1&max_rnk=200&fmt=json"
    )
    r = requests.get(url, timeout=15)

    try:
        data = r.json()
        return data.get("StudyFieldsResponse", {}).get("StudyFields", [])
    except Exception:
        print("Erreur JSON ClinicalTrials.gov")
        print(r.text[:500])
        return []
def phase_score(phase_text):
    p = (phase_text or "").lower()
    if "phase 2" in p: return 1.0
    if "phase 1" in p: return 0.6
    if "phase 3" in p: return 0.3
    return 0.5

def country_score(country_text):
    c = (country_text or "").lower()
    if c == "france": return 1.0
    if c in ALLOWED_COUNTRIES: return 0.8
    return 0.5

def compute_score_and_flags(trial):
    text = " ".join(
        safe_get_list_field(trial, "BriefTitle") +
        safe_get_list_field(trial, "Condition") +
        safe_get_list_field(trial, "BriefSummary")
    ).lower()

    nectin4_flag = 1.0 if "nectin4" in text else 0.0
    flags = {k: (k in text) for k in BONUS_KEYWORDS}

    phase = safe_get_list_field(trial, "Phase")[0]
    country = safe_get_list_field(trial, "LocationCountry")[0]

    pscore = phase_score(phase)
    cscore = country_score(country)

    base_raw = WEIGHT_NECTIN4 * nectin4_flag + WEIGHT_PHASE * pscore + WEIGHT_COUNTRY * cscore
    bonus = sum(w for k, w in BONUS_KEYWORDS.items() if flags[k])

    max_possible = WEIGHT_NECTIN4 + WEIGHT_PHASE + WEIGHT_COUNTRY + sum(BONUS_KEYWORDS.values())
    score = round(((base_raw + bonus) / max_possible) * 100, 1)

    return score, flags
def normalize_trial(t):
    id_ = safe_get_list_field(t, "NCTId")[0]
    title = safe_get_list_field(t, "BriefTitle")[0]
    phase = safe_get_list_field(t, "Phase")[0]
    status = safe_get_list_field(t, "OverallStatus")[0]
    country = safe_get_list_field(t, "LocationCountry")[0]
    summary = safe_get_list_field(t, "BriefSummary")[0]

    score, flags = compute_score_and_flags(t)
    center_name, dist_km = nearest_center_distance(country)

    return {
        "id": id_,
        "title": title,
        "phase": phase,
        "status": status,
        "country": country,
        "distance_km": round(dist_km, 1),
        "nearest_center": center_name,
        "score": score,
        "flags": flags,
        "summary": summary
    }
def filter_and_normalize(trials):
    out = []

    for t in trials:
        country = safe_get_list_field(t, "LocationCountry")[0].lower()

        # Filtre pays : France + Europe élargie
        if country != "france" and country not in ALLOWED_COUNTRIES:
            continue

        # Filtre TNBC
        text = " ".join(
            safe_get_list_field(t, "BriefTitle") +
            safe_get_list_field(t, "Condition")
        ).lower()

        if "triple" not in text and "tnbc" not in text:
            continue

        out.append(normalize_trial(t))

    out.sort(key=lambda x: (-x["score"], x["distance_km"]))
    return out
def save_results_txt(trials):
    now = datetime.utcnow().isoformat(timespec='minutes') + "Z"
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write(f"# Results generated {now}\n")
        for t in trials:
            flags = ",".join([k for k, v in t["flags"].items() if v])
            f.write(
                f"{t['id']} | {t['score']} | {t['phase']} | {t['status']} | "
                f"{t['country']} | {t['distance_km']} km | {t['nearest_center']} | "
                f"{t['title']} | {flags}\n"
            )

def save_results_csv(trials):
    with open("results.csv", "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = ["id", "score", "phase", "status", "country",
                      "distance_km", "nearest_center", "flags", "title", "summary"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for t in trials:
            writer.writerow({
                "id": t["id"],
                "score": t["score"],
                "phase": t["phase"],
                "status": t["status"],
                "country": t["country"],
                "distance_km": t["distance_km"],
                "nearest_center": t["nearest_center"],
                "flags": ",".join([k for k, v in t["flags"].items() if v]),
                "title": t["title"],
                "summary": t["summary"]
            })

def generate_summary_for_oncologist(trials, top_n=5):
    top = trials[:top_n]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    with open("summary_for_oncologist.md", "w", encoding="utf-8") as f:
        f.write(f"# Summary for Oncologist — generated {now}\n\n")

        if not top:
            f.write("Aucun essai trouvé.\n")
            return

        for i, t in enumerate(top, 1):
            f.write(f"## {i}. {t['id']} — {t['title']}\n")
            f.write(f"- Score : {t['score']}/100\n")
            f.write(f"- Phase : {t['phase']} — Status : {t['status']}\n")
            f.write(f"- Pays : {t['country']}\n")
            f.write(f"- Centre le plus proche : {t['nearest_center']} ({t['distance_km']} km)\n")

            flags = [k.upper() for k, v in t["flags"].items() if v]
            if flags:
                f.write(f"- Biomarqueurs détectés : {', '.join(flags)}\n")

            f.write("\n")
def main():
    print("Fetching ClinicalTrials.gov...")
    trials = fetch_clinicaltrials()

    print(f"Total raw trials: {len(trials)}")

    filtered = filter_and_normalize(trials)
    print(f"Filtered: {len(filtered)} trials")

    save_results_txt(filtered)
    save_results_csv(filtered)
    generate_summary_for_oncologist(filtered)

    print("Generated: results.txt, results.csv, summary_for_oncologist.md")

if __name__ == "__main__":
    main()
