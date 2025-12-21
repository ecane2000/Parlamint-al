# -*- coding: utf-8 -*-
from xml.etree import ElementTree as ET
from typing import Dict, Optional
from .utils import squash_ws

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
def q(tag): return f"{{{NS['tei']}}}{tag}"

def tei_root(title: str, when_iso: str, license_url: str) -> ET.Element:
    root = ET.Element(q("TEI"), {"xmlns:tei": NS["tei"]})
    teiHeader = ET.SubElement(root, q("teiHeader"))

    fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
    ET.SubElement(titleStmt, q("title"), {"type": "main"}).text = title

    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
    ET.SubElement(publicationStmt, q("publisher")).text = "Kuvendi i Shqipërisë; CLARIN ERIC"
    ET.SubElement(publicationStmt, q("pubPlace")).text = "Tiranë"
    avail = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
    ET.SubElement(avail, q("licence"), {"target": license_url}).text = "CC BY 4.0"
    if when_iso:
        ET.SubElement(publicationStmt, q("date"), {"when": when_iso}).text = when_iso

    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
    bibl = ET.SubElement(sourceDesc, q("bibl"))
    ET.SubElement(bibl, q("title")).text = "Procesverbal i Kuvendit të Shqipërisë"
    ET.SubElement(bibl, q("idno"), {"type": "URL"}).text = "https://www.kuvendi.gov.al/"
    if when_iso:
        ET.SubElement(bibl, q("date"), {"when": when_iso}).text = when_iso

    encodingDesc = ET.SubElement(teiHeader, q("encodingDesc"))
    projectDesc = ET.SubElement(encodingDesc, q("projectDesc"))
    ET.SubElement(projectDesc, q("p")).text = (
        "ParlaMint-AL: korpus i krahasueshëm i seancave parlamentare, i përputhshëm me ParlaMint v5."
    )
    classDecl = ET.SubElement(encodingDesc, q("classDecl"))
    tax = ET.SubElement(classDecl, q("taxonomy"), {"xml:id": "parla-taxonomy"})
    # roles
    cat_roles = ET.SubElement(tax, q("category"), {"xml:id": "parla.roles", "n": "Speaker roles"})
    cr1 = ET.SubElement(cat_roles, q("category"), {"xml:id": "parla.speaker"})
    ET.SubElement(cr1, q("catDesc")).text = "Folës"
    cr2 = ET.SubElement(cat_roles, q("category"), {"xml:id": "parla.chair"})
    ET.SubElement(cr2, q("catDesc")).text = "Kryetar/Moderues"
    # events
    cat_events = ET.SubElement(tax, q("category"), {"xml:id": "parla.events", "n": "Event types"})
    ce1 = ET.SubElement(cat_events, q("category"), {"xml:id": "parla.sitting"})
    ET.SubElement(ce1, q("catDesc")).text = "Seancë/mbledhje"
    ce2 = ET.SubElement(cat_events, q("category"), {"xml:id": "parla.committee"})
    ET.SubElement(ce2, q("catDesc")).text = "Komision"

    profileDesc = ET.SubElement(teiHeader, q("profileDesc"))
    settingDesc = ET.SubElement(profileDesc, q("settingDesc"))
    setting = ET.SubElement(settingDesc, q("setting"))
    ET.SubElement(setting, q("name")).text = "Kuvendi i Shqipërisë"
    if when_iso:
        ET.SubElement(setting, q("date"), {"when": when_iso}).text = when_iso
    ET.SubElement(setting, q("placeName")).text = "Tiranë, AL"
    ET.SubElement(profileDesc, q("p")).text = "Pjesëmarrësit referohen te listPerson/listOrg në nivel korpusi."

    revisionDesc = ET.SubElement(teiHeader, q("revisionDesc"))
    ET.SubElement(revisionDesc, q("change"), {"when": when_iso or ""}).text = "Konvertimi fillestar në TEI (ParlaMint-AL)."

    return root

def write_plain_day(
    session: dict,
    speakers_idx: Dict[str, str],
    out_path: str,
    license_url: str,
    eventTypeAna: Optional[str] = None,
):
    title = session.get("title") or f"Kuvendi i Shqipërisë, Procesverbal, {session.get('date','')}"
    root = tei_root(title, session.get("date",""), license_url)

    # Enrich <titleStmt> with <meeting>
    teiHeader = root.find(q("teiHeader"))
    titleStmt = teiHeader.find(f".//{q('titleStmt')}")
    meeting = ET.SubElement(titleStmt, q("meeting"))
    if session.get("eventType"):
        for line in session["eventType"].splitlines():
            if line.strip():
                ET.SubElement(meeting, q("p")).text = line.strip()
    if session.get("date"):
        ET.SubElement(meeting, q("date"), {"when": session["date"]}).text = session["date"]
    if session.get("time"):
        ET.SubElement(meeting, q("time")).text = session["time"]
    if session.get("chair_name"):
        chair_text = session["chair_name"]
        if session.get("chair_role"):
            chair_text += f" — {session['chair_role']}"
        ET.SubElement(meeting, q("chair")).text = chair_text
    if eventTypeAna:
        meeting.set("ana", eventTypeAna)

    text = ET.SubElement(root, q("text"), {"xml:lang": "sq"})
    div_attrs = {"type": "debateSection"}
    if eventTypeAna:
        div_attrs["ana"] = eventTypeAna
    body = ET.SubElement(text, q("body"))
    div = ET.SubElement(body, q("div"), div_attrs)

    for i, u in enumerate(session.get("utterances", []), 1):
        who_name = u.get("who_name") or "UNKNOWN"
        pid = speakers_idx.get((who_name or "").strip().lower())
        who = f"#{pid}" if pid else "#pAL_UNKNOWN"
        u_el = ET.SubElement(
            div, q("u"),
            {
                "xml:id": f"uAL_{session.get('date','0000-00-00').replace('-','')}_{i:04d}",
                "who": who,
                "ana": "#parla.speaker",
            }
        )
        for seg in u.get("paragraphs", []):
            seg_el = ET.SubElement(u_el, q("seg"))
            seg_el.text = squash_ws(seg)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
