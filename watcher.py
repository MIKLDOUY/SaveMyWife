#!/usr/bin/env python3
import json
import re
import requests
from datetime import datetime, UTC

MEDICAL_REPORT_PATH = "medical_report.md"
RESULTS_JSON = "results.json"
RESULTS_TXT = "results.txt"
RESULTS_CSV = "results.csv"
SUMMARY_MD = "summary_for_oncologist.md"
ALERTS_LOG = "alerts.log"

###############################################
# 1. Charger le dossier médical
###############################################

def load_medical_report():
    try:
        with open(MEDICAL_REPORT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("ERROR: medical_report.md introuvable.")
        return ""

###############################################
# 2. Extraire le profil patient
###############################################

def extract_profile(text):
    profile = {
        "diagnosis": "TNBC metastatic",
        "biomarkers": [],
        "notes": []
    }

    text_upper = text.upper()

    if "NECTIN4" in text_upper:
        profile["biomarkers"].append("NECTIN4_gain")
    if "PIK3R1" in text_upper:
        profile["biomarkers"].append("PIK3R1_mutation")
    if "TP53" in text_upper:
        profile["biomarkers"].append("TP53_mutation")
    if re.search(r"HER2[^0-9]*1\+", text, re.IGNORECASE):
        profile["biomarkers"].append("HER2_low")

    profile["notes"].append("Profil TNBC métastatique avec biomarqueurs détectés.")

    return profile

###############################################
# 3. Interroger ClinicalTrials.gov (robuste)
###############################################

def fetch_clinicaltrials():
    url = "https://clinicaltrials.gov/api/query/study_fields"
    params = {
        "expr": "triple negative breast cancer",
        "fields": "NCTId,BriefTitle,Condition,LocationCountry,Phase,OverallStatus",
        "min_rnk": 1,
        "max_rnk": 200,
        "fmt": "json"
    }
    headers = {"User-Agent": "SaveMyWife-watcher/1.0"}

    r = requests.get(url, params=params, headers=headers, timeout=30)

    print("STATUS:", r.status_code)
    print("RAW RESPONSE (first 300 chars):")
    print(r.text[:300])

    if r.status_code != 200:
        print("[ClinicalTrials] HTTP error:", r.status_code)
        return []

    try:
        data = r.json()
    except Exception as e:
        print("[ClinicalTrials] Invalid JSON response")
        print("ERROR:", e)
        return []

    return data.get("StudyFieldsResponse", {}).get("StudyFields", [])

###############################################
# 4. Filtrer les essais pertinents
###############################################

def filter_trials(trials, profile):
    filtered = []

    for t in trials:
        nct = t.get("NCTId", [""])[0]
        title = t.get("BriefTitle", [""])[0]
        cond = t.get("Condition", [])
        country = t.get("LocationCountry", [])
        phase = t.get("Phase", [""])[0]
        status = t.get("OverallStatus", [""])[0]

        if status.lower() not in ["recruiting", "not yet recruiting"]:
            continue

        if not any("breast" in c.lower() for c in cond):
            continue

        filtered.append({
            "nct_id": nct,
            "title": title,
            "conditions": cond,
            "countries": country,
            "phase": phase,
            "status": status
        })

    return filtered

###############################################
# 5. Générer les fichiers de sortie
###############################################

def save_json(data):
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_txt(trials):
    with open(RESULTS_TXT, "w", encoding="utf-8") as f:
        for t in trials:
            f.write(f"{t['nct_id']} - {t['title']}\n")

def save_csv(trials):
    with open(RESULTS_CSV, "w", encoding="utf-8") as f:
        f.write("NCT ID,Title,Phase,Status,Countries\n")
        for t in trials:
            countries = ";".join(t["countries"])
            f.write(f"{t['nct_id']},{t['title']},{t['phase']},{t['status']},{countries}\n")

def save_summary(profile, trials):
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("# Synthèse pour l'oncologue\n\n")
        f.write(f"**Généré le :** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write("## Profil patient\n")
        f.write(json.dumps(profile, indent=2))
        f.write("\n\n## Essais pertinents\n")
        for t in trials[:10]:
            f.write(f"- **{t['title']}** (NCT {t['nct_id']}) — Phase {t['phase']}, {t['status']}\n")

def log_alert(message):
    with open(ALERTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(UTC).isoformat()} — {message}\n")

###############################################
# 6. Main
###############################################

def main():
    print("=== SaveMyWife Watcher ===")

    report = load_medical_report()
    profile = extract_profile(report)

    trials = fetch_clinicaltrials()
    filtered = filter_trials(trials, profile)

    results = {
        "generated_at": datetime.now(UTC).isoformat(),
        "patient_profile": profile,
        "trial_count": len(filtered),
        "trials": filtered
    }

    save_json(results)
    save_txt(filtered)
    save_csv(filtered)
    save_summary(profile, filtered)

    log_alert(f"Run completed — {len(filtered)} trials found.")

    print("Generated: results.json, results.txt, results.csv, summary_for_oncologist.md")
    print("Updated: alerts.log")

if __name__ == "__main__":
    main()
