from lxml import etree
from datetime import date
from .utils import normalize_whitespace

NS = {"tei": "http://www.tei-c.org/ns/1.0"}

def build_header(title, source_url, when_iso, parliament_name, city, license_url):
    TEI = etree.Element("{http://www.tei-c.org/ns/1.0}TEI")
    teiHeader = etree.SubElement(TEI, "{http://www.tei-c.org/ns/1.0}teiHeader")
    fileDesc = etree.SubElement(teiHeader, "{http://www.tei-c.org/ns/1.0}fileDesc")
    titleStmt = etree.SubElement(fileDesc, "{http://www.tei-c.org/ns/1.0}titleStmt")
    etree.SubElement(titleStmt, "{http://www.tei-c.org/ns/1.0}title").text = title
    respStmt = etree.SubElement(titleStmt, "{http://www.tei-c.org/ns/1.0}respStmt")
    etree.SubElement(respStmt, "{http://www.tei-c.org/ns/1.0}resp").text = "Konvertim/kurim TEI"
    etree.SubElement(respStmt, "{http://www.tei-c.org/ns/1.0}name").text = "Ekipi ParlaMint‑AL (pilot)"
    publicationStmt = etree.SubElement(fileDesc, "{http://www.tei-c.org/ns/1.0}publicationStmt")
    etree.SubElement(publicationStmt, "{http://www.tei-c.org/ns/1.0}publisher").text = "ParlaMint‑AL pilot"
    availability = etree.SubElement(publicationStmt, "{http://www.tei-c.org/ns/1.0}availability")
    etree.SubElement(availability, "{http://www.tei-c.org/ns/1.0}licence", target=license_url).text = "CC BY 4.0 (derivat TEI)"
    etree.SubElement(publicationStmt, "{http://www.tei-c.org/ns/1.0}date", when=date.today().isoformat())
    sourceDesc = etree.SubElement(fileDesc, "{http://www.tei-c.org/ns/1.0}sourceDesc")
    bibl = etree.SubElement(sourceDesc, "{http://www.tei-c.org/ns/1.0}bibl")
    etree.SubElement(bibl, "{http://www.tei-c.org/ns/1.0}title").text = "Procesverbal i seancës parlamentare"
    etree.SubElement(bibl, "{http://www.tei-c.org/ns/1.0}idno", type="url").text = source_url
    etree.SubElement(bibl, "{http://www.tei-c.org/ns/1.0}date", when=when_iso)
    etree.SubElement(bibl, "{http://www.tei-c.org/ns/1.0}note", type="provenance").text = "Burim: Kuvendi i Shqipërisë (PDF zyrtar)."

    encodingDesc = etree.SubElement(teiHeader, "{http://www.tei-c.org/ns/1.0}encodingDesc")
    classDecl = etree.SubElement(encodingDesc, "{http://www.tei-c.org/ns/1.0}classDecl")
    taxonomy = etree.SubElement(classDecl, "{http://www.tei-c.org/ns/1.0}taxonomy", **{"{http://www.w3.org/XML/1998/namespace}id": "taxo-speaker"})
    c1 = etree.SubElement(taxonomy, "{http://www.tei-c.org/ns/1.0}category", **{"{http://www.w3.org/XML/1998/namespace}id": "role-chair"})
    etree.SubElement(c1, "{http://www.tei-c.org/ns/1.0}catDesc").text = "Kryetar(ja) e seancës"
    c2 = etree.SubElement(taxonomy, "{http://www.tei-c.org/ns/1.0}category", **{"{http://www.w3.org/XML/1998/namespace}id": "role-mp"})
    etree.SubElement(c2, "{http://www.tei-c.org/ns/1.0}catDesc").text = "Deputet/e"
    c3 = etree.SubElement(taxonomy, "{http://www.tei-c.org/ns/1.0}category", **{"{http://www.w3.org/XML/1998/namespace}id": "role-guest"})
    etree.SubElement(c3, "{http://www.tei-c.org/ns/1.0}catDesc").text = "I/e ftuar"

    profileDesc = etree.SubElement(teiHeader, "{http://www.tei-c.org/ns/1.0}profileDesc")
    langUsage = etree.SubElement(profileDesc, "{http://www.tei-c.org/ns/1.0}langUsage")
    etree.SubElement(langUsage, "{http://www.tei-c.org/ns/1.0}language", ident="sq").text = "Shqip"
    settingDesc = etree.SubElement(profileDesc, "{http://www.tei-c.org/ns/1.0}settingDesc")
    setting = etree.SubElement(settingDesc, "{http://www.tei-c.org/ns/1.0}setting")
    etree.SubElement(setting, "{http://www.tei-c.org/ns/1.0}name", type="parliament").text = parliament_name
    etree.SubElement(setting, "{http://www.tei-c.org/ns/1.0}placeName").text = city
    etree.SubElement(setting, "{http://www.tei-c.org/ns/1.0}date", when=when_iso)

    revisionDesc = etree.SubElement(teiHeader, "{http://www.tei-c.org/ns/1.0}revisionDesc")
    etree.SubElement(revisionDesc, "{http://www.tei-c.org/ns/1.0}change", when=date.today().isoformat()).text = "Version pilot; tekst i pjesshëm për demonstrim."
    return TEI

