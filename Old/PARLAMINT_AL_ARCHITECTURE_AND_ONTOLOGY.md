# ParlaMint-AL: Architecture, Semantic Ontology, and Corpus Engineering
## A Master-Level Technical Treatise on the Albanian Parliamentary TEI XML Corpus (ParlaMint 5.0)

---

### Abstract & Scope

This document provides a comprehensive technical and theoretical specification of the **ParlaMint-AL** corpus architecture, its underlying semantic ontology, processing pipeline engineering, and XML outputs. Designed for graduate students and researchers with a foundational knowledge of the **Text Encoding Initiative (TEI P5)** guidelines, **Universal Dependencies (UD)**, formal ontologies, and the European **CLARIN ERIC ParlaMint** framework, this treatise explores how unstructured parliamentary minutes (*procesverbale*) of the Parliament of Albania (*Kuvendi i Shqipërisë*) are acquired, normalized, disambiguated, semantically enriched, and encoded into strictly conforming **ParlaMint 5.0** TEI XML corpora.

---

## 1. Executive Summary & Scientific Motivation

### 1.1 Context: The CLARIN ParlaMint Initiative
ParlaMint is a major European infrastructure initiative supported by **CLARIN ERIC** (*Common Language Resources and Technology Infrastructure - European Research Infrastructure Consortium*). Its primary goal is the creation of multilingual, comparable, interoperable, and richly annotated corpora of parliamentary proceedings across European national and regional legislative assemblies. 

Comparative parliamentary discourse represents an invaluable empirical testbed for:
1. **Political Science & Governance Studies**: Measuring political polarization, legislative agenda-setting, party discipline, cabinet accountability, coalition dynamics, and gender representation.
2. **Computational Linguistics & Natural Language Processing (NLP)**: Training and evaluating language models, cross-lingual stance detection, named entity recognition (NER), semantic role labeling, and dependency parsing across morphologically diverse languages.
3. **Digital Humanities & Legal Informatics**: Historical tracking of statutory deliberations, public interest debates, and institutional democratization.

### 1.2 The Albanian Parliamentary Corpus (ParlaMint-AL)
Albanian (*shqip*) represents an independent, non-contiguous branch of the Indo-European language family. Integrating the legislative output of *Kuvendi i Shqipërisë* into the ParlaMint standard fills a crucial geographical and linguistic gap in South-Eastern European parliamentary language resources. 

However, unlike parliamentary institutions that publish native structured XML or rich Akoma Ntoso data feeds, the Albanian Parliament publishes its plenary and committee proceedings primarily as semi-structured or unstructured PDF documents (*procesverbale*). Consequently, **ParlaMint-AL** requires a robust, reproducible, and verifiable end-to-end extraction, normalization, speaker resolution, and TEI encoding pipeline.

### 1.3 Core Engineering & Methodological Objectives
The development of ParlaMint-AL is guided by four foundational pillars:
- **Strict Compliance with ParlaMint 5.0**: Adhering to the modular root/component XML architecture, strict validation constraints (Relax NG / Schematron), standardized TEI headers, and dual-language (`sq` / `en`) metadata.
- **Ontological Grounding**: Formalizing legislative agents, organizations, temporal affiliations, and chamber discourse into an explicit Entity-Relationship model connected to external semantic identifiers (e.g., Wikidata).
- **Linguistic Precision via Universal Dependencies**: Generating dual corpus representations—plain text TEI (`ParlaMint-AL.xml`) and linguistically annotated TEI (`ParlaMint-AL.ana.xml`) featuring tokenization, lemmatization, morphosyntactic descriptions (MSD / UPOS), and syntactic dependency trees.
- **FAIR Principles**: Ensuring that the corpus is *Findable, Accessible, Interoperable, and Reusable* under open access licensing (Creative Commons Attribution 4.0 International — CC BY 4.0).

---

## 2. Theoretical Foundations: ParlaMint 5.0, TEI P5, and Semantic Ontologies

```
+---------------------------------------------------------------------------------------------------+
|                                      CORPUS ARCHITECTURE LAYERS                                    |
+---------------------------------------------------------------------------------------------------+
|  1. Root Corpus Container    : ParlaMint-AL.xml (<teiCorpus> aggregating all sub-resources)        |
|  2. Session Component Files  : out/TEI/plain/ParlaMint-AL_YYYY-MM-DD.xml (<TEI> sitting files)    |
|  3. Authority Metadata Lists : ParlaMint-AL-listPerson.xml & ParlaMint-AL-listOrg.xml             |
|  4. Controlled Taxonomies    : ParlaMint-taxonomy-*.xml (speaker_types, roles, orientation, etc.)|
|  5. Linguistic Layer (.ana)  : out/TEI/ana/ParlaMint-AL_YYYY-MM-DD.ana.xml (Token/Lemma/UD Trees) |
+---------------------------------------------------------------------------------------------------+
```

