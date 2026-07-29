#!/usr/bin/env python3
import json
import re
import requests
from datetime import datetime, UTC
from bs4 import BeautifulSoup

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
# 2. Extraire le profil patient + biomarqueurs
###############################################

def extract_profile(text):
    profile = {
        "diagnosis": "TNBC metastatic",
        "biomarkers": [],
        "notes": []
    }

    text_upper = text.upper()

    if "NECTIN4" in text_upper:
        profile["biomarkers"].append("NECTIN4")
    if "PIK3R1" in text_upper:
        profile["biomarkers"].append("PIK3R1")
    if "TP53" in text_upper:
        profile["biomarkers"].append("TP53")
    if re.search(r"HER2[^0-9]*1\+", text, re.IGNORECASE):
        profile["biomarkers"].append("HER2_low")

    profile["notes"].append("Profil TNBC métastatique avec biomarqueurs détectés.")

    return profile

###############################################
# 3. ClinicalTrials.gov (API JSON robuste)
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

    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
    except Exception as e:
        print("[ClinicalTrials] Request error:", e)
        return []

    print("STATUS (CT.gov):", r.status_code)
    print("RAW RESPONSE CT.gov (first 300 chars):")
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

    trials = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
    normalized = []

    for t in trials:
        nct = t.get("NCTId", [""])[0]
        title = t.get("BriefTitle", [""])[0]
        cond = t.get("Condition", [])
        country = t.get("LocationCountry", [])
        phase = t.get("Phase", [""])[0]
        status = t.get("OverallStatus", [""])[0]

        normalized.append({
            "source": "CT.gov",
            "nct_id": nct,
            "title": title,
            "conditions": cond,
            "countries": country,
            "phase": phase,
            "status": status
        })

    print(f"[ClinicalTrials] Parsed {len(normalized)} trials")
    return normalized

###############################################
# 4. WHO ICTRP (HTML + BeautifulSoup, parsing générique)
###############################################

def fetch_who_ictrp():
    url = "https://trialsearch.who.int/TrialSearch/TrialSearch.aspx"
    params = {"cond": "triple negative breast cancer"}

    try:
        r = requests.get(url, params=params, timeout=30)
    except Exception as e:
        print("[WHO ICTRP] Request error:", e)
        return []

    print("STATUS (WHO ICTRP):", r.status_code)
    print("RAW RESPONSE WHO (first 300 chars):")
    print(r.text[:300])

    if r.status_code != 200:
        print("[WHO ICTRP] HTTP error:", r.status_code)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    trials = []

    # Parsing générique : à ajuster après inspection du HTML réel.
    table = soup.find("table")
    if not table:
        print("[WHO ICTRP] No table found")
        return []

    for row in table.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 2:
            continue

        title = cols[0]
        cond = cols[1]

        if "breast" not in cond.lower():
            continue

        trials.append({
            "source": "WHO ICTRP",
            "nct_id": "",
            "title": title,
            "conditions": [cond],
            "countries": [],
            "phase": "",
            "status": ""
        })

    print(f"[WHO ICTRP] Parsed {len(trials)} trials")
    return trials

###############################################
# 5. EUCTR / INCa / CTIS / centres FR — hooks
###############################################

def fetch_euctr():
    print("[EUCTR] TODO: implement real scraping/API")
    return []

def fetch_inca():
    print("[INCa] TODO: implement real scraping/API")
    return []

def fetch_ctis():
    print("[CTIS] TODO: implement real scraping/API")
    return []

def fetch_french_centers():
    print("[FR Centers] TODO: implement real integration (Curie, IPC, CLB, GR)")
    return []

###############################################
# 6. Scoring clinique + matching biomarqueurs
###############################################

