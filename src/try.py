from pathlib import Path
from .segment import SPEAKER_LINE, _paragraphs
from .utils import normalize_text

# Use relative path inside the project
text_path = Path(
    r"inbox/cleaned/202510241107180185Procesverbal%2C_dat%C3%AB_17.10.2025.txt"
)

raw = text_path.read_text(encoding="utf-8")
text = normalize_text(raw)

for para in _paragraphs(text):
    first = para.splitlines()[0].strip()
    print("FIRST:", repr(first), "MATCH:", bool(SPEAKER_LINE.match(first)))