### 2.1 The TEI P5 Parliamentary Profile
The Text Encoding Initiative (TEI P5) provides standard guidelines for digital text representation. For parliamentary corpora, TEI defines specialized elements to capture the dialogic and procedural reality of legislative chambers:
- `<teiCorpus>`: The top-level root element designed to encapsulate multiple distinct `<TEI>` documents while sharing common metadata, taxonomy definitions, and participant registries.
- `<teiHeader>`: Contains structured provenance, bibliographic descriptions (`fileDesc`), encoding declarations (`encodingDesc`), and contextual profiles (`profileDesc`).
- `<u>` (*utterance*): Represents a single, uninterrupted speech turn delivered by a single speaker.
- `<seg>` (*segment*): Represents a coherent paragraph or semantic unit within an utterance.
- Non-lexical chamber interventions: `<vocal>` (e.g., interruptions, laughter), `<kinesic>` (e.g., applause, gestures), and `<note>` (e.g., editorial descriptions, procedural notes).

### 2.2 ParlaMint 5.0 Modular Architecture
ParlaMint version 5.0 enforces a strict separation of concerns through W3C XML Inclusions (**XInclude** `http://www.w3.org/2001/XInclude`):
1. **The Master Corpus Root (`ParlaMint-AL.xml`)**: Does not store the transcript text directly. Instead, its `<teiHeader>` defines the overarching edition statement, total speech and word extents, funding bodies, shared taxonomic schemes in `<classDecl>`, and links to authority lists (`listPerson` and `listOrg`) in `<particDesc>`. It aggregates daily component files via `<xi:include href="plain/ParlaMint-AL_YYYY-MM-DD.xml"/>`.
2. **Component Session Files (`ParlaMint-AL_YYYY-MM-DD.xml`)**: Self-contained `<TEI>` documents containing sitting-level metadata (meeting type, legislative term, presiding officer, date) and the body of debates (`<text><body><div type="debateSection">`).
3. **Stand-Off Authority Registries**: Person metadata (`ParlaMint-AL-listPerson.xml`) and organization metadata (`ParlaMint-AL-listOrg.xml`) are separated from the transcripts, allowing rich, temporally scoped biographical and institutional data to be maintained independently.
4. **Controlled Taxonomies**: External XML files defining standardized controlled vocabularies for speaker classifications, legislative structures, political orientations, and subcorpus partitions.

### 2.3 Ontological Foundations in Digital Humanities
From an ontological standpoint, parliamentary proceedings are modeled as a multi-layered semantic graph comprising:
- **Actors (Agents)**: Members of Parliament (MPs), government ministers, committee chairs, invited experts, and citizens.
- **Organizations (Institutions)**: Unicameral parliament, standing committees, political parties, parliamentary groups, and government cabinets.
- **Temporal Roles & Affiliations (Relations)**: Time-bound memberships, leadership positions, and ministerial appointments.
- **Discourse Events (Events)**: Sittings, legislative terms, debates, speech turns, and paralinguistic events.
- **Concepts & Classifications (Taxonomies)**: Controlled vocabularies providing standardized semantic anchors across national boundaries.

---

## 3. Complete Ontological Architecture & Entity-Relationship Model

The semantic ontology of ParlaMint-AL is formalized below, matching the structural relations and data properties specified in the formal schema architecture.