def score_trial(trial, profile):
    score = 0

    # Source
    if trial.get("source") == "CT.gov":
        score += 2
    if trial.get("source") == "WHO ICTRP":
        score += 1

    # Phase
    phase = trial.get("phase", "").lower()
    if "3" in phase:
        score += 3
    elif "2" in phase:
        score += 2
    elif "1" in phase:
        score += 1

    # Statut
    status = trial.get("status", "").lower()
    if "recruiting" in status:
        score += 2
    elif "not yet recruiting" in status:
        score += 1

    # TNBC / triple negative dans le titre
    title = trial.get("title", "").lower()
    if "triple negative" in title or "tnbc" in title:
        score += 3

    # Matching biomarqueurs dans le titre
    biomarkers = profile.get("biomarkers", [])
    for bm in biomarkers:
        if bm.lower() in title:
            score += 2

    return score

###############################################
# 7. Filtrer + trier les essais pertinents
###############################################

def filter_and_rank_trials(trials, profile):
    filtered = []

    for t in trials:
        title = t.get("title", "")
        cond = t.get("conditions", [])
        status = t.get("status", "")
        phase = t.get("phase", "")
        countries = t.get("countries", [])
        nct = t.get("nct_id", "")
        source = t.get("source", "unknown")

        # condition sein
        if not any("breast" in c.lower() for c in cond):
            continue

        # statut si disponible
        if status and status.lower() not in ["recruiting", "not yet recruiting", ""]:
            continue

        s = score_trial(t, profile)

        filtered.append({
            "source": source,
            "nct_id": nct,
            "title": title,
            "conditions": cond,
            "countries": countries,
            "phase": phase,
            "status": status,
            "score": s
        })

    # tri par score décroissant
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered

###############################################
# 8. Générer les fichiers de sortie
###############################################

def save_json(data):
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_txt(trials):
    with open(RESULTS_TXT, "w", encoding="utf-8") as f:
        for t in trials:
            src = t.get("source", "unknown")
            f.write(f"[{src}] {t['nct_id']} (score {t['score']}) - {t['title']}\n")

def save_csv(trials):
    with open(RESULTS_CSV, "w", encoding="utf-8") as f:
        f.write("Source,NCT ID,Title,Phase,Status,Countries,Score\n")
        for t in trials:
            countries = ";".join(t["countries"])
            f.write(
                f"{t.get('source','')},{t['nct_id']},{t['title']},{t['phase']},{t['status']},{countries},{t['score']}\n"
            )

def save_summary(profile, trials):
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("# Synthèse pour l'oncologue\n\n")
        f.write(f"**Généré le :** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write("## Profil patient\n")
        f.write(json.dumps(profile, indent=2))
        f.write("\n\n## Essais pertinents (multi-sources, triés par score)\n")
        for t in trials[:20]:
            src = t.get("source", "unknown")
            f.write(
                f"- **{t['title']}** (source {src}, NCT {t['nct_id']}) — Phase {t['phase']}, {t['status']}, score {t['score']}\n"
            )

def log_alert(message):
    with open(ALERTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(UTC).isoformat()} — {message}\n")

###############################################
# 9. Main
###############################################

def main():
    print("=== SaveMyWife Watcher (multi-sources + scoring) ===")

    report = load_medical_report()
    profile = extract_profile(report)

    trials = []
    trials += fetch_clinicaltrials()
    trials += fetch_who_ictrp()
    trials += fetch_euctr()
    trials += fetch_inca()
    trials += fetch_ctis()
    trials += fetch_french_centers()

    ranked = filter_and_rank_trials(trials, profile)

    results = {
        "generated_at": datetime.now(UTC).isoformat(),
        "patient_profile": profile,
        "trial_count": len(ranked),
        "trials": ranked
    }

    save_json(results)
    save_txt(ranked)
    save_csv(ranked)
    save_summary(profile, ranked)

    log_alert(f"Run completed — {len(ranked)} ranked trials from {len(trials)} raw entries.")

    print("Generated: results.json, results.txt, results.csv, summary_for_oncologist.md")
    print("Updated: alerts.log")

if __name__ == "__main__":
    main()
