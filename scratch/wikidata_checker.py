import csv
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

def get_wikidata_entity(entity_id):
    try:
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json&props=labels|descriptions|claims|sitelinks"
        req = urllib.request.Request(url, headers={"User-Agent": "ParlamintVerifier/1.0 (academic; parlamint-al)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("entities", {}).get(entity_id, {})
    except Exception as e:
        return {"error": str(e)}

def search_wikidata(query):
    try:
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(query)}&language=sq&format=json&limit=5"
        req = urllib.request.Request(url, headers={"User-Agent": "ParlamintVerifier/1.0 (academic; parlamint-al)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("search", [])
    except Exception as e:
        return []

def main():
    print("=== 1. CHECKING PROMPT SPECIFIC EXAMPLE (Q13045612) ===")
    q_example = get_wikidata_entity("Q13045612")
    print("Q13045612 entity data:")
    print(f"Title / ID: {q_example.get('title', q_example.get('id'))}")
    if "redirects" in q_example:
        print(f"REDIRECTS TO: {q_example['redirects']['to']}")
        target_entity = get_wikidata_entity(q_example['redirects']['to'])
        en_label = target_entity.get("labels", {}).get("en", {}).get("value")
        en_desc = target_entity.get("descriptions", {}).get("en", {}).get("value")
        sq_label = target_entity.get("labels", {}).get("sq", {}).get("value")
        print(f"Target Label (en): {en_label}")
        print(f"Target Label (sq): {sq_label}")
        print(f"Target Description: {en_desc}")
    else:
        en_label = q_example.get("labels", {}).get("en", {}).get("value")
        en_desc = q_example.get("descriptions", {}).get("en", {}).get("value")
        print(f"Label: {en_label}, Desc: {en_desc}")

    print("\nSearching correct Wikidata entity for Erion Braçe...")
    eb_matches = search_wikidata("Erion Braçe")
    for m in eb_matches:
        print(f"  Match: ID={m['id']}, Label={m.get('label')}, Desc={m.get('description')}, URL=https://www.wikidata.org/wiki/{m['id']}")

    print("\n=== 2. SCANNING ALL PERSONS IN metadata/persons.csv ===")
    persons_file = Path("metadata/persons.csv")
    with open(persons_file, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    print(f"Total rows in metadata/persons.csv: {len(reader)}")

    verified_matches = []
    
    for row in reader:
        pid = (row.get("person_id") or "").strip()
        forename = (row.get("forename") or "").strip()
        surname = (row.get("surname") or "").strip()
        full_name = f"{forename} {surname}".strip()
        current_wiki = (row.get("wikidata_id") or "").strip()

        if not full_name or pid == "AL_PERS_LEGJISLATURAXI":
            continue

        matches = search_wikidata(full_name)
        time.sleep(0.05)

        # Let's inspect the best candidate
        best_candidate = None
        for m in matches:
            desc = (m.get("description") or "").lower()
            label = (m.get("label") or "").lower()
            # Check if match is Albanian politician / human / relevant
            if any(term in desc for term in ["albania", "shqipëri", "shqip", "politician", "politikan", "deputet", "minister", "ministër", "kryetar", "jurist", "economist", "diplomat", "activist"]):
                best_candidate = m
                break
        
        # If not found by keyword, check if exact label matches
        if not best_candidate and matches:
            if matches[0].get("label", "").lower() == full_name.lower():
                best_candidate = matches[0]

        verified_matches.append({
            "person_id": pid,
            "forename": forename,
            "surname": surname,
            "full_name": full_name,
            "current_wikidata_id": current_wiki,
            "found_candidate": best_candidate["id"] if best_candidate else None,
            "candidate_label": best_candidate.get("label") if best_candidate else None,
            "candidate_desc": best_candidate.get("description") if best_candidate else None,
        })

    with open("scratch/wikidata_full_audit.json", "w", encoding="utf-8") as f:
        json.dump(verified_matches, f, indent=2, ensure_ascii=False)

    print(f"\nAudit complete. Processed {len(verified_matches)} unique persons.")
    found_count = sum(1 for v in verified_matches if v["found_candidate"])
    print(f"Persons with high-confidence Wikidata match found: {found_count} / {len(verified_matches)}")

if __name__ == "__main__":
    main()