```
+-----------------------------------------------------------------------------------------------------------------------------+
|                                    PARLAMINT-AL ONTOLOGICAL ENTITY-RELATIONSHIP MODEL                                      |
+-----------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                             |
|   +--------------------------+  xi:include  +--------------------------------+  xi:include  +----------------------------+  |
|   |        teiCorpus         |------------->|    TEI (Sitting Component)     |------------->|  Taxonomy & Controlled Voc  |  |
|   |         [ROOT]           |              |          [COMPONENT]           |              |        [CONTROLLED]        |  |
|   +--------------------------+              +--------------------------------+              +----------------------------+  |
|         |            |                               |               |                                     ^                |
|         | xi:include | xi:include                    | 1..N contains | composed of [1..N]                  | classifies     |
|         v            v                               v               v                                     |                |
|   +------------+ +------------+             +-----------------+ +-----------------------+                  |                |
|   | listPerson | |  listOrg   |             | Meeting/Setting | | Utterance (<u/> turn) |------------------+                |
|   | [AUTHORITY]| | [AUTHORITY]|             |    [CONTEXT]    | |      [DISCOURSE]      |                                   |
|   +------------+ +------------+             +-----------------+ +-----------------------+                                   |
|         ^            ^                               | who points [0..1]     |                                              |
|         |            |                               v                       | 1..N contains                                |
|         |            |                      +-----------------+              v                                              |
|         |            +----------------------| Person (<person>) |       +----------------------+                             |
|         |              affiliation [0..N]   +-----------------+       |    DiscourseItem     |                             |
|         |                                                             | (<seg>, <vocal>, etc)|                             |
|         |                                                             +----------------------+                             |
|         |                                                                        |                                          |
|         |                                                                        | 1..1 NLP Tokenized                       |
|         |                                                                        v                                          |
|         |                                                             +----------------------+                             |
|         +-------------------------------------------------------------| LinguisticAnnotation |                             |
|                                 references speaker ID                 |      (TEI.ana)       |                             |
|                                                                       +----------------------+                             |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

### 3.1 Entity 1: `teiCorpus` [Root Architecture]
The `teiCorpus` serves as the global root object aggregating the entire corpus.

- **Data Attributes & Properties**:
  - `@xml:id`: Unique identifier for the corpus (`"ParlaMint-AL"` or `"ParlaMint-AL.ana"`).
  - `@xml:lang`: Primary language identifier (`"sq"`).
  - `edition`: ParlaMint version release (`"5.0"`).
  - `publisher`: Responsible legal entity (`"Kuvendi i Shqipërisë; CLARIN ERIC"`).
  - `idno[@type='URI'][@subtype='handle']`: Persistent identifier (PID) resolving to the official repository handle.
  - `licence`: CC BY 4.0 International license URI (`"https://creativecommons.org/licenses/by/4.0/"`).
  - `extent`: Cumulative quantitative metrics capturing total speeches and total word counts in Albanian and English.
- **Object Relations (Edges)**:
  - `xi:include` $\rightarrow$ `TEI (Sitting Component)`: References all daily XML components (`href="plain/ParlaMint-AL_YYYY-MM-DD.xml"`).
  - `xi:include` $\rightarrow$ `listPerson` & `listOrg`: Embeds authority files in `<profileDesc>/<particDesc>`.
  - `xi:include` $\rightarrow$ `Taxonomies`: Embeds shared classification schemes in `<encodingDesc>/<classDecl>`.

```xml
<!-- Root teiCorpus Header Snippet -->
<teiCorpus xmlns="http://www.tei-c.org/ns/1.0" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="ParlaMint-AL" xml:lang="sq">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main" xml:lang="sq">Korpusi parlamentar shqiptar ParlaMint-AL</title>
        <title type="main" xml:lang="en">Albanian parliamentary corpus ParlaMint-AL</title>
        <funder><orgName xml:lang="sq">CLARIN ERIC</orgName></funder>
      </titleStmt>
      <editionStmt><edition>5.0</edition></editionStmt>
      <extent>
        <measure unit="speeches" quantity="1420" xml:lang="sq">1420 fjalime</measure>
        <measure unit="words" quantity="385200" xml:lang="sq">385200 fjalë</measure>
      </extent>
      <publicationStmt>
        <publisher>Kuvendi i Shqipërisë; CLARIN ERIC</publisher>
        <idno type="URI" subtype="handle">http://hdl.handle.net/11356/ParlaMint-AL</idno>
        <availability status="free"><licence>https://creativecommons.org/licenses/by/4.0/</licence></availability>
        <date when="2026-03-01">2026-03-01</date>
      </publicationStmt>
      <sourceDesc>
        <bibl>
          <title type="main" xml:lang="sq">Procesverbalet e Kuvendit të Shqipërisë</title>
          <idno type="URI">https://www.kuvendi.gov.al/</idno>
        </bibl>
      </sourceDesc>
    </fileDesc>
    <encodingDesc>
      <classDecl>
        <xi:include href="ParlaMint-taxonomy-speaker_types.xml"/>
        <xi:include href="ParlaMint-taxonomy-parla.roles.xml"/>
        <xi:include href="ParlaMint-taxonomy-subcorpus.xml"/>
        <xi:include href="ParlaMint-taxonomy-parla.legislature.xml"/>
        <xi:include href="ParlaMint-taxonomy-politicalOrientation.xml"/>
        <xi:include href="ParlaMint-taxonomy-CHES.xml"/>
      </classDecl>
    </encodingDesc>
    <profileDesc>
      <particDesc>
        <xi:include href="ParlaMint-AL-listOrg.xml"/>
        <xi:include href="ParlaMint-AL-listPerson.xml"/>
      </particDesc>
    </profileDesc>
  </teiHeader>
  <xi:include href="plain/ParlaMint-AL_2025-10-17.xml"/>
