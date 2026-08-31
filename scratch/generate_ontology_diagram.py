# -*- coding: utf-8 -*-
"""
Generate publication-quality, zero-overlap Ontology Schema Graph for ParlaMint-AL.
Renders classes, data attributes, object relations, cardinality, and taxonomies
with clean perimeter and gutter routing, crisp typography, and modern UI styling.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def create_ontology_diagram(output_paths: list[Path]):
    fig = plt.figure(figsize=(26, 17), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Dark aesthetic background
    fig.patch.set_facecolor("#0B1120") # Very dark slate / navy
    ax.set_facecolor("#0B1120")

    # Title & Subtitle Banner
    title_banner = patches.FancyBboxPatch((4.0, 93.0), 92.0, 5.4, boxstyle="round,pad=0.2,rounding_size=0.6",
                                         facecolor="#1E293B", edgecolor="#334155", linewidth=1.5, zorder=2)
    ax.add_patch(title_banner)

    ax.text(50, 96.4, "ParlaMint-AL: TEI / Semantic Ontology & Schema Architecture",
            fontsize=20, fontweight="bold", color="#F8FAFC", ha="center", va="center", family="sans-serif", zorder=3)
    ax.text(50, 94.3, "Formal Entity-Relationship Model, Data Properties, Object Relations & Controlled Taxonomies (ParlaMint 5.0 Strict XML)",
            fontsize=10.5, color="#94A3B8", ha="center", va="center", family="sans-serif", zorder=3)

    # Color Palette per Ontological Layer
    colors = {
        "corpus": {"bg": "#0F172A", "border": "#38BDF8", "header": "#0284C7", "accent": "#7DD3FC"},     # Sky Blue
        "session": {"bg": "#0F172A", "border": "#818CF8", "header": "#4F46E5", "accent": "#A5B4FC"},    # Indigo
        "discourse": {"bg": "#0F172A", "border": "#34D399", "header": "#059669", "accent": "#6EE7B7"},  # Emerald
        "entity": {"bg": "#0F172A", "border": "#F472B6", "header": "#BE185D", "accent": "#FBCFE8"},     # Pink / Rose
        "taxonomy": {"bg": "#0F172A", "border": "#FBBF24", "header": "#B45309", "accent": "#FDE68A"},   # Amber
        "linguistic": {"bg": "#0F172A", "border": "#C084FC", "header": "#7E22CE", "accent": "#E9D5FF"}, # Purple
    }

    # Card Drawer Helper
    def draw_class_card(x, y, w, h, title, layer_key, badge, attributes, relations):
        cfg = colors[layer_key]
        
        # Outer Card Shadow effect
        shadow = patches.FancyBboxPatch((x + 0.3, y - 0.3), w, h, boxstyle="round,pad=0.3,rounding_size=0.7",
                                        facecolor="#000000", edgecolor="none", alpha=0.35, zorder=2)
        ax.add_patch(shadow)

        # Main Card Box
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.7",
                                     linewidth=1.8, edgecolor=cfg["border"], facecolor=cfg["bg"], zorder=3)
        ax.add_patch(card)

        # Header Box
        header_h = 2.4
        header_patch = patches.FancyBboxPatch((x, y + h - header_h), w, header_h,
                                             boxstyle="round,pad=0.1,rounding_size=0.4",
                                             linewidth=0, facecolor=cfg["header"], zorder=4)
        ax.add_patch(header_patch)

        # Header Title
        ax.text(x + 1.2, y + h - header_h / 2, title,
                fontsize=10.5, fontweight="bold", color="#FFFFFF", ha="left", va="center", zorder=5)

        # Class Badge
        badge_w = 6.2
        badge_rect = patches.FancyBboxPatch((x + w - badge_w - 0.8, y + h - header_h + 0.5), badge_w, 1.4,
                                           boxstyle="round,pad=0.1,rounding_size=0.3",
                                           facecolor="#0F172A", edgecolor=cfg["accent"], linewidth=1.0, zorder=5)
        ax.add_patch(badge_rect)
        ax.text(x + w - badge_w / 2 - 0.8, y + h - header_h + 1.2, badge,
                fontsize=7.2, fontweight="bold", color=cfg["accent"], ha="center", va="center", zorder=6)

        # Section: Data Attributes
        curr_y = y + h - header_h - 1.1
        ax.text(x + 0.8, curr_y, "DATA ATTRIBUTES (Properties):", fontsize=7.2, fontweight="bold", color=cfg["accent"], zorder=5)
        curr_y -= 1.05
        for attr, dtype in attributes:
            if not attr: # blank line / sub-item
                ax.text(x + 2.2, curr_y, dtype, fontsize=6.3, color="#CBD5E1", zorder=5)
            else:
                ax.text(x + 1.2, curr_y, f"• {attr}", fontsize=6.7, color="#E2E8F0", zorder=5)
                if dtype:
                    ax.text(x + w - 1.0, curr_y, f"[{dtype}]", fontsize=6.2, color="#94A3B8", ha="right", zorder=5)
            curr_y -= 0.95

        # Section: Relations
        if relations:
            curr_y -= 0.3
            ax.text(x + 0.8, curr_y, "OBJECT RELATIONS (Edges):", fontsize=7.2, fontweight="bold", color=cfg["accent"], zorder=5)
            curr_y -= 1.05
            for rel, target, card_val in relations:
                ax.text(x + 1.2, curr_y, f"→ {rel}", fontsize=6.7, color="#F1F5F9", zorder=5)
                ax.text(x + w - 1.0, curr_y, f"({card_val}) {target}", fontsize=6.2, color=cfg["border"], ha="right", zorder=5)
                curr_y -= 0.95

    # =========================================================================
    # ROW 1 (TOP): CORPUS & SITTING SESSION (Y = 66.0 to 90.5)
    # =========================================================================

    # 1. teiCorpus (Top-Left)
    draw_class_card(
        x=4.5, y=66.0, w=26.5, h=24.5,
        title="teiCorpus",
        layer_key="corpus",
        badge="ROOT",
        attributes=[
            ("@xml:id", "xsd:ID = 'ParlaMint-AL'"),
            ("@xml:lang", "xsd:language = 'sq'"),
            ("edition", "xsd:string = '5.0'"),
            ("licence", "URI = CC BY 4.0"),
            ("publisher", "xsd:string = 'Kuvendi; CLARIN'"),
            ("handleURI", "URI = 'http://hdl.handle...'"),
            ("extentSpeeches", "xsd:nonNegativeInteger"),
            ("extentWords", "xsd:nonNegativeInteger"),
            ("releaseDate", "xsd:date = '2026-08-28'")
        ],
        relations=[
            ("xi:include", "TEI", "1..N"),
            ("particDesc", "listOrg", "1..1"),
            ("particDesc", "listPerson", "1..1"),
            ("classDecl", "Taxonomy", "1..5")
        ]
    )

    # 2. TEI Component (Top-Center)
    draw_class_card(
        x=36.5, y=66.0, w=27.0, h=24.5,
        title="TEI (Sitting Component)",
        layer_key="session",
        badge="COMPONENT",
        attributes=[
            ("@xml:id", "xsd:ID = 'ParlaMint-AL_YYYY-MM-DD'"),
            ("@xml:lang", "xsd:language = 'sq' | 'en'"),
            ("@ana", "TaxonomyRef = '#parla.sitting'"),
            ("titleMain[sq]", "xsd:string"),
            ("titleMain[en]", "xsd:string"),
            ("extentSpeeches", "xsd:nonNegativeInteger"),
            ("extentWords", "xsd:nonNegativeInteger"),
            ("sourceDesc/bibl", "URI (PDF Source URL)"),
            ("date[@when]", "xsd:date = YYYY-MM-DD"),
            ("tagUsage counts", "xsd:integer for u, seg, etc.")
        ],
        relations=[
            ("contains", "Meeting", "1..N"),
            ("contains", "Setting", "1..1"),
            ("contains", "DebateSection", "1..1")
        ]
    )

    # 3. Meeting & Setting Context (Top-Right)
    draw_class_card(
        x=69.0, y=66.0, w=26.5, h=24.5,
        title="Meeting & Setting",
        layer_key="session",
        badge="CONTEXT",
        attributes=[
            ("meeting/@n", "xsd:string = 'XI' (Term)"),
            ("meeting/@ana", "TaxonomyRef = '#parla.term'"),
            ("meeting/@corresp", "IDREF = '#AL_ORG_Kuvendi'"),
            ("meeting.label", "xsd:string = 'Legjislatura XI'"),
            ("meeting.session", "TaxonomyRef = '#parla.sitting'"),
            ("setting/address", "xsd:string = 'Kuvendi...'"),
            ("setting/city", "xsd:string = 'Tiranë'"),
            ("setting/country", "ISO-3166 = 'AL'"),
            ("setting/date", "xsd:date = YYYY-MM-DD")
        ],
        relations=[
            ("correspOrg", "Org (#AL_ORG_Kuvendi)", "1..1"),
            ("partOf", "TEI Component", "1..1")
        ]
    )

    # =========================================================================
    # ROW 2 (MIDDLE): DISCOURSE & TRANSCRIPTS (Y = 36.0 to 62.5)
    # =========================================================================

    # 4. Utterance (Middle-Left)
    draw_class_card(
        x=4.5, y=36.0, w=26.5, h=26.5,
        title="Utterance (<u> Speech Turn)",
        layer_key="discourse",
        badge="DISCOURSE",
        attributes=[
            ("@xml:id", "xsd:ID = '...u1', '...u2'"),
            ("@ana", "TaxonomyRef = '#chair' | '#regular'"),
            ("@who", "IDREF = '#AL_PERS_...' (optional)"),
            ("speech_index", "xsd:positiveInteger"),
            ("speaker_raw", "xsd:string (Raw transcript cue)"),
            ("role_status", "xsd:string ('#chair'/'#regular'/'#guest')"),
            ("is_resolved", "xsd:boolean (who omitted if false)")
        ],
        relations=[
            ("spokenBy (@who)", "Person", "0..1"),
            ("roleRef (@ana)", "Taxonomy[speaker_types]", "1..1"),
            ("contains", "Segment (<seg>)", "1..N"),
            ("containsEvent", "Vocal (<vocal>)", "0..N"),
            ("containsEvent", "Kinesic (<kinesic>)", "0..N"),
            ("containsNote", "Note (<note>)", "0..N")
        ]
    )

    # 5. DiscourseItem & Events (Middle-Center)
    draw_class_card(
        x=36.5, y=36.0, w=27.0, h=26.5,
        title="DiscourseItem (<seg>, <vocal>, etc.)",
        layer_key="discourse",
        badge="SEGMENTS",
        attributes=[
            ("<seg> @xml:id", "xsd:ID = '...seg1', '...seg2'"),
            ("<seg> text", "xsd:string (Transcript spoken text)"),
            ("<vocal> @type", "xsd:string = 'interruption'|'laughter'"),
            ("<vocal>/<desc>", "xsd:string = '(Ndërhyrje pa mikrofon)'"),
            ("<kinesic> @type", "xsd:string = 'applause'"),
            ("<kinesic>/<desc>", "xsd:string = '(Duartrokitje)'"),
            ("<note> @type", "xsd:string = 'comment'"),
            ("<note> text", "xsd:string = Parenthetical note")
        ],
        relations=[
            ("childOf", "Utterance (<u>)", "1..1"),
            ("annotatedAs", "LinguisticAnnotation", "1..1 (in .ana)")
        ]
    )

    # 6. LinguisticAnnotation (Middle-Right)
    draw_class_card(
        x=69.0, y=36.0, w=26.5, h=26.5,
        title="LinguisticAnnotation (TEI.ana)",
        layer_key="linguistic",
        badge="LINGUISTIC",
        attributes=[
            ("<s> @xml:id", "xsd:ID = Sentence Identifier"),
            ("<w> text", "xsd:string (Token surface)"),
            ("<w> @lemma", "xsd:string (Dictionary lemma)"),
            ("<w> @pos", "UD POS = 'NOUN'|'VERB'..."),
            ("<w> @msd", "UD Feats = 'Case=Nom|...'"),
            ("<w> @dep", "UD Rel = 'nsubj'|'root'..."),
            ("<w> @head", "xsd:integer (Head token)"),
            ("<pc> text", "xsd:string (Punctuation)")
        ],
        relations=[
            ("tokenizes", "Segment (<seg>)", "1..1"),
            ("producedBy", "Stanza / UDPipe NLP", "1..1")
        ]
    )

    # =========================================================================
    # ROW 3 (BOTTOM): ACTORS, ORGANISATIONS & TAXONOMIES (Y = 6.0 to 32.5)
    # =========================================================================

    # 7. Person Metadata (Bottom-Left)
    draw_class_card(
        x=4.5, y=6.0, w=26.5, h=26.5,
        title="Person (<person> in listPerson)",
        layer_key="entity",
        badge="AUTHORITY",
        attributes=[
            ("@xml:id", "xsd:ID = 'AL_PERS_{ForenameSurname}'"),
            ("persName/forename", "xsd:string = e.g. 'Niko'"),
            ("persName/surname", "xsd:string = e.g. 'Peleshi'"),
            ("sex/@value", "xsd:string = 'M' | 'F'"),
            ("birth/@when", "xsd:date = YYYY-MM-DD"),
            ("death/@when", "xsd:date = YYYY-MM-DD"),
            ("wikidata_id", "URI = 'https://www.wikidata...'"),
            ("education", "xsd:string"),
            ("occupation", "xsd:string")
        ],
        relations=[
            ("speaksIn", "Utterance (<u>)", "0..N"),
            ("hasAffiliation", "Affiliation", "0..N")
        ]
    )

    # 8. Org & Affiliation (Bottom-Center)
    draw_class_card(
        x=36.5, y=6.0, w=27.0, h=26.5,
        title="Org & Affiliation (listOrg)",
        layer_key="entity",
        badge="AUTHORITY",
        attributes=[
            ("org/@xml:id", "xsd:ID = 'AL_ORG_{ShortName}'"),
            ("org/@role", "Enum = parliament | politicalParty |"),
            ("", "       committee | parliamentaryGroup | govt"),
            ("orgName[@full='init']", "xsd:string = 'PS', 'PD', 'CLAP'"),
            ("orgName[@full='yes']", "xsd:string (Official Name sq)"),
            ("affiliation/@role", "Enum = member | chairperson | ..."),
            ("affiliation/@from", "xsd:date = YYYY-MM-DD"),
            ("affiliation/@to", "xsd:date = YYYY-MM-DD"),
            ("relation/@name", "xsd:string = 'subpart'")
        ],
        relations=[
            ("holdsAffiliation", "Person", "1..N"),
            ("subpartOf", "Parent Org (#AL_ORG_Kuvendi)", "0..1")
        ]
    )

    # 9. Taxonomies & Controlled Vocabularies (Bottom-Right)
    draw_class_card(
        x=69.0, y=6.0, w=26.5, h=26.5,
        title="Taxonomy & Controlled Vocabularies",
        layer_key="taxonomy",
        badge="CONTROLLED",
        attributes=[
            ("Taxonomy: speaker_types", "#chair, #regular, #guest"),
            ("Taxonomy: subcorpus", "#reference, #covid, #war"),
            ("Taxonomy: parla.legislature", "#parla.uni, #parla.national,"),
            ("", "#parla.term, #parla.sitting,"),
            ("", "#parla.committee, #parla.meeting..."),
            ("Taxonomy: politicalOrientation", "#left, #centre-left, #centre,"),
            ("", "#centre-right, #right"),
            ("Taxonomy: CHES", "#CHES.econ_left, #CHES.econ_right")
        ],
        relations=[
            ("classifiesUtterance", "Utterance.@ana", "1..1"),
            ("classifiesSession", "TEI.@ana", "1..1"),
            ("classifiesOrg", "Org.orientation", "0..1")
        ]
    )

    # =========================================================================
    # ARROW DRAWING HELPERS
    # =========================================================================
    def draw_direct_edge(x1, y1, x2, y2, label="", color="#38BDF8", style="->", rad=0.0, label_pos=0.5, label_offset=(0, 0.6)):
        ax.annotate(
            "",
            xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle=style,
                color=color,
                lw=2.0,
                mutation_scale=14,
                connectionstyle=f"arc3,rad={rad}",
            ),
            zorder=8
        )
        if label:
            mx = x1 + (x2 - x1) * label_pos + label_offset[0]
            my = y1 + (y2 - y1) * label_pos + label_offset[1]
            ax.text(mx, my, label, fontsize=7.2, fontweight="bold",
                    color=color, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", fc="#0B1120", ec=color, lw=1.0),
                    zorder=9)

    def draw_path_edge(points, label="", color="#38BDF8", label_idx=1, label_offset=(0, 0.6)):
        for i in range(len(points) - 1):
            is_last = (i == len(points) - 2)
            p1 = points[i]
            p2 = points[i+1]
            ax.annotate(
                "",
                xy=p2, xytext=p1,
                arrowprops=dict(
                    arrowstyle="->" if is_last else "-",
                    color=color,
                    lw=1.8,
                    mutation_scale=14 if is_last else 0,
                ),
                zorder=8
            )
        if label and len(points) >= 2:
            p_a = points[label_idx]
            p_b = points[label_idx + 1]
            mx = (p_a[0] + p_b[0]) / 2 + label_offset[0]
            my = (p_a[1] + p_b[1]) / 2 + label_offset[1]
            ax.text(mx, my, label, fontsize=7.2, fontweight="bold",
                    color=color, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", fc="#0B1120", ec=color, lw=1.0),
                    zorder=9)

    # -------------------------------------------------------------------------
    # ROW 1 (TOP) HORIZONTAL EDGES
    # -------------------------------------------------------------------------
    # teiCorpus -> TEI Component
    draw_direct_edge(31.0, 78.0, 36.5, 78.0, label="1..N xi:include", color="#38BDF8")

    # TEI Component -> Meeting & Setting
    draw_direct_edge(63.5, 78.0, 69.0, 78.0, label="1..N contains", color="#818CF8")

    # -------------------------------------------------------------------------
    # TIER 1 TO TIER 2 VERTICAL / GUTTER EDGES
    # -------------------------------------------------------------------------
    # TEI Component -> Utterance (through debateSection in gutter)
    draw_direct_edge(36.5, 72.0, 31.0, 58.0, label="body/div [1..N u]", color="#34D399", rad=0.08, label_pos=0.5)

    # -------------------------------------------------------------------------
    # ROW 2 (MIDDLE) HORIZONTAL EDGES
    # -------------------------------------------------------------------------
    # Utterance -> DiscourseItem
    draw_direct_edge(31.0, 49.0, 36.5, 49.0, label="1..N contains (<seg>, <vocal>)", color="#34D399")

    # DiscourseItem -> LinguisticAnnotation
    draw_direct_edge(63.5, 49.0, 69.0, 49.0, label="NLP Tokenization (<s>, <w>, <pc>)", color="#C084FC")

    # -------------------------------------------------------------------------
    # TIER 2 TO TIER 3 VERTICAL EDGES
    # -------------------------------------------------------------------------
    # Utterance -> Person (who resolves to)
    draw_direct_edge(17.5, 36.0, 17.5, 32.5, label="who @who (0..1)", color="#F472B6")

    # -------------------------------------------------------------------------
    # ROW 3 (BOTTOM) HORIZONTAL EDGES
    # -------------------------------------------------------------------------
    # Person -> Org & Affiliation (Horizontal)
    draw_direct_edge(31.0, 19.0, 36.5, 19.0, label="affiliation @ref (0..N)", color="#F472B6")

    # Org -> Taxonomy (Horizontal link)
    draw_direct_edge(63.5, 19.0, 69.0, 19.0, label="orientation Ref", color="#FBBF24")

    # -------------------------------------------------------------------------
    # PERIMETER ROUTED EDGES (Zero Overlap with Cards)
    # -------------------------------------------------------------------------
    # Meeting -> Org (Right Margin routing: Top-Right to Bottom-Center)
    draw_path_edge(
        points=[(95.5, 78.0), (98.0, 78.0), (98.0, 13.0), (63.5, 13.0)],
        label="@corresp (#AL_ORG_Kuvendi)",
        color="#818CF8",
        label_idx=1,
        label_offset=(-3.8, 0.0)
    )

    # Taxonomy -> Utterance @ana (Bottom & Left Margin routing)
    draw_path_edge(
        points=[(82.0, 6.0), (82.0, 3.2), (1.5, 3.2), (1.5, 46.0), (4.5, 46.0)],
        label="speaker_types classifies @ana",
        color="#FBBF24",
        label_idx=1,
        label_offset=(0.0, 0.6)
    )

    # teiCorpus -> listPerson / listOrg (Authority XIncludes along Left Margin)
    draw_path_edge(
        points=[(4.5, 78.0), (2.8, 78.0), (2.8, 20.0), (4.5, 20.0)],
        label="particDesc XIncludes",
        color="#38BDF8",
        label_idx=1,
        label_offset=(2.5, 0.0)
    )

    # =========================================================================
    # LEGEND / FOOTER BAR
    # =========================================================================
    footer = patches.FancyBboxPatch((4.0, 0.6), 92.0, 2.2, boxstyle="round,pad=0.2,rounding_size=0.4",
                                   linewidth=1.2, edgecolor="#334155", facecolor="#1E293B", zorder=3)
    ax.add_patch(footer)

    legend_items = [
        ("Corpus Hierarchy", colors["corpus"]["header"], "#38BDF8"),
        ("Sitting Session", colors["session"]["header"], "#818CF8"),
        ("Discourse / Transcripts", colors["discourse"]["header"], "#34D399"),
        ("Authority (Person/Org)", colors["entity"]["header"], "#F472B6"),
        ("Controlled Taxonomies", colors["taxonomy"]["header"], "#FBBF24"),
        ("Linguistic Layer (ana)", colors["linguistic"]["header"], "#C084FC")
    ]

    leg_x = 5.5
    for label, col, border_col in legend_items:
        rect = patches.Rectangle((leg_x, 1.05), 1.8, 1.0, facecolor=col, edgecolor=border_col, lw=1.2, zorder=4)
        ax.add_patch(rect)
        ax.text(leg_x + 2.4, 1.55, label, fontsize=7.8, fontweight="bold", color="#E2E8F0", va="center", zorder=4)
        leg_x += 15.2

    plt.tight_layout()

    # Save to all requested output paths
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, bbox_inches="tight", dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"Saved: {p}")

    plt.close(fig)

if __name__ == "__main__":
    out_dir = Path("./out")
    artifact_dir = Path("/Users/ecane/.gemini/antigravity-ide/brain/d297b920-bbfd-42cc-81b1-f180ac31c344")
    
    paths = [
        Path("./ontology_schema.png"),
        Path("./ontology_schema.jpg"),
        out_dir / "ParlaMint_AL_Ontology_Schema.png",
        out_dir / "ParlaMint_AL_Ontology_Schema.jpg",
        out_dir / "TEI" / "plain" / "ParlaMint_AL_Ontology_Schema.png",
        out_dir / "TEI" / "plain" / "ParlaMint_AL_Ontology_Schema.jpg",
        artifact_dir / "ParlaMint_AL_Ontology_Schema.png",
        artifact_dir / "ParlaMint_AL_Ontology_Schema.jpg",
    ]
    create_ontology_diagram(paths)
