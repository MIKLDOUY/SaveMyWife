#!/usr/bin/env python3
"""
watcher.py — version complète "tout inclus"
- Sources : ClinicalTrials.gov (principal), AccessTrial (best-effort)
- Filtrage : TNBC, France/Europe
- Détection de biomarqueurs : NECTIN4, PIK3R1, TP53, BRCA1/2, PD-L1, PIK3CA, AKT1, TMB, MSI, HER2, NTRK, FGFR, MET, HRD, AR, ...
- Score : pondération principale (NECTIN4 + phase + pays) + bonus mots-clés
- Distance : Haversine depuis Pontcharra (coordonnées fixes)
- Sorties : results.txt, results.csv, summary_for_oncologist.md
Usage : python watcher.py
"""

import requests
import csv
import math
import sys
from datetime import datetime

# ---------- CONFIGURATION FIXE ----------
BASE_LOCATION = {"lat": 45.333, "lon": 5.866}  # Pontcharra (fixe)

ALLOWED_COUNTRIES = {
    "france": "FR", "germany": "DE", "spain": "ES", "italy": "IT", "belgium": "BE",
    "netherlands": "NL", "switzerland": "CH", "united kingdom": "GB",
    "portugal": "PT", "austria": "AT", "sweden": "SE", "denmark": "DK",
    "norway": "NO", "poland": "PL", "czech republic": "CZ", "ireland": "IE"
}

# Liste de centres (nom, pays, lat, lon)
CENTERS = [
    ("Gustave Roussy, Villejuif", "France", 48.792, 2.357),
    ("Institut Curie, Paris", "France", 48.840, 2.315),
    ("Centre Léon Bérard, Lyon", "France", 45.748, 4.855),
    ("IPC, Marseille", "France", 43.296, 5.369),
    ("Centre Antoine Lacassagne, Nice", "France", 43.703, 7.266),
    ("Royal Marsden, London", "United Kingdom", 51.403, -0.168),
    ("Charité, Berlin", "Germany", 52.520, 13.405),
    ("Istituto Europeo di Oncologia, Milan", "Italy", 45.462, 9.190)
]

# Pondérations principales (modifiable)
WEIGHT_NECTIN4 = 50.0
WEIGHT_PHASE = 30.0
WEIGHT_COUNTRY = 20.0

# Bonus keywords weights (additionnels)
BONUS_KEYWORDS = {
    "brca1": 8.0, "brca2": 8.0,
    "pd-l1": 6.0, "pdl1": 6.0,
    "pik3r1": 5.0, "pik3ca": 5.0, "akt1": 5.0, "akt2": 4.0,
    "tmb": 4.0, "msi": 4.0,
    "her2": 4.0,
    "ntrk": 6.0, "fgfr": 4.0, "met": 4.0,
    "hrd": 3.0, "ar": 2.0, "tp53": 2.0
}
# -------------------------------------------------------

def safe_get_list_field(obj, key):
    v = obj.get(key, "")
    if isinstance(v, list):
        return v
    if v is None:
        return [""]
    return [str(v)]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))

def nearest_center_distance(country_name):
    best = (None, 99999.0)
    if country_name:
        for name, ctry, lat, lon in CENTERS:
            if ctry.lower() == country_name.strip().lower():
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
    url = (
        "https://clinicaltrials.gov/api/query/study_fields?"
        "expr=triple+negative+breast+cancer&"
        "fields=NCTId,BriefTitle,Condition,OverallStatus,Phase,LocationCountry,BriefSummary&"
        "min_rnk=1&max_rnk=200&fmt=json"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("StudyFieldsResponse", {}).get("StudyFields", [])
    except Exception as e:
        print("Error fetching ClinicalTrials.gov:", e, file=sys.stderr)
        return []

def fetch_accesstrial():
    try:
        r = requests.get("https://accesstrial.care/api/trials?condition=TNBC", timeout=10)
        r.raise_for_status()
        data = r.json()
        out = []
        for t in data.get("trials", []):
            out.append({
                "NCTId": t.get("id") or "",
                "BriefTitle": [t.get("title","")],
                "Condition": [t.get("condition","")],
                "OverallStatus": [t.get("status","")],
                "Phase": [t.get("phase","")],
                "LocationCountry": [t.get("country","")],
                "BriefSummary": [t.get("summary","")]
            })
        return out
    except Exception:
        return []

def contains_keyword(text, keywords):
    if not text:
        return False
    s = text.lower()
    for k in keywords:
        if k.lower() in s:
            return True
    return False

def phase_score(phase_text):
    p = (phase_text or "").lower()
    if "phase 1" in p and "phase 2" in p:
        return 1.0
    if "phase 2" in p:
        return 1.0
    if "phase 1" in p:
        return 0.6
    if "phase 3" in p:
        return 0.3
    return 0.5

def country_score(country_text):
    if not country_text:
        return 0.5
    c = country_text.strip().lower()
    if c == "france":
        return 1.0
    if c in ALLOWED_COUNTRIES:
        return 0.8
    for k in ALLOWED_COUNTRIES.keys():
        if k.lower() in c:
            return 0.8
    return 0.5

def compute_score_and_flags(trial):
    title = " ".join(safe_get_list_field(trial, "BriefTitle"))
    cond = " ".join(safe_get_list_field(trial, "Condition"))
    summary = " ".join(safe_get_list_field(trial, "BriefSummary"))
    text = " ".join([title, cond, summary]).lower()

    # main flags
    nectin4_flag = 1.0 if "nectin4" in text else 0.0

    # bonus flags detection
    flags = {}
    for k in BONUS_KEYWORDS.keys():
        flags[k] = True if k in text else False

    # phase and country
    phase = safe_get_list_field(trial, "Phase")[0]
    country = safe_get_list_field(trial, "LocationCountry")[0]
    pscore = phase_score(phase)
    cscore = country_score(country)

    base_raw = WEIGHT_NECTIN4 * nectin4_flag + WEIGHT_PHASE * pscore + WEIGHT_COUNTRY * cscore
    bonus = 0.0
    for k, w in BONUS_KEYWORDS.items():
        if k != "nectin4" and flags.get(k):
            bonus += w

    max_possible = WEIGHT_NECTIN4 + WEIGHT_PHASE + WEIGHT_COUNTRY + sum(v for kk, v in BONUS_KEYWORDS.items() if kk != "nectin4")
    score = round(((base_raw + bonus) / max_possible) * 100, 1)
    return score, flags

def normalize_trial(t):
    id_ = safe_get_list_field(t, "NCTId")[0] or t.get("id","")
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
        "distance_km": round(dist_km,1),
        "nearest_center": center_name or "",
        "score": score,
        "flags": flags,
        "summary": summary
    }