</teiCorpus>
```

---

### 3.2 Entity 2: `TEI (Sitting Component)` [Component Architecture]
The individual `<TEI>` component encapsulates a single sitting or meeting transcript.

- **Data Attributes & Properties**:
  - `@xml:id`: Standardized document identifier (`"ParlaMint-AL_YYYY-MM-DD"`).
  - `@xml:lang`: Component language (`"sq"`).
  - `@ana`: Subcorpus classification (`"#parla.sitting #reference"` or `"#parla.committee.standing #reference"`).
  - `tagsDecl`: Complete audit of all element tag occurrences within the component (`tagUsage`).
- **Object Relations**:
  - Sub-tree contains `<teiHeader>` and `<text><body><div type="debateSection">`.
  - Aggregates 1 or more `<meeting>` and `<setting>` elements.
  - Composed of 1 to $N$ speech turns (`<u>`).

---

### 3.3 Entity 3: `Meeting & Setting` [Contextual Metadata]
Located within `<titleStmt>` and `<settingDesc>`, these elements model institutional context.

- **Data Attributes & Properties**:
  - `<meeting @n>`: Identifies the legislative term (e.g., `n="XI"`).
  - `<meeting @ana>`: Taxonomy pointers to legislative terms and meeting types (e.g., `ana="#parla.uni #parla.term #KUV.XI"` and `ana="#parla.sitting #reference"`).
  - `<meeting @corresp>`: Links directly to the parliament organization ID (`corresp="#AL_ORG_Kuvendi"`).
  - `<setting>`: Defines spatial attributes (`<name type="city">Tiranë</name>`, `<name type="country" key="AL">Albania</name>`).
  - `<date @when>`: ISO-8601 session date (`YYYY-MM-DD`).

---

### 3.4 Entity 4: `Utterance (<u/> Speech Turn)` [Discourse Representation]
The fundamental discourse atom representing an uninterrupted speech turn.

- **Data Attributes & Properties**:
  - `@xml:id`: Unique utterance identifier (`"{doc_id}.u{index}"`, e.g., `"ParlaMint-AL_2025-11-13.u0001"`).
  - `@who`: Pointer to the canonical person authority (`"#AL_PERS_NikollaLindita"`). *Crucial rule in ParlaMint 5.0*: If a speaker cannot be resolved or is genuinely anonymous, `@who` is omitted rather than populated with placeholder values.
  - `@ana`: Pointer to the speaker type taxonomy category (`"#chair"`, `"#regular"`, or `"#guest"`).
- **Object Relations**:
  - `@who` $\rightarrow$ `Person` in `ParlaMint-AL-listPerson.xml`.
  - `@ana` $\rightarrow$ Category in `ParlaMint-taxonomy-speaker_types.xml`.
  - Contains an ordered sequence of 1 to $N$ `DiscourseItem` elements (`<seg>`, `<vocal>`, `<kinesic>`, `<note>`).

---

### 3.5 Entity 5: `DiscourseItem` [Discourse Segmentation & Non-Lexical Events]
Parliamentary transcripts capture both spoken language and non-lexical chamber actions:

- **Data Types**:
  1. `<seg @xml:id>`: Standard speech paragraph (`"{doc_id}.seg{global_index}"`). Contains the spoken text.
  2. `<vocal @type>`: Non-lexical vocal sounds (`type="interruption"`, `type="laughter"`). Encapsulates `<desc>`.
  3. `<kinesic @type>`: Physical actions (`type="applause"`). Encapsulates `<desc>`.
  4. `<note @type>`: Editorial and procedural annotations (`type="comment"`).

```xml
<!-- Discourse Representation in Component File -->
<u xml:id="ParlaMint-AL_2025-10-23.u0002" who="#AL_PERS_BozdoEnno" ana="#regular">
  <seg xml:id="ParlaMint-AL_2025-10-23.seg3">Zonja kryetare, e lexova me vëmendje rezolutën...</seg>
  <vocal type="interruption"><desc>Ndërhyrje pa mikrofon nga salla.</desc></vocal>
  <seg xml:id="ParlaMint-AL_2025-10-23.seg4">Doni ta kaloni kështu siç është, apo ia vlen ta diskutojmë në një seancë më vete?</seg>
  <kinesic type="applause"><desc>Duartrokitje nga deputetët e opozitës.</desc></kinesic>
</u>
```

---

### 3.6 Entity 6: `LinguisticAnnotation` [TEI.ana Universal Dependencies Layer]
In `.ana.xml` files, plain text within `<seg>` is replaced by tokenized, morphosyntactically tagged, and syntactically parsed Universal Dependencies (UD v2) structures.

- **Data Properties & XML Structure**:
  - `<s>`: Sentence boundary container (`xml:id="{seg_id}.s{sentence_index}"`).
  - `<w>`: Word token element.
    - `@lemma`: Dictionary base form.
    - `@pos`: Universal POS tag (`NOUN`, `VERB`, `ADJ`, `PRON`, `ADV`, `ADP`, etc.).
    - `@msd`: Morphosyntactic description feature bundle formatted according to Universal Features (e.g., `"Case=Nom|Gender=Fem|Number=Sing"`).
    - `@dep`: Universal Dependency syntactic relation (e.g., `"root"`, `"nsubj"`, `"obj"`, `"obl"`, `"punct"`).
    - `@head`: Identifier of the governing token (`head="2"` or target pointer).
  - `<pc>`: Punctuation mark token element (`pos="PUNCT"`).

```xml
<!-- Linguistically Annotated Sentence Snippet (<seg> -> <s> -> <w>/<pc>) -->
<seg xml:id="ParlaMint-AL_2025-11-13.seg1">
  <s xml:id="ParlaMint-AL_2025-11-13.seg1.s1">
    <w xml:id="ParlaMint-AL_2025-11-13.w1" lemma="filloj" pos="VERB" msd="Mood=Ind|Number=Plur|Person=1|Tense=Pres|VerbForm=Fin" dep="root" head="0">Fillojmë</w>
    <w xml:id="ParlaMint-AL_2025-11-13.w2" lemma="mbledhje" pos="NOUN" msd="Case=Acc|Definite=Def|Gender=Fem|Number=Sing" dep="obj" head="1">mbledhjen</w>
    <w xml:id="ParlaMint-AL_2025-11-13.w3" lemma="e" pos="DET" msd="Gender=Fem|Number=Sing" dep="det" head="4">e</w>
    <w xml:id="ParlaMint-AL_2025-11-13.w4" lemma="komision" pos="NOUN" msd="Case=Gen|Definite=Def|Gender=Masc|Number=Sing" dep="nmod" head="2">Komisionit</w>
    <pc xml:id="ParlaMint-AL_2025-11-13.pc1" pos="PUNCT" dep="punct" head="1">.</pc>
  </s>
