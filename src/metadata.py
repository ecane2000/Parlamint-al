from dataclasses import dataclass
from .utils import guess_date_from_url

@dataclass
class DocMeta:
    when_iso: str
    source_url: str
    title: str

    @classmethod
    def from_url(cls, url: str):
        d = guess_date_from_url(url)
        return cls(when_iso=d, source_url=url, title=f"ParlaMint-AL: Seanca {d} (plain)")
