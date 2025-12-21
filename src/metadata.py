# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Optional, Dict
from .utils import normalize_name, mint_person_id

@dataclass
class DocumentMetadata:
    date: str
    time: Optional[str]
    eventType: Optional[str]
    eventTypeAna: Optional[str] = None
    chair_name: Optional[str] = None
    chair_role: Optional[str] = None
    topics: Optional[str] = None
    place: str = "Tiranë, AL"
    licence_url: str = "https://creativecommons.org/licenses/by/4.0/"
    speakers_idx: Dict[str, str] = field(default_factory=dict)

    def speaker_id(self, full_name: str) -> str:
        key = normalize_name(full_name)
        if key in self.speakers_idx:
            return self.speakers_idx[key]
        pid = mint_person_id(full_name)
        self.speakers_idx[key] = pid
        return pid