</seg>
```

---

### 3.7 Entity 7: `Person` (`listPerson`) [Biographical Authority]
Stores biographical metadata in `ParlaMint-AL-listPerson.xml`.

- **Data Attributes & Properties**:
  - `@xml:id`: Canonical person identifier (`"AL_PERS_{Surname}{Forename}"`, e.g., `"AL_PERS_BraçeErion"`).
  - `<persName>`: Structured name parts (`<forename>`, `<surname>`).
  - `<sex @value>`: Gender marker (`"M"` or `"F"`).
  - `<birth @when>` / `<death @when>`: ISO date markers.
  - `<idno @type='URI' @subtype='wikidata'>`: Direct URI linkage to Wikidata (e.g., `https://www.wikidata.org/wiki/Q13038669`).
  - `<affiliation>`: Temporal organizational affiliations.

```xml
<!-- Stand-Off Authority: Person with Affiliations -->
<person xml:id="AL_PERS_BraçeErion">
  <persName xml:lang="sq">
    <forename>Erion</forename>
    <surname>Braçe</surname>
  </persName>
  <sex value="M"/>
  <birth when="1972-04-02"/>
  <affiliation ref="#AL_ORG_PS" role="member" from="2021-09-10" to="2025-09-09">
    <roleName xml:lang="sq">Deputet i Grupit Parlamentar të Partisë Socialiste</roleName>
    <roleName xml:lang="en">MP of the Socialist Party Parliamentary Group</roleName>
  </affiliation>
  <affiliation ref="#AL_ORG_KomisioniEkonomia" role="head" from="2021-09-15" to="2025-09-09">
    <roleName xml:lang="sq">Kryetar i Komisionit për Ekonominë dhe Financat</roleName>
    <roleName xml:lang="en">Chair of the Standing Committee on Economy and Finance</roleName>
  </affiliation>
  <idno type="URI" subtype="wikidata">https://www.wikidata.org/wiki/Q13038669</idno>
</person>
```

---

### 3.8 Entity 8: `Org & Affiliation` (`listOrg`) [Institutional Hierarchy]
Models political and parliamentary entities in `ParlaMint-AL-listOrg.xml`.

- **Data Attributes & Properties**:
  - `@xml:id`: Organization identifier (`"AL_ORG_{ShortName}"`, e.g., `"AL_ORG_Kuvendi"`, `"AL_ORG_PS"`, `"AL_ORG_PD"`, `"AL_ORG_KomisioniLigjet"`).
  - `@role`: Controlled organization type (`"parliament"`, `"politicalParty"`, `"parliamentaryGroup"`, `"committee"`, `"government"`).
  - `<orgName @full='init'>`: Acronym or short name.
  - `<orgName @full='yes' xml:lang='sq'>`: Official full name.
  - `<listRelation>`: Expresses hierarchical structure (e.g., `<relation name="subpart" active="#AL_ORG_KomisioniLigjet" passive="#AL_ORG_Kuvendi"/>`).

---

### 3.9 Entity 9: `Taxonomy & Controlled Vocabularies` [Semantic Grounding]
All categorical codes in ParlaMint-AL link directly to dual-language TEI taxonomy files:

| Taxonomy File | XML ID | Target Elements / Attributes | Categories Defined |
|:---|:---|:---|:---|
| `ParlaMint-taxonomy-speaker_types.xml` | `speaker_types` | `u/@ana` | `#chair`, `#regular`, `#guest` |
| `ParlaMint-taxonomy-parla.roles.xml` | `parla.roles` | `affiliation/@role` | `#head`, `#deputyHead`, `#member`, `#minister`, `#guest` |
| `ParlaMint-taxonomy-subcorpus.xml` | `subcorpus` | `TEI/@ana`, `text/@ana` | `#reference`, `#covid`, `#war` |
| `ParlaMint-taxonomy-parla.legislature.xml` | `parla.legislature` | `meeting/@ana` | `#parla.uni`, `#parla.national`, `#parla.term`, `#parla.sitting`, `#parla.committee` |
| `ParlaMint-taxonomy-politicalOrientation.xml` | `politicalOrientation` | `org/state/@ana` | `#left`, `#centre-left`, `#centre`, `#centre-right`, `#right` |
| `ParlaMint-taxonomy-CHES.xml` | `CHES` | `org/state/@ana` | `#CHES.econ_left`, `#CHES.econ_right` (Chapel Hill Expert Survey) |

---

## 4. Pipeline Engineering & Processing Workflows

The software architecture of the ParlaMint-AL processing stack is implemented in modular Python scripts located in `src/`. It implements a pipeline transforming raw web artifacts into validated TEI XML.

```
+---------------------------------------------------------------------------------------------------------------+
|                                       END-TO-END PROCESSING PIPELINE                                          |
+---------------------------------------------------------------------------------------------------------------+
|                                                                                                               |
|  [Step 1: Web Scraping]  ==>  [Step 2: Text Extraction]  ==>  [Step 3: Text Normalization & Cleaning]        |
|  crawl_pdfs_selenium.py       crawl.py (pdfminer.six)         extract.py (Regex OCR Repairs)                  |
|  (parlament.al -> PDFs)       (PDFs -> raw_txt/)              (raw_txt/ -> texts/)                            |
|                                                                        |                                      |
|                                                                        v                                      |
|  [Step 6: TEI Component Generation] <== [Step 5: Speaker Resolution] <== [Step 4: Segmentation]               |
|  tei.py                                 resolve_speakers.py            segment.py                             |
|  (XML DOM Serialization)                (Entity Disambiguation)        (Speech Turns & Chamber Events)        |
|            |                                                                                                  |
|            v                                                                                                  |
|  [Step 7: Master Corpus Root]  ==>  [Step 8: Linguistic Annotation Layer]                                     |
|  build_root.py                      annotate_stanza.py / annotate_udpipe.py                                   |
|  (ParlaMint-AL.xml Aggregation)     (UD Token/Lemma/UPOS/Feats/Deprel -> .ana.xml)                            |
|                                                                                                               |
+---------------------------------------------------------------------------------------------------------------+
```