def insert_body_plain(TEI_root, paragraphs, who="#per_AL_unknown", ana="#role-mp"):
    text = TEI_root.find(".//tei:text", namespaces=NS) or etree.SubElement(TEI_root, "{http://www.tei-c.org/ns/1.0}text")
    body = TEI_root.find(".//tei:body", namespaces=NS) or etree.SubElement(text, "{http://www.tei-c.org/ns/1.0}body")
    div = etree.SubElement(body, "{http://www.tei-c.org/ns/1.0}div", type="debate")
    for i, p in enumerate(paragraphs, start=1):
        u = etree.SubElement(div, "{http://www.tei-c.org/ns/1.0}u", who=who, ana=ana, **{"{http://www.w3.org/XML/1998/namespace}id": f"AL_demo.u{i}"})
        etree.SubElement(u, "{http://www.tei-c.org/ns/1.0}seg").text = normalize_whitespace(p)
    return TEI_root

def insert_body_ana(TEI_root, sentences):
    """
    sentences: 
      - List[List[dict]] from annotate.ud_doc (unified tokens) 
    """
    tei = "{http://www.tei-c.org/ns/1.0}"
    body = root.find(f".//{tei}body")
    if body is None:
        body = ET.SubElement(root, f"{tei}body")
    div = ET.SubElement(body, f"{tei}div", attrib={"type": "session"})
    
    text = TEI_root.find(".//tei:text", namespaces=NS) or etree.SubElement(TEI_root, "{http://www.tei-c.org/ns/1.0}text")
    body = TEI_root.find(".//tei:body", namespaces=NS) or etree.SubElement(text, "{http://www.tei-c.org/ns/1.0}body")
    div = TEI_root.find(".//tei:div[@type='debate']", namespaces=NS) or etree.SubElement(body, "{http://www.tei-c.org/ns/1.0}div", type="debate")
    u = etree.SubElement(div, "{http://www.tei-c.org/ns/1.0}u", who="#per_AL_unknown", ana="#role-mp", **{"{http://www.w3.org/XML/1998/namespace}id": "AL_demo.u_ana"})
    for si, sent in enumerate(stanza_sentences, start=1):
        s = etree.SubElement(u, "{http://www.tei-c.org/ns/1.0}s", **{"{http://www.w3.org/XML/1998/namespace}id": f"AL_demo.s{si}"})
        for ti, tok in enumerate(sent, start=1):
            if tok.get("text") in {",", ".", ";", ":"}:
                etree.SubElement(s, "{http://www.tei-c.org/ns/1.0}pc").text = tok["text"]
            else:
                w = etree.SubElement(s, "{http://www.tei-c.org/ns/1.0}w", **{"{http://www.w3.org/XML/1998/namespace}id": f"w{si}_{ti}"})
                w.text = tok.get("text")
                if tok.get("lemma"): w.set("lemma", tok["lemma"])
                ana_vals = []
                if tok.get("upos"): ana_vals.append(f"#upos-{tok['upos']}")
                if tok.get("deprel") == "root": ana_vals.append("#deprel-root")
                if ana_vals: w.set("ana", " ".join(ana_vals))
    return TEI_root

def serialize(TEI_root) -> str:
    return etree.tostring(TEI_root, encoding="utf-8", pretty_print=True, xml_declaration=True).decode("utf-8")
