import sys
sys.path.insert(0, r"C:\Users\Keerthisri\Desktop\Design and Development of Ai crime Investigator\Ai_Crime_investigator")

from backend.nlp.ner_extractor import extract_entities
from backend.nlp.relation_extractor import extract_relations
from backend.graph.case_graph_builder import build_case_graph, get_graph_summary, graph_has_path
from backend.graph.graph_store import run_search_details, normalize_node

with open(r"C:\Users\Keerthisri\AppData\Local\Temp\opencode\case_new.txt", encoding="utf-8") as fh:
    case_text = fh.read()

entities = extract_entities(case_text)
print("=== ENTITIES ===")
for e in entities:
    print(f"  {e}")
print(f"  TOTAL: {len(entities)}")

relations = extract_relations(case_text, entities)
print("=== RELATIONS ===")
for r in relations:
    print(f"  {r['source']} --{r['relation']}--> {r['target']}  (conf={r['confidence']}, reason={r['reason'][:60]!r})")
print(f"  TOTAL: {len(relations)}")

graph = build_case_graph(entities, relations)
print("=== GRAPH NODES ===")
for n in graph.nodes:
    print(f"  node={n!r}")
print(f"  TOTAL: {graph.number_of_nodes()}")
print("=== GRAPH EDGES ===")
for s, t, d in graph.edges(data=True):
    print(f"  {s!r} --{d.get('relation')}--> {t!r}")
print(f"  TOTAL: {graph.number_of_edges()}")
print("=== SUMMARY ===")
print(get_graph_summary(graph))

print("=== SEARCH: Arun Kumar -> Ravi ===")
for start, target in [("Arun Kumar", "Ravi"), ("Ravi", "Arun Kumar")]:
    print(f"--- {start} -> {target} ---")
    print("  has_path:", graph_has_path(graph, start, target))
    det = run_search_details(graph, start, target)
    for alg in ("BFS", "DFS", "A*"):
        d = det.get(alg) or {}
        print(f"  {alg}: found={d.get('found')} path={d.get('path')} len={d.get('path_length')} visited={d.get('visited_nodes')} cost={d.get('cost')}")