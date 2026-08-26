import json
from collections import Counter, defaultdict

g = json.load(open("graphify-out/graph.json", encoding="utf-8"))
nodes = g.get("nodes", [])
print(f"Total nodes: {len(nodes)}, edges: {len(g.get('edges', g.get('links', [])))}")

src_counter = Counter()
for n in nodes:
    src = n.get("source_file") or n.get("source") or "?"
    parts = src.replace("\\", "/").split("/")
    # bucket by recognizable segment
    if "docs" in parts:
        b = "docs"
    elif "services" in parts:
        i = parts.index("services")
        b = f"services/{parts[i+1] if i+1 < len(parts) else '?'}"
    elif "shared" in parts:
        b = "shared"
    elif "scripts" in parts:
        b = "scripts"
    else:
        b = "other:" + "/".join(parts[:2])
    src_counter[b] += 1

for k, v in sorted(src_counter.items()):
    print(f"{v:4d}  {k}")
