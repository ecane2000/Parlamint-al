*** a/src/utils.py
--- b/src/utils.py
@@
+import re
+
+UNICODE_DASHES = r"[–—-]"
+SPACE_DASH_SPACE = re.compile(rf"\s*{UNICODE_DASHES}\s*")
+
+def squash_ws(s: str) -> str:
+    """Collapse internal whitespace to single spaces; keep newlines."""
+    return re.sub(r"[ \t]+", " ", s)
+
+def normalize_name(name: str) -> str:
+    """Lowercase, trim, collapse spaces for stable lookups."""
+    return re.sub(r"\s+", " ", (name or "").strip()).lower()
+
+def mint_person_id(full_name: str) -> str:
+    """
+    ParlaMint-style simple person id from name:
+    pAL_<Surname><Name> (ASCII-ish, but we keep UTF-8 to stay readable).
+    """
+    full_name = (full_name or "").strip()
+    parts = re.split(r"\s+", full_name)
+    if len(parts) >= 2:
+        surname = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[-1])
+        name = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[0])
+        base = f"{surname}{name}"
+    else:
+        base = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", full_name) or "UNKNOWN"
+    return f"pAL_{base}"
+
+def looks_like_committee(lines_between_kv_and_procesverbal: str) -> bool:
+    """Heuristic: if header mentions 'Komision' consider it committee context."""
+    return bool(re.search(r"\bKomision\w*", lines_between_kv_and_procesverbal or "", flags=re.I))

*** a/src/metadata.py
--- b/src/metadata.py
@@
-from dataclasses import dataclass
-from typing import Optional, Dict
+from dataclasses import dataclass
+from typing import Optional, Dict
+from .utils import normalize_name, mint_person_id
@@
 @dataclass
 class DocumentMetadata:
     date: str
     time: Optional[str]
     eventType: Optional[str]
+    eventTypeAna: Optional[str] = None
     chair_name: Optional[str] = None
     chair_role: Optional[str] = None
     topics: Optional[str] = None
     place: str = "Tiranë, AL"
     licence_url: str = "https://creativecommons.org/licenses/by/4.0/"
@@
     def speaker_id(self, full_name: str) -> str:
-        key = (full_name or "").strip().lower()
+        key = normalize_name(full_name)
         if key in self.speakers_idx:
             return self.speakers_idx[key]
-        pid = f"pAL_{key.replace(' ', '') or 'UNKNOWN'}"
+        pid = mint_person_id(full_name)
         self.speakers_idx[key] = pid
         return pid

*** a/src/pipeline.py
--- b/src/pipeline.py
@@
-from .segment import segment_by_speakers, parse_header
+from .segment import segment_by_speakers, parse_header
 from .tei import write_plain_day
 from .metadata import DocumentMetadata
-from .utils import squash_ws
+from .utils import squash_ws, looks_like_committee
@@
 def convert_inbox_to_tei(inbox: str, out_dir: str):
     """
     For every cleaned TXT in inbox, build a session dict (metadata + utterances) and write TEI day.
     """
@@
         header = session.get("header", {})
         # Build DocumentMetadata with richer fields
         eventType = header.get("eventType", "")
+        # Add simple @ana flags so TEI can annotate <meeting>/<div>:
+        eventTypeAna = "#parla.sitting"
+        if looks_like_committee(eventType):
+            eventTypeAna += " #parla.committee"
         md = DocumentMetadata(
             date=session.get("date", ""),
             time=session.get("time"),
             eventType=eventType,
+            eventTypeAna=eventTypeAna,
             chair_name=header.get("chair_name"),
             chair_role=header.get("chair_role"),
             topics=header.get("agenda_text"),
             place="Tiranë, AL",
             licence_url="https://creativecommons.org/licenses/by/4.0/",
         )
