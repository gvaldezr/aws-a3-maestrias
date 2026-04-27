"""Show reading sizes for a subject."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/latest.json"
with open(path) as f:
    sj = json.load(f)

er = sj.get("content_package", {}).get("executive_readings", {})
readings = er.get("readings", []) if isinstance(er, dict) else (er if isinstance(er, list) else [])

print(f"Asignatura: {sj['metadata']['subject_name']}")
print(f"Total lecturas: {len(readings)}")
print("=" * 70)

for r in readings:
    if not isinstance(r, dict):
        continue
    title = r.get("title", "")
    content = r.get("content_md", "")
    words = len(content.split())
    chars = len(content)
    lines = content.count("\n") + 1

    print(f"\nSemana {r.get('week', '')}: {title}")
    print(f"  Caracteres: {chars:,}")
    print(f"  Palabras:   {words:,}")
    print(f"  Lineas:     {lines}")
    print(f"  Preview:    {content[:200]}...")
    print("-" * 60)

total_chars = sum(len(r.get("content_md", "")) for r in readings if isinstance(r, dict))
total_words = sum(len(r.get("content_md", "").split()) for r in readings if isinstance(r, dict))
print(f"\nTOTAL: {total_chars:,} caracteres, {total_words:,} palabras")
print(f"Promedio por lectura: {total_chars // max(len(readings),1):,} chars, {total_words // max(len(readings),1):,} palabras")
