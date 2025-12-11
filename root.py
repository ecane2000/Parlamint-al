<?xml version="1.0" encoding="UTF-8"?>
<teiCorpus xmlns="http://www.tei-c.org/ns/1.0"
           xmlns:xi="http://www.w3.org/2001/XInclude"
           xml:id="ParlaMint-AL"
           xml:lang="sq">

  <!-- ===================== corpus header ===================== -->
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title xml:lang="sq">
          ParlaMint-AL: Korpusi i seancave parlamentare të Kuvendit të Shqipërisë
        </title>
        <title xml:lang="en">
          ParlaMint-AL: Albanian parliamentary proceedings corpus
        </title>

        <!-- Add your real editors / compilers here -->
        <respStmt>
          <resp xml:lang="en">Corpus compilation and TEI conversion</resp>
          <name xml:lang="sq">[Shqipëri: ekipi ParlaMint-AL]</name>
        </respStmt>
      </titleStmt>

      <editionStmt>
        <edition n="1.0" xml:lang="en">First release of ParlaMint-AL</edition>
      </editionStmt>

      <!-- Fill in when you know the exact size -->
      <extent>
        <measure unit="speeches">0</measure>
        <measure unit="words">0</measure>
      </extent>

      <publicationStmt>
        <publisher xml:lang="en">[Your institution, e.g. University X / CLARIN-AL]</publisher>
        <pubPlace xml:lang="sq">Tiranë</pubPlace>
        <availability>
          <licence target="http://creativecommons.org/licenses/by/4.0/">
            CC BY 4.0
          </licence>
        </availability>
        <idno type="hdl">http://hdl.handle.net/11356/ParlaMint-AL</idno>
      </publicationStmt>

      <sourceDesc>
        <bibl xml:lang="sq">
          Protokollet e seancave të Kuvendit të Shqipërisë, të shkarkuara nga
          faqja zyrtare e Kuvendit: https://www.parlament.al
        </bibl>
      </sourceDesc>
    </fileDesc>

    <encodingDesc>
      <projectDesc>
        <p xml:lang="en">
          The ParlaMint-AL corpus is part of the ParlaMint project, providing a
          TEI-encoded, linguistically annotated corpus of Albanian parliamentary
          debates comparable with other ParlaMint corpora.
        </p>
        <p xml:lang="sq">
          Korpusi ParlaMint-AL është pjesë e projektit ParlaMint dhe ofron
          një korpus të shënjuar të seancave parlamentare në gjuhën shqipe,
          i krahasueshëm me korpuset e vendeve të tjera.
        </p>
      </projectDesc>

      <!-- Taxonomies: common + (later) your local ones -->
      <classDecl>
        <!-- Common ParlaMint taxonomies (these filenames are standardized) -->
        <xi:include href="ParlaMint-taxonomy-parla.legislature.xml"/>
        <xi:include href="ParlaMint-taxonomy-speaker_types.xml"/>
        <!-- Later you can add UD / NER / local taxonomies here as needed -->
        <!-- <xi:include href="ParlaMint-taxonomy-UD-SYN.xml"/> -->
      </classDecl>

      <tagsDecl>
        <tagUsage gi="u" occurs="veryOften"/>
        <tagUsage gi="w" occurs="veryOften"/>
      </tagsDecl>

      <editorialDecl>
        <normalization>
          <p xml:lang="en">
            Obvious OCR errors and encoding issues have been corrected; line-end
            hyphenation has been removed; multiple spaces collapsed to one.
          </p>
        </normalization>
      </editorialDecl>
    </encodingDesc>

    <profileDesc>
      <!-- Where & when, at corpus level -->
      <settingDesc>
        <setting>
          <name type="address">Bulevardi Dëshmorët e Kombit</name>
          <name type="city">Tiranë</name>
          <name type="country" key="AL">Shqipëri</name>
          <!-- Global time span of the corpus; adjust once you know it -->
          <date from="2015-01-01" to="2025-12-31">
            2015–2025
          </date>
        </setting>
      </settingDesc>

      <!-- TextClass with basic ParlaMint categories -->
      <textClass>
        <catRef scheme="#parla.legislature" target="#parla.uni"/>
        <catRef scheme="#parla.chamber" target="#parla.lower"/>
      </textClass>

      <!-- Participant description: listOrg + listPerson via XInclude -->
      <particDesc>
        <!-- Your TEI list of organisations -->
        <xi:include href="ParlaMint-AL-listOrg.xml"/>
        <!-- Your TEI list of persons/speakers -->
        <xi:include href="ParlaMint-AL-listPerson.xml"/>
      </particDesc>

      <!-- Languages used in the corpus -->
      <langUsage>
        <language ident="sq" xml:lang="sq">shqip</language>
        <language ident="en" xml:lang="sq">anglisht</language>
        <language ident="sq" xml:lang="en">Albanian</language>
        <language ident="en" xml:lang="en">English</language>
      </langUsage>
    </profileDesc>

    <revisionDesc>
      <change when="2025-12-01">
        <name>[Your name / team]</name>:
        Initial ParlaMint-AL corpus compilation.
      </change>
    </revisionDesc>
  </teiHeader>

  <!-- ===================== components via XInclude ===================== -->
  <!--
    In a full ParlaMint distro, these are year subdirectories:

      ParlaMint-AL.TEI/2015/ParlaMint-AL_2015-01-05-1.xml
      ParlaMint-AL.TEI/2015/ParlaMint-AL_2015-01-06-1.xml
      ...

    During development, if your pipeline writes into out/TEI/plain/,
    you can either:
      - move files into year dirs as above, or
      - temporarily point href to "plain/..." (not “official”, but works).
  -->

  <!-- Example: 3 components in 2015 -->
  <xi:include href="2015/ParlaMint-AL_2015-01-05-1.xml"/>
  <xi:include href="2015/ParlaMint-AL_2015-01-06-1.xml"/>
  <xi:include href="2015/ParlaMint-AL_2015-01-07-1.xml"/>

  <!-- Example: 2 components in 2016 -->
  <xi:include href="2016/ParlaMint-AL_2016-02-10-1.xml"/>
  <xi:include href="2016/ParlaMint-AL_2016-02-11-1.xml"/>

  <!-- etc. In practice you generate one xi:include per TEI component file. -->

</teiCorpus>