def filter_and_normalize(trials):
    out = []
    for t in trials:
        country = safe_get_list_field(t, "LocationCountry")[0]
        if country:
            c = country.strip().lower()
            if c != "france" and c not in ALLOWED_COUNTRIES:
                matched = False
                for k in ALLOWED_COUNTRIES.keys():
                    if k.lower() in c or c in k.lower():
                        matched = True
                        break
                if not matched:
                    continue
        text = " ".join(safe_get_list_field(t, "BriefTitle") + safe_get_list_field(t, "Condition"))
        if not contains_keyword(text, ["triple", "tnbc"]):
            continue
        out.append(normalize_trial(t))
    out.sort(key=lambda x: (-x["score"], x["distance_km"]))
    return out

def save_results_txt(trials):
    now = datetime.utcnow().isoformat(timespec='minutes') + "Z"
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write(f"# Results generated {now}\n")
        f.write("# id | score | phase | status | country | distance_km | nearest_center | title | flags\n")
        for t in trials:
            flags_str = ",".join([k for k,v in t["flags"].items() if v])
            f.write(f"{t['id']} | {t['score']} | {t['phase']} | {t['status']} | {t['country']} | {t['distance_km']} km | {t['nearest_center']} | {t['title']} | {flags_str}\n")

def save_results_csv(trials):
    with open("results.csv", "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = ["id","score","phase","status","country","distance_km","nearest_center","flags","title","summary"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for t in trials:
            row = {
                "id": t.get("id",""),
                "score": t.get("score",""),
                "phase": t.get("phase",""),
                "status": t.get("status",""),
                "country": t.get("country",""),
                "distance_km": t.get("distance_km",""),
                "nearest_center": t.get("nearest_center",""),
                "flags": ",".join([k for k,v in t["flags"].items() if v]),
                "title": t.get("title",""),
                "summary": t.get("summary","")
            }
            writer.writerow(row)

def generate_summary_for_oncologist(trials, top_n=5):
    patient_summary = "Dossier médical non trouvé (medical_report.md absent)."
    try:
        with open("medical_report.md", "r", encoding="utf-8") as f:
            md = f.read()
            lines = [l.strip() for l in md.splitlines() if l.strip()]
            patient_summary = "\n".join(lines[:20])
    except Exception:
        pass

    top = trials[:top_n]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open("summary_for_oncologist.md", "w", encoding="utf-8") as f:
        f.write(f"# Summary for Oncologist — generated {now}\n\n")
        f.write("## Patient (extrait)\n")
        f.write(patient_summary + "\n\n")
        f.write("## Top candidate trials (automatically filtered & scored)\n\n")
        if not top:
            f.write("No candidate trials found for France/Europe with TNBC filter.\n")
            return
        for i, t in enumerate(top, 1):
            f.write(f"### {i}. {t['id']} — {t['title']}\n")
            f.write(f"- **Score**: {t['score']} / 100\n")
            f.write(f"- **Phase**: {t['phase']} — **Status**: {t['status']}\n")
            f.write(f"- **Country**: {t['country']} — **Nearest center**: {t['nearest_center']} ({t['distance_km']} km)\n")
            flags = [k.upper() for k,v in t["flags"].items() if v]
            if flags:
                f.write(f"- **Detected keywords**: {', '.join(flags)}\n")
            s = (t.get("summary") or "").strip()
            if s:
                f.write(f"- **Brief**: {s[:350]}{'...' if len(s)>350 else ''}\n")
            f.write("\n")
        f.write("## Notes\n- Document factuel, ne remplace pas l'avis médical.\n- Vérifier critères d'inclusion/exclusion et disponibilité des places.\n")

def main():
    print("Fetching trials from ClinicalTrials.gov ...")
    trials = fetch_clinicaltrials()
    print(f"Fetched {len(trials)} records from ClinicalTrials.gov")
    print("Fetching AccessTrial (best-effort)...")
    trials += fetch_accesstrial()
    print(f"Total raw records: {len(trials)}")
    filtered = filter_and_normalize(trials)
    print(f"Filtered & normalized: {len(filtered)} trials (France/Europe + TNBC)")
    save_results_txt(filtered)
    save_results_csv(filtered)
    generate_summary_for_oncologist(filtered, top_n=5)
    print("Files written: results.txt, results.csv, summary_for_oncologist.md")

if __name__ == "__main__":
    main()