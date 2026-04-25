"""Extract JSON from AgentCore logs."""
import json
import re
import sys

logfile = sys.argv[1]
outfile = sys.argv[2]

with open(logfile) as f:
    lines = f.readlines()

in_json = False
json_lines = []
for line in lines:
    text = line.strip()
    if "```json" in text:
        in_json = True
        json_lines = []
        continue
    if in_json:
        cleaned = re.sub(r'^2026-04-25T\d{2}:\d{2}:\d{2}\s*', '', text)
        if cleaned:
            json_lines.append(cleaned)

json_text = "\n".join(json_lines)

# Find end of JSON by brace matching
depth = 0
end_pos = 0
for i, ch in enumerate(json_text):
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            end_pos = i + 1
            break

parsed = json.loads(json_text[:end_pos])
print(f"Keys: {list(parsed.keys())}")

with open(outfile, "w") as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)
print(f"Saved to {outfile}")