---

### 4.1 Step 1: Web Crawling & Ingestion (`crawl_pdfs_selenium.py`)
- **Challenge**: The Albanian parliamentary portal renders document records dynamically via JavaScript cards (`.act-card-wrapper`), with PDF downloads triggered via client-side events.
- **Solution**: A headless Playwright / Selenium browser instance navigates `https://www.parlament.al/procesverbale`, handles pagination, intercepts downstream download triggers, validates Azure Blob Storage endpoints (`kuvendiwebfiles.blob.core.windows.net`), and writes an index of verified URLs to `pdf_urls.json`.

---

### 4.2 Step 2: Stream Extraction (`crawl.py`)
- **Process**: Using `requests` with chunked streaming ($1\text{ MB}$ buffers), PDFs are downloaded to `pdfs/`. Text extraction is executed via `pdfminer.six` using structural layout analysis parameters:
  $$\text{LAParams}(\text{line\_margin}=0.5, \text{word\_margin}=0.1, \text{boxes\_flow}=0.5)$$
- **Output**: Raw, uncorrected text files stored in `raw_txt/`.

---

### 4.3 Step 3: Orthographic Normalization & OCR Repair (`extract.py`)
Raw text extracted from government PDFs frequently suffers from systematic typographical and OCR artifacting:
1. **Diacritical & Glyph Normalization**:
   - $\text{" é"}, \text{"É"} \rightarrow \text{" ë"}, \text{"Ë"}$ (Correcting acute accents substituted for Albanian trema).
   - $\text{"¢"} \rightarrow \text{"ç"}$ (Cent symbol misrecognition for cedilla $ç$).
   - $\text{"\bgë"} \rightarrow \text{"që"}$ and $\text{"\bgy"} \rightarrow \text{"gj"}$ (Common ligated OCR confusion).
2. **Structural Cleaning**:
   - Elimination of page header banners (`PAGE_HDR_RE = r"===== Page \d+ ====="`).
   - Removal of isolated page numbers and document tracking hashes.
   - Normalization of line endings ($\text{CRLF} \rightarrow \text{LF}$) and multiple spaces.
3. **Line Reconstruction (`reconstruct_broken_lines`)**:
   - Merges wrapped lines that do not terminate in valid sentence-ending punctuation (`.`, `!`, `?`, `:`, `"`), healing broken clauses split across PDF column boundaries.
4. **Header Block Parsing (`extract_header_block`)**:
   - Isolates the metadata prologue between `"KUVENDI"` and `"HAPET MBLEDHJA"` (or `"PROCESVERBAL"`).
   - Extracts sitting date, time, presiding officer (*"Drejton mbledhjen:"*), and the formal agenda (*"Rendi i ditës:"*).

---

### 4.4 Step 4: Speaker Segmentation & Discourse Parsing (`segment.py`)
The normalized text is segmented into discrete `SittingBlock`, `SpeechBlock`, and `DiscourseItem` data structures:

1. **Speaker Cue Recognition (`SPEAKER_CUE_RE`)**:
   Recognizes speaker cues using the regular expression:
   ```python
   SPEAKER_CUE_RE = re.compile(
       r"^\s*(?:\d+\s+)?(?P<label>(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?"
       r"[A-ZÇË][\wÀ-ÖØ-öø-ÿÇËçë’'\.\-]*\s+[A-ZÇË][\wÀ-ÖØ-öø-ÿÇËçë’'\.\-]*)\s*[–—-]\s*(?P<rest>.*)$",
       flags=re.UNICODE | re.DOTALL
   )
   ```
2. **Discourse Item Classification (`parse_discourse_text`)**:
   Identifies parenthetical non-speech chamber events and categorizes them:
   - Interruptions: `"(Ndërhyrje pa mikrofon...)"` $\rightarrow$ `<vocal type="interruption">`
   - Applause: `"(Duartrokitje...)"` $\rightarrow$ `<kinesic type="applause">`
   - Laughter: `"(Të qeshura...)"` $\rightarrow$ `<vocal type="laughter">`
   - Editorial remarks: `"(...)"` $\rightarrow$ `<note type="comment">`
   - Spoken prose $\rightarrow$ `<seg>`

---

### 4.5 Step 5: Entity Resolution & Disambiguation (`resolve_speakers.py`)
A core challenge in parliamentary corpus compilation is mapping ambiguous natural language strings (e.g., *"Z. Braçe"*, *"Kryetarja"*, *"Ministri Manja"*, *"Erion Brace"*) to unique authority IDs (`AL_PERS_BraçeErion`).

