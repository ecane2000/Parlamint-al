# -*- coding: utf-8 -*-
"""
ParlaMint-AL package:
Tools for compiling, processing, and encoding Albanian parliamentary proceedings
into the standard ParlaMint TEI XML and TEI.ana format.
"""
from .config import PARLIAMENT_NAME, COUNTRY_CODE, LANGUAGE_CODE
from .metadata import DocumentMetadata
from .person_org_metadata import PersonMetadata, OrgMetadata, Affiliation
from .segment import SittingBlock, SpeechBlock
from .resolve_speakers import SpeakerResolution

__version__ = "0.2.0"
