#!/usr/bin/env python3
import json
import re
import requests
from datetime import datetime

MEDICAL_REPORT_PATH = "medical_report.md"
RESULTS_PATH = "results.json"

CLINICALTRIALS_API = "https://clinicaltrials.gov/api/query/study_fields"

def load_medical_report(path=MEDICAL_REPORT_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_profile(text):
    profile = {
        "diagnosis": "TNBC metastatic",
        "biomarkers": [],
        "notes": []
    }

    if "NECTIN4" in text.upper():
        profile["biomarkers"].append("NECTIN4_gain")
    if "PIK3R1" in text.upper():
        profile["biomarkers"].append("PIK3R1_mutation")
    if "TP53" in text.upper():
        profile["biomarkers"].append("TP53_mutation")

    if re.search(r"HER2[^0-9]*1\+", text, re.IGNORECASE):
        profile["biomarkers"].append("HER2_low")

    profile["notes"].append("Profil TNBC métastatique avec NECTIN4/PIK3R1/TP53.")
    return profile

def query_clinicaltrials_tnbc():
    params = {
        "expr": "triple negative breast cancer",
        "fields": "NCTId,BriefTitle,Condition,LocationCountry,Phase,OverallStatus",
        "min_rnk": 1,
        "max_rnk": 100,
        "fmt": "json"
    }
    r = requests.get(CLINICALTRIALS_API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("StudyFieldsResponse", {}).get("StudyFields", [])

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

def build_results(profile, trials):
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "patient_profile": profile,
        "source": "ClinicalTrials.gov",
        "trial_count": len(trials),
        "trials": trials
    }

def main():
    report_text = load_medical_report()
    profile = extract_profile(report_text)
    trials = query_clinicaltrials_tnbc()
    filtered = filter_trials(trials, profile)
    results = build_results(profile, filtered)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
