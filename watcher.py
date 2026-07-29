#!/usr/bin/env python3
"""
watcher.py — version mobile friendly, multi‑source prototype
But : récupérer rapidement des essais TNBC pertinents et produire results.txt
Usage : python watcher.py
"""

import requests
import csv
from datetime import datetime

PROFILE = {
    "tnbc": True,
    "HER2_low": True,
    "NECTIN4_gain": True,
    "multi_lines": True
}

def fetch_clinicaltrials():
    url = "https://clinicaltrials.gov/api/query/study_fields"
    params = {
        "expr": "triple negative breast cancer",
        "fields": "NCTId,BriefTitle,Condition,LocationCountry,Phase,OverallStatus",
        "min_rnk": 1,
        "max_rnk": 100,
        "fmt": "json"
    }
    headers = {"User-Agent": "SaveMyWife-watcher/1.0"}

    r = requests.get(url, params=params, headers=headers, timeout=30)

    print("STATUS:", r.status_code)
    print("HEADERS:", r.headers)
    print("RAW RESPONSE (first 500 chars):")
    print(r.text[:500])

    try:
        return r.json().get("StudyFieldsResponse", {}).get("StudyFields", [])
    except Exception as e:
        print("JSON ERROR:", e)
        return []

   

def fetch_accesstrial():
    try:
        r = requests.get("https://accesstrial.care/api/trials?condition=TNBC", timeout=10)
        return r.json().get("trials", [])
    except:
        return []

def normalize_trial(t):
    # Retourne un dict uniforme pour l'export
    return {
        "id": (t.get("NCTId") or [""])[0] if isinstance(t.get("NCTId"), list) else t.get("id", ""),
        "title": (t.get("BriefTitle") or [""])[0] if isinstance(t.get("BriefTitle"), list) else t.get("title", ""),
        "phase": (t.get("Phase") or [""])[0] if isinstance(t.get("Phase"), list) else t.get("phase", ""),
        "status": (t.get("OverallStatus") or [""])[0] if isinstance(t.get("OverallStatus"), list) else t.get("status", ""),
        "country": (t.get("LocationCountry") or [""])[0] if isinstance(t.get("LocationCountry"), list) else t.get("country", "")
    }

def filter_trials(trials):
    out = []
    for t in trials:
        title = (t.get("BriefTitle") or [""])[0].lower() if isinstance(t.get("BriefTitle"), list) else (t.get("title","").lower())
        phase = (t.get("Phase") or [""])[0].lower() if isinstance(t.get("Phase"), list) else (t.get("phase","").lower())

        if PROFILE["tnbc"] and "triple" not in title and "tnbc" not in title:
            continue
        if PROFILE["multi_lines"] and not ("phase 1" in phase or "phase 2" in phase):
            continue
        out.append(normalize_trial(t))
    return out

def save_results_txt(trials):
    now = datetime.utcnow().isoformat(timespec='minutes') + "Z"
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write(f"# Results generated {now}\n")
        for t in trials:
            f.write(f"{t['id']} - {t['title']} - {t['phase']} - {t['status']} - {t['country']}\n")

def save_results_csv(trials):
    with open("results.csv", "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id","title","phase","status","country"])
        writer.writeheader()
        for t in trials:
            writer.writerow(t)

def main():
    trials = []
    trials += fetch_clinicaltrials()
    trials += fetch_accesstrial()
    filtered = filter_trials(trials)
    save_results_txt(filtered)
    save_results_csv(filtered)
    print(f"{len(filtered)} essais trouvés. Fichiers results.txt et results.csv créés.")

if __name__ == "__main__":
    main()
