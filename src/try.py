from pathlib import Path
from .segment import SPEAKER_LINE

text_path = Path(
    r"C:\Users\ecane\Projects\Parlamint-al\inbox\cleaned\202510241107180185Procesverbal%2C_dat%C3%AB_17.10.2025.txt"
)
text = text_path.read_text(encoding="utf-8")

for i, line in enumerate(text.splitlines(), 1):
    s = line.strip()
    print(i, repr(s), "MATCH:", bool(SPEAKER_LINE.match(s)))