```
+---------------------------------------------------------------------------------------------------+
|                                     SPEAKER RESOLUTION WORKFLOW                                   |
+---------------------------------------------------------------------------------------------------+
|  Raw Cue: "Z. Taulant Balla – Faleminderit..."                                                    |
|    |                                                                                              |
|    +---> 1. Strip Honorifics: "Taulant Balla" (removes "Z.", "Znj.", "Deputeti", etc.)           |
|    +---> 2. Canonical Normalization: Case folding, diacritics alignment                           |
|    +---> 3. Alias Lookup: Checks SPEAKER_ALIASES dictionary (OCR misspellings)                    |
|    +---> 4. Registry Matching: Multi-index lookup in persons.csv (Full Name -> Surname)           |
|    +---> 5. Temporal Verification: Date matching against affiliations.csv                         |
|    +---> 6. Role Assignment:                                                                      |
|              - Matches Sitting Chair? ==> #chair                                                  |
|              - Minister / Guest Affiliation? ==> #guest                                           |
|              - Regular MP? ==> #regular                                                           |
|    +---> 7. Fallback: If unresolved, heuristic minting & audit logging to CSV                         |
+---------------------------------------------------------------------------------------------------+
```

- **Resolution Strategy**:
  1. **Exact Full Name Matching**: Normalized string matches `f"{forename} {surname}"` or `f"{surname} {forename}"`.
  2. **Unique Surname Lookup**: If only a surname is given, matches against `surname_map`. If unambiguous (exactly 1 candidate), resolves with `"alias"` confidence.
  3. **Presiding Officer Context**: If the normalized speaker matches the session chair extracted from the header, the speaker role is dynamically assigned as `@ana="#chair"`.
  4. **Temporal Affiliation Querying**: Evaluates whether the sitting date falls within the person's active affiliation intervals (`from_date` $\le \text{date} \le$ `to_date`). If the speaker holds a ministerial or external post, role is set to `@ana="#guest"`; otherwise `@ana="#regular"`.
  5. **Audit Reporting**: Any unresolved or heuristically minted speaker is logged to `out/TEI/unresolved_speakers_report.csv` for human curation.

---

### 4.6 Step 6: Linguistic Annotation Architecture (`annotate_stanza.py`)
To generate `out/TEI/ana/*.ana.xml`, plain TEI files are processed through the **Stanza** NLP pipeline (Universal Dependencies v2 for Albanian):
- Pipeline configuration: `stanza.Pipeline(lang="sq", processors="tokenize,pos,lemma,depparse")`.
- Text inside `<seg>` is passed to the NLP pipeline.
- Output tokens are converted into `<s>` (sentence), `<w>` (word token with `@lemma`, `@pos`, `@msd`, `@dep`, `@head`), and `<pc>` (punctuation mark) elements.
- The component root attributes are updated: `@xml:id` is suffixed with `.ana`, and `@ana` is augmented with `"#ud-sq-stanza"`.

---

## 5. Corpus Output, Formats, and Schema Validation

### 5.1 Corpus File System Structure
The generated corpus follows the standardized directory layout:

```
out/TEI/
├── ParlaMint-AL.xml                         # Master corpus root (Plain TEI)
├── ParlaMint-AL.ana.xml                     # Master corpus root (Linguistic .ana TEI)
├── ParlaMint-AL-listPerson.xml              # Stand-off Person authority registry
├── ParlaMint-AL-listOrg.xml                 # Stand-off Organisation authority registry
├── ParlaMint-taxonomy-speaker_types.xml     # Speaker roles taxonomy (#chair, #regular, #guest)
├── ParlaMint-taxonomy-parla.roles.xml       # Institutional roles taxonomy (#head, #member, etc.)
├── ParlaMint-taxonomy-subcorpus.xml         # Subcorpus partition taxonomy (#reference, etc.)
├── ParlaMint-taxonomy-parla.legislature.xml # Legislative taxonomy (#parla.sitting, etc.)
├── ParlaMint-taxonomy-politicalOrientation.xml # Party orientation taxonomy
├── ParlaMint-taxonomy-CHES.xml              # Chapel Hill Expert Survey taxonomy
├── unresolved_speakers_report.csv          # QA audit log for speaker resolution
├── plain/                                  # Component plain TEI XML files
│   ├── ParlaMint-AL_2025-10-17.xml
│   ├── ParlaMint-AL_2025-10-23.xml
│   └── ...
└── ana/                                    # Component linguistically annotated TEI XML files
    ├── ParlaMint-AL_2025-10-17.ana.xml
    ├── ParlaMint-AL_2025-10-23.ana.xml
    └── ...
```

---

### 5.2 Comparative Analysis: Plain TEI vs. Annotated TEI (`.ana`)

| Architectural Dimension | Plain TEI Component (`out/TEI/plain/`) | Annotated TEI Component (`out/TEI/ana/`) |
|:---|:---|:---|
| **Root Tag & ID** | `<TEI xml:id="ParlaMint-AL_2025-11-13">` | `<TEI xml:id="ParlaMint-AL_2025-11-13.ana">` |
| **Root Annotation (`@ana`)** | `ana="#parla.sitting #reference"` | `ana="#parla.sitting #reference #ud-sq-stanza"` |
| **Segment Content (`<seg>`)** | Plain text string with whitespace squashed | Structured sentence (`<s>`) and token (`<w>`, `<pc>`) tree |
| **Linguistic Metadata** | None (lexical level only) | Lemma, UPOS, Universal Features MSD, Dependency relations & Heads |
| **Primary Research Utility** | Corpus query engines (CQP), text classification, LLM prompt ingestion | Syntactic treebanking, quantitative grammar analysis, complex grammatical querying |
| **Processing Overhead** | Lightweight (linear regex and XML serialization) | Intensive (neural tokenization, POS tagging, and biaffine dependency parsing) |

