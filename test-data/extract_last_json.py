"""Extract the LAST JSON block from AgentCore logs."""
import json
import re
import sys

logfile = sys.argv[1]
outfile = sys.argv[2]

with open(logfile) as f:
    lines = f.readlines()

# Find ALL ```json blocks and keep the last one
all_blocks = []
in_json = False
current_lines = []

for line in lines:
    text = line.strip()
    if "```json" in text:
        in_json = True
        current_lines = []
        continue
    if in_json and "```" in text and not text.startswith("{"):
        # End of block
        in_json = False
        if current_lines:
            all_blocks.append(current_lines[:])
        current_lines = []
        continue
    if in_json:
        cleaned = re.sub(r'^2026-04-25T\d{2}:\d{2}:\d{2}\s*', '', text)
        if cleaned:
            current_lines.append(cleaned)

# If still in_json (no closing ```), save what we have
if in_json and current_lines:
    all_blocks.append(current_lines)

print(f"Found {len(all_blocks)} JSON blocks")

# Try each block from last to first
for i, block in enumerate(reversed(all_blocks)):
    json_text = "\n".join(block)
    # Find end by brace matching
    depth = 0
    end_pos = 0
    for j, ch in enumerate(json_text):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end_pos = j + 1
                break
    if end_pos == 0:
        continue
    try:
        parsed = json.loads(json_text[:end_pos])
        if isinstance(parsed, dict) and ("executive_readings" in parsed or "quizzes" in parsed or "top20_papers" in parsed):
            print(f"Using block {len(all_blocks) - i} (from end). Keys: {list(parsed.keys())}")
            with open(outfile, "w") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
            print(f"Saved to {outfile}")
            sys.exit(0)
    except json.JSONDecodeError:
        continue

print("No valid JSON block found with expected keys")
sys.exit(1)
