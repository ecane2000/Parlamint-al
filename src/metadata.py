from dataclasses import dataclass
from pathlib import Path
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

    @classmethod
    def from_source(cls, path: Path, url: str | None = None):
        """
        Build metadata when we have a local TXT path and optionally a source URL.
        Falls back to guessing the date from the path string if URL is missing.
        """
        basis = url if url else str(path)
        d = guess_date_from_url(basis)
        return cls(
            when_iso=d,
            source_url=url if url else f"file://{path.name}",
            title=f"ParlaMint-AL: Seanca {d} (plain)"
        )