@@
-        # Ensure a title for TEI
-        if "title" not in session:
-            if eventType:
-                one_line = " / ".join([ln.strip() for ln in eventType.splitlines() if ln.strip()])
-                session["title"] = f"Kuvendi i Shqipërisë — {one_line}, {md.date}"
-            else:
-                session["title"] = f"Kuvendi i Shqipërisë, Procesverbal, {md.date}"
+        # Ensure a title for TEI (Hungarian-style richness)
+        if "title" not in session:
+            if eventType:
+                one_line = " / ".join([ln.strip() for ln in eventType.splitlines() if ln.strip()])
+                session["title"] = f"Kuvendi i Shqipërisë — {one_line}, {md.date}"
+            else:
+                session["title"] = f"Kuvendi i Shqipërisë, Procesverbal, {md.date}"
@@
-        write_plain_day(session, speakers_idx=name_to_pid, out_path=out_path, license_url=md.licence_url)
+        write_plain_day(
+            session,
+            speakers_idx=name_to_pid,
+            out_path=out_path,
+            license_url=md.licence_url,
+            eventTypeAna=md.eventTypeAna
+        )

*** a/src/tei.py
--- b/src/tei.py
@@
-from xml.etree import ElementTree as ET
+from xml.etree import ElementTree as ET
 from typing import Dict, List, Optional
 from .utils import squash_ws
@@
 NS = {"tei": "http://www.tei-c.org/ns/1.0"}
 def q(tag): return f"{{{NS['tei']}}}{tag}"
@@
-def tei_root(title: str, when_iso: str, license_url: str) -> ET.Element:
+def tei_root(title: str, when_iso: str, license_url: str) -> ET.Element:
     root = ET.Element(q("TEI"), {"xmlns:tei": NS["tei"]})
     teiHeader = ET.SubElement(root, q("teiHeader"))
     fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
     titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
     ET.SubElement(titleStmt, q("title"), {"type": "main"}).text = title
