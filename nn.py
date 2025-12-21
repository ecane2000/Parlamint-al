from pathlib import Path
p = Path("urls.txt")
lines = []
for ln in p.read_text(encoding="utf-8").splitlines():
    u = ln.strip()
    if (u.startswith('"') and u.endswith('"')) or (u.startswith("'") and u.endswith("'")):
        u = u[1:-1].strip()
    u = u.rstrip("\\").strip()
    if u and not u.startswith("#"):
        lines.append(u)
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Cleaned urls.txt")

