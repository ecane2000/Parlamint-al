import csv
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path("/Users/ecane/Library/CloudStorage/GoogleDrive-ecane2000@gmail.com/Other computers/My Laptop/Google Drive/Project_VSC/Parlamint-al")
SCRATCH_DIR = BASE_DIR / "scratch"

def check_single_entity(qid):
    try:
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&format=json&props=labels|descriptions|claims|sitelinks"
        req = urllib.request.Request(url, headers={"User-Agent": "ParlaMintALBot/1.0 (academic research; contact: ecane@parlamint.al)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
            ent = data.get("entities", {}).get(qid, {})
            if "redirects" in ent:
                target_id = ent["redirects"]["to"]
                target_info = check_single_entity(target_id)
                return {
                    "is_redirect": True,
                    "target_id": target_id,
                    "target_info": target_info
                }
            label_en = ent.get("labels", {}).get("en", {}).get("value")
            label_sq = ent.get("labels", {}).get("sq", {}).get("value")
            desc_en = ent.get("descriptions", {}).get("en", {}).get("value")
            desc_sq = ent.get("descriptions", {}).get("sq", {}).get("value")
            return {
                "id": qid,
                "label_en": label_en,
                "label_sq": label_sq,
                "desc_en": desc_en,
                "desc_sq": desc_sq,
                "sqwiki": ent.get("sitelinks", {}).get("sqwiki", {}).get("url"),
                "enwiki": ent.get("sitelinks", {}).get("enwiki", {}).get("url"),
            }
    except Exception as e:
        return {"error": str(e)}

def search_candidate(name):
    try:
        # Search sqwiki first
        sq_url = f"https://sq.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&titles={urllib.parse.quote(name)}&format=json"
        req = urllib.request.Request(sq_url, headers={"User-Agent": "ParlaMintALBot/1.0 (contact: ecane@parlamint.al)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                if pid != "-1" and "pageprops" in pdata and "wikibase_item" in pdata["pageprops"]:
                    qid = pdata["pageprops"]["wikibase_item"]
                    return qid, "sq.wikipedia", pdata.get("title")
    except:
        pass

    try:
        # Search enwiki
        en_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&titles={urllib.parse.quote(name)}&format=json"
        req = urllib.request.Request(en_url, headers={"User-Agent": "ParlaMintALBot/1.0 (contact: ecane@parlamint.al)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                if pid != "-1" and "pageprops" in pdata and "wikibase_item" in pdata["pageprops"]:
                    qid = pdata["pageprops"]["wikibase_item"]
                    return qid, "en.wikipedia", pdata.get("title")
    except:
        pass

    try:
        # Search Wikidata entities
        wd_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(name)}&language=sq&format=json&limit=5"
        req = urllib.request.Request(wd_url, headers={"User-Agent": "ParlaMintALBot/1.0 (contact: ecane@parlamint.al)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
            for item in data.get("search", []):
                desc = (item.get("description") or "").lower()
                label = (item.get("label") or "").lower()
                if any(w in desc for w in ["albania", "politician", "deputet", "minister", "jurist", "shqip", "lawyer", "party", "socialist", "democrat"]):
                    return item["id"], "wikidata.search", item.get("description")
                if label == name.lower():
                    return item["id"], "wikidata.exact_label", item.get("description")
    except:
        pass

    return None, None, None

def run_audit():
    print("=" * 60)
    print("1. AUDITING PROMPT SPECIFIC EXAMPLE (Q13045612)")
    print("=" * 60)
    q_data = check_single_entity("Q13045612")
    print(f"Given URL: https://www.wikidata.org/wiki/Q13045612")
    print(f"Wikidata API result for Q13045612:\n{json.dumps(q_data, indent=2)}")

    print("\nCorrect Wikidata Lookup for 'Erion Braçe':")
    eb_qid, eb_src, eb_desc = search_candidate("Erion Braçe")
    eb_info = check_single_entity(eb_qid) if eb_qid else {}
    print(f"Resolved QID: {eb_qid} via {eb_src}")
    print(f"Entity Details:\n{json.dumps(eb_info, indent=2)}")

    print("\n" + "=" * 60)
    print("2. AUDITING ALL ENTITIES IN metadata/persons.csv")
    print("=" * 60)
    persons_file = BASE_DIR / "metadata" / "persons.csv"
    with open(persons_file, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    audit_results = []
    for r in rows:
        pid = r["person_id"].strip()
        fn = r["forename"].strip()
        sn = r["surname"].strip()
        full_name = f"{fn} {sn}".strip()
        curr_wiki = r.get("wikidata_id", "").strip()

        if not full_name or pid == "AL_PERS_LEGJISLATURAXI":
            continue

        found_qid, src, note = search_candidate(full_name)
        time.sleep(0.15) # avoid 429
        entity_info = check_single_entity(found_qid) if found_qid else {}

        audit_results.append({
            "person_id": pid,
            "forename": fn,
            "surname": sn,
            "full_name": full_name,
            "current_wikidata_id": curr_wiki,
            "resolved_wikidata_id": found_qid,
            "resolved_source": src,
            "label_en": entity_info.get("label_en"),
            "label_sq": entity_info.get("label_sq"),
            "desc_en": entity_info.get("desc_en"),
            "desc_sq": entity_info.get("desc_sq"),
            "sqwiki": entity_info.get("sqwiki"),
            "enwiki": entity_info.get("enwiki"),
        })

    out_json = SCRATCH_DIR / "wikidata_audit_report.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)

    print(f"\nTotal persons processed: {len(audit_results)}")
    resolved_count = sum(1 for a in audit_results if a["resolved_wikidata_id"])
    print(f"Total resolved to verified Wikidata entities: {resolved_count} / {len(audit_results)}")

    print("\n--- SAMPLE OF RESOLVED PERSONS ---")
    for a in audit_results[:40]:
        if a["resolved_wikidata_id"]:
            print(f"{a['person_id']:<26} | {a['full_name']:<22} | {a['resolved_wikidata_id']:<10} | {a.get('desc_en') or a.get('desc_sq') or ''}")

if __name__ == "__main__":
    run_audit()