@@
-    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
-    ET.SubElement(publicationStmt, q("publisher")).text = "Kuvendi i Shqipërisë; CLARIN ERIC"
-    ET.SubElement(publicationStmt, q("pubPlace")).text = "Tiranë"
-    availability = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
-    ET.SubElement(availability, q("licence"), {"target": license_url}).text = "CC BY 4.0"
-    if when_iso:
-        ET.SubElement(publicationStmt, q("date"), {"when": when_iso}).text = when_iso
+    # --- publicationStmt ---
+    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
+    ET.SubElement(publicationStmt, q("publisher")).text = "Kuvendi i Shqipërisë; CLARIN ERIC"
+    ET.SubElement(publicationStmt, q("pubPlace")).text = "Tiranë"
+    availability = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
+    ET.SubElement(availability, q("licence"), {"target": license_url}).text = "CC BY 4.0"
+    if when_iso:
+        ET.SubElement(publicationStmt, q("date"), {"when": when_iso}).text = when_iso
@@
-    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
-    bibl = ET.SubElement(sourceDesc, q("bibl"))
-    ET.SubElement(bibl, q("title")).text = "Procesverbal i Kuvendit të Shqipërisë"
-    ET.SubElement(bibl, q("idno"), {"type": "URL"}).text = "https://www.kuvendi.gov.al/"
-    if when_iso:
-        ET.SubElement(bibl, q("date"), {"when": when_iso}).text = when_iso
+    # --- sourceDesc ---
+    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
+    bibl = ET.SubElement(sourceDesc, q("bibl"))
+    ET.SubElement(bibl, q("title")).text = "Procesverbal i Kuvendit të Shqipërisë"
+    ET.SubElement(bibl, q("idno"), {"type": "URL"}).text = "https://www.kuvendi.gov.al/"
+    if when_iso:
+        ET.SubElement(bibl, q("date"), {"when": when_iso}).text = when_iso
@@
-    # encodingDesc / projectDesc / classDecl are minimal in the current AL files; enrich to HU style
-    encodingDesc = ET.SubElement(teiHeader, q("encodingDesc"))
-    projectDesc = ET.SubElement(encodingDesc, q("projectDesc"))
-    ET.SubElement(projectDesc, q("p")).text = "ParlaMint-AL: korpus i krahasueshëm i seancave parlamentare, i përputhshëm me ParlaMint v5."
-    classDecl = ET.SubElement(encodingDesc, q("classDecl"))
-    tax = ET.SubElement(classDecl, q("taxonomy"), {"xml:id": "parla-taxonomy"})
-    # roles
-    cat_roles = ET.SubElement(tax, q("category"), {"xml:id": "parla.roles", "n": "Speaker roles"})
-    cd = ET.SubElement(cat_roles, q("catDesc")); cd.text = "Roli i folësit"
-    ET.SubElement(cat_roles, q("category"), {"xml:id": "parla.speaker"}).append(ET.Element(q("catDesc")))
-    ET.SubElement(cat_roles, q("category"), {"xml:id": "parla.chair"}).append(ET.Element(q("catDesc")))
-    # event types
-    cat_events = ET.SubElement(tax, q("category"), {"xml:id": "parla.events", "n": "Event types"})
-    ET.SubElement(cat_events, q("category"), {"xml:id": "parla.sitting"}).append(ET.Element(q("catDesc")))
-    ET.SubElement(cat_events, q("category"), {"xml:id": "parla.committee"}).append(ET.Element(q("catDesc")))
+    # --- encodingDesc (HU-like richness) ---
+    encodingDesc = ET.SubElement(teiHeader, q("encodingDesc"))
+    projectDesc = ET.SubElement(encodingDesc, q("projectDesc"))
+    ET.SubElement(projectDesc, q("p")).text = (
+        "ParlaMint-AL: korpus i krahasueshëm i seancave parlamentare, i përputhshëm me ParlaMint v5."
+    )
+    classDecl = ET.SubElement(encodingDesc, q("classDecl"))
+    tax = ET.SubElement(classDecl, q("taxonomy"), {"xml:id": "parla-taxonomy"})
+    # roles
+    cat_roles = ET.SubElement(tax, q("category"), {"xml:id": "parla.roles", "n": "Speaker roles"})
+    ET.SubElement(cat_roles, q("catDesc")).text = "Roli i folësit"
+    cd1 = ET.SubElement(cat_roles, q("category"), {"xml:id": "parla.speaker"})
+    ET.SubElement(cd1, q("catDesc")).text = "Folës"
+    cd2 = ET.SubElement(cat_roles, q("category"), {"xml:id": "parla.chair"})
+    ET.SubElement(cd2, q("catDesc")).text = "Kryetar/Moderues"
+    # event types
+    cat_events = ET.SubElement(tax, q("category"), {"xml:id": "parla.events", "n": "Event types"})
+    ce1 = ET.SubElement(cat_events, q("category"), {"xml:id": "parla.sitting"})
+    ET.SubElement(ce1, q("catDesc")).text = "Seancë/mbledhje"
+    ce2 = ET.SubElement(cat_events, q("category"), {"xml:id": "parla.committee"})
+    ET.SubElement(ce2, q("catDesc")).text = "Komision"
@@
-    profileDesc = ET.SubElement(teiHeader, q("profileDesc"))
-    settingDesc = ET.SubElement(profileDesc, q("settingDesc"))
-    setting = ET.SubElement(settingDesc, q("setting"))
-    ET.SubElement(setting, q("name")).text = "Kuvendi i Shqipërisë"
-    if when_iso:
-        ET.SubElement(setting, q("date"), {"when": when_iso}).text = when_iso
-    ET.SubElement(setting, q("placeName")).text = "Tiranë, AL"
+    # --- profileDesc / setting ---
+    profileDesc = ET.SubElement(teiHeader, q("profileDesc"))
+    settingDesc = ET.SubElement(profileDesc, q("settingDesc"))
+    setting = ET.SubElement(settingDesc, q("setting"))
+    ET.SubElement(setting, q("name")).text = "Kuvendi i Shqipërisë"
+    if when_iso:
+        ET.SubElement(setting, q("date"), {"when": when_iso}).text = when_iso
+    ET.SubElement(setting, q("placeName")).text = "Tiranë, AL"
+    ET.SubElement(profileDesc, q("p")).text = "Pjesëmarrësit referohen te listPerson/listOrg në nivel korpusi."
@@
-    revisionDesc = ET.SubElement(teiHeader, q("revisionDesc"))
-    ET.SubElement(revisionDesc, q("change"), {"when": when_iso or ""}).text = "Konvertimi fillestar në TEI (ParlaMint-AL)."
+    revisionDesc = ET.SubElement(teiHeader, q("revisionDesc"))
+    ET.SubElement(revisionDesc, q("change"), {"when": when_iso or ""}).text = "Konvertimi fillestar në TEI (ParlaMint-AL)."
@@
-def write_plain_day(session: dict, speakers_idx: Dict[str, str], out_path: str, license_url: str):
+def write_plain_day(session: dict, speakers_idx: Dict[str, str], out_path: str, license_url: str, eventTypeAna: Optional[str] = None):
     """
     Emit a ParlaMint-style plain day file for a single session.
     """