---

### 5.3 Quality Control & Validation Protocols
Validation is conducted across four strict layers:
1. **XML Well-Formedness & Namespace Integrity**: All elements strictly reside in the TEI namespace (`http://www.tei-c.org/ns/1.0`), XInclude namespace (`http://www.w3.org/2001/XInclude`), or XML namespace (`http://www.w3.org/XML/1998/namespace`).
2. **Schema Conformance (Relax NG & Schematron)**:
   - Validated against official ParlaMint 5.0 RNG schemas (`ParlaMint-TEI.rng` and `ParlaMint-TEI.ana.rng`).
   - Ensures valid `<teiHeader>` structure, mandatory dual-language descriptions, non-empty `<editionStmt>`, and correct placement of `<tagsDecl>`.
3. **Cross-Reference Referential Integrity**:
   - Every `@who` attribute on `<u>` resolves to an existing `@xml:id` in `ParlaMint-AL-listPerson.xml`.
   - Every `@ana` attribute resolves to a declared category in the corresponding taxonomy XML file.
   - Every `@corresp` on `<meeting>` resolves to an organization in `ParlaMint-AL-listOrg.xml`.
4. **Extent Consistency**:
   - The corpus root extent measures ($\sum \text{speeches}, \sum \text{words}$) exactly match the sum of component measurements.

---

## 6. Academic Use Cases, Research Methodologies, and Master-Level Applications

The ParlaMint-AL corpus provides an empirical foundation for interdisciplinary research:

```
+---------------------------------------------------------------------------------------------------+
|                                      RESEARCH METHODOLOGY STACK                                   |
+---------------------------------------------------------------------------------------------------+
|  [Political Science]         [Computational Linguistics]          [Digital Humanities]            |
|  - Speech Share by Gender    - Syntactic Complexity Analysis      - Inter-parliamentary Alignment |
|  - Cabinet vs Opposition     - Named Entity Disambiguation        - Diachronic Topic Drift        |
|  - Party Discipline Index    - Sentiment & Stance Detection       - SPARQL Semantic Queries       |
+---------------------------------------------------------------------------------------------------+
```

### 6.1 Quantitative Political Science
- **Gender & Discourse Dynamics**: By joining `u/@who` with `person/sex/@value`, researchers can measure the proportion of floor time, floor interruptions (`<vocal type="interruption">`), and agenda leadership occupied by female MPs across parliamentary cycles.
- **Government-Opposition Interaction**: By linking speaker party affiliations to the `politicalOrientation` taxonomy, political scientists can track adversarial speech patterns, committee scrutiny levels, and voting loyalty.

### 6.2 Computational Linguistics & NLP
- **Syntactic Parsing Evaluation**: ParlaMint-AL.ana provides a rich source of authentic, spontaneous spoken-prose syntax in Albanian for testing and training dependency parsers.
- **Stance & Argument Mining**: Investigating how political actors frame contentious policy issues (e.g., judicial reform, European Union integration) using dependency-based feature extraction.

### 6.3 Digital Humanities & Semantic Web Integration
- **Linked Open Data (LOD)**: The inclusion of Wikidata URIs in `listPerson` allows ParlaMint-AL to be federated with external knowledge graphs (e.g., DBpedia, Europeana, Wikidata Query Service), enabling SPARQL queries across European political datasets.

---

## 7. Conclusion & Future Roadmap

ParlaMint-AL establishes a high-quality, ParlaMint 5.0-compliant TEI XML infrastructure for the Parliament of Albania. By unifying automated web scraping, domain-specific text normalization, rule-based discourse parsing, temporal entity resolution, and neural linguistic annotation, the pipeline transforms messy PDF proceedings into an open, FAIR, and interoperable digital research asset.

### Ongoing & Future Extensions:
1. **Audio/Video Alignment**: Synchronizing utterance timestamps (`<u>`) with official broadcast archives.
2. **Historical Back-Crawl**: Extending the temporal reach of the corpus back through earlier post-communist legislatures (1991–2020).
3. **Automated Akoma Ntoso Mapping**: Exposing bi-directional transformations between TEI P5 and the UN Akoma Ntoso legislative XML standard.
4. **Integration with CLARIN Concordance Services**: Deploying ParlaMint-AL into online query engines such as **KonText** and **NoSketch Engine**.

---

### References & Technical Specifications
- CLARIN ERIC ParlaMint Portal: [https://www.clarin.eu/parlamint](https://www.clarin.eu/parlamint)
- ParlaMint Guidelines & Schemas: [https://clarin-eric.github.io/ParlaMint/](https://clarin-eric.github.io/ParlaMint/)
- Text Encoding Initiative (TEI P5): [https://tei-c.org/guidelines/p5/](https://tei-c.org/guidelines/p5/)
- Universal Dependencies v2 Specification: [https://universaldependencies.org/](https://universaldependencies.org/)
