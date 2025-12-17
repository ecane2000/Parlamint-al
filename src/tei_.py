
from pathlib import Path
import xml.etree.ElementTree as ET
from .utils import normalize_text

TEI_NS = "http://www.tei-c.org/ns/1.0"
def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"

ET.register_namespace("", TEI_NS)

def tei_root(title: str, when_iso: str, license_url: str):
    TEI = ET.Element(q("TEI"))
    teiHeader = ET.SubElement(TEI, q("teiHeader"))
    fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
    ET.SubElement(titleStmt, q("title"), {"type": "main"}).text = title or "Mbledhje"
    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
    availability = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
    ET.SubElement(availability, q("licence"), {"target": license_url}).text = license_url
    if when_iso:
        ET.SubElement(publicationStmt, q("date"), {"when": when_iso}).text = when_iso
    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
    ET.SubElement(sourceDesc, q("p")).text = "Burimi: Kuvendi i Shqipërisë."
    ET.SubElement(teiHeader, q("profileDesc"))
    return TEI

def write_plain_day(session, speakers_idx, out_path: Path, license_url: str = "https://creativecommons.org/licenses/by/4.0/"):
    title = f"Kuvendi i Shqipërisë, Procesverbal, {session.get('date','')}"
    if session.get("eventType"):
        one_line = " / ".join([ln.strip() for ln in session["eventType"].splitlines() if ln.strip()])
        title = f"Kuvendi i Shqipërisë — {one_line}, {session.get('date','')}"
    root = tei_root(title, session.get("date") or "", license_url)

    teiHeader = root.find(q("teiHeader"))
    fileDesc = teiHeader.find(q("fileDesc"))
    titleStmt = fileDesc.find(q("titleStmt"))
    meeting = ET.SubElement(titleStmt, q("meeting"), {"ana": "#parla.sitting"})
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
            chair_text = f"{chair_text} — {session['chair_role']}"
        ET.SubElement(meeting, q("chair")).text = chair_text

    profileDesc = teiHeader.find(q("profileDesc"))
    if session.get("topics"):
        list_el = ET.SubElement(profileDesc, q("list"), {"type": "agenda"})
        for it in session["topics"]:
            li = ET.SubElement(list_el, q("item"))
            if "n" in it:
                li.set("n", str(it["n"]))
            li.text = it.get("text") or ""
    for label, key in (("present", "participants_present"),
                       ("absent", "participants_absent"),
                       ("guests", "participants_guests")):
        val = session.get(key)
        if val:
            p = ET.SubElement(profileDesc, q("p"), {"type": f"participants:{label}"})
            p.text = val

    text = ET.SubElement(root, q("text"))
    body = ET.SubElement(text, q("body"))
    div = ET.SubElement(body, q("div"), {"type": "debateSection"})

    def _norm(s: str) -> str:
        try:
            return normalize_text(s, preserve_paragraphs=True)
        except TypeError:
            return normalize_text(s)

    for i, u in enumerate(session.get("utterances", []), 1):
        who_name = u.get("who_name") or "UNKNOWN"
        pid = None
        if isinstance(speakers_idx, dict):
            pid = speakers_idx.get((who_name or "").lower())
        who = f"#{pid}" if pid else "#pAL_UNKNOWN"
        u_el = ET.SubElement(div, q("u"), {"xml:id": f"spAL_{i:04d}", "who": who})
        utext = _norm(u.get("text",""))
        paras = [p for p in utext.split("\n\n") if p.strip()]
        if not paras:
            paras = [utext] if utext else []
        for para in paras:
            seg = ET.SubElement(u_el, q("seg"))
            seg.text = para

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