-    title = session.get("title") or f"Kuvendi i Shqipërisë, Procesverbal, {session.get('date','')}"
+    title = session.get("title") or f"Kuvendi i Shqipërisë, Procesverbal, {session.get('date','')}"
     root = tei_root(title, session.get("date",""), license_url)
-    text = ET.SubElement(root, q("text"))
+    text = ET.SubElement(root, q("text"), {"xml:lang": "sq"})
     body = ET.SubElement(text, q("body"))
-    div = ET.SubElement(body, q("div"), {"type": "debateSection"})
+    div_attrs = {"type": "debateSection"}
+    if eventTypeAna:
+        div_attrs["ana"] = eventTypeAna
+    div = ET.SubElement(body, q("div"), div_attrs)
@@
-    # enrich <titleStmt> with a <meeting> summary
+    # enrich <titleStmt> with a <meeting> summary (HU-like)
     teiHeader = root.find(q("teiHeader"))
     titleStmt = teiHeader.find(f".//{q('titleStmt')}")
     meeting = ET.SubElement(titleStmt, q("meeting"))
-    if session.get("eventType"):
-        for line in session["eventType"].splitlines():
-            if line.strip():
-                ET.SubElement(meeting, q("p")).text = line.strip()
+    if session.get("eventType"):
+        for line in session["eventType"].splitlines():
+            if line.strip():
+                ET.SubElement(meeting, q("p")).text = line.strip()
     if session.get("date"):
         ET.SubElement(meeting, q("date"), {"when": session["date"]}).text = session["date"]
     if session.get("time"):
         ET.SubElement(meeting, q("time")).text = session["time"]
     if session.get("chair_name"):
         chair_text = session["chair_name"]
         if session.get("chair_role"):
             chair_text += f" — {session['chair_role']}"
         ET.SubElement(meeting, q("chair")).text = chair_text
+    if eventTypeAna:
+        meeting.set("ana", eventTypeAna)
@@
-    for i, u in enumerate(session.get("utterances", []), 1):
+    for i, u in enumerate(session.get("utterances", []), 1):
         who_name = u.get("who_name") or "UNKNOWN"
         pid = speakers_idx.get((who_name or "").strip().lower())
         who = f"#{pid}" if pid else "#pAL_UNKNOWN"
-        u_el = ET.SubElement(div, q("u"), {"who": who})
+        u_el = ET.SubElement(
+            div, q("u"),
+            {
+                "xml:id": f"uAL_{session.get('date','0000-00-00').replace('-','')}_{i:04d}",
+                "who": who,
+                "ana": "#parla.speaker"
+            }
+        )
         for seg in u.get("paragraphs", []):
             seg_el = ET.SubElement(u_el, q("seg"))
             seg_el.text = seg
