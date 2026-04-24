# knowledge_graph.py
# Install first: pip install anthropic networkx matplotlib
import json
import anthropic
import networkx as nx
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
# ─────────────────────────────────────────
# STEP 1: Define the schema via tools
# (structured output — D4 exam concept)
# ─────────────────────────────────────────
extraction_tool = {
    "name": "extract_knowledge",
    "description": "Extract entities and relationships from text",
    "input_schema": {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":   {"type": "string"},   # unique identifier
                        "name": {"type": "string"},   # entity name
                        "type": {"type": "string"}    # PERSON, ORG, PLACE, etc.
                    },
                    "required": ["id", "name", "type"]
                }
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source":   {"type": "string"},  # entity id
                        "target":   {"type": "string"},  # entity id
                        "relation": {"type": "string"}   # WORKS_AT, FOUNDED, etc.
                    },
                    "required": ["source", "target", "relation"]
                }
            }
        },
        "required": ["entities", "relationships"]
    }
}
# ─────────────────────────────────────────
# STEP 2: Extract entities + relationships
# ─────────────────────────────────────────
def extract_graph(text: str) -> dict:
    """Send text to Claude, get back structured entities + relationships."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        tools=[extraction_tool],
        tool_choice={"type": "tool", "name": "extract_knowledge"},  # force tool use
        messages=[
            {
                "role": "user",
                "content": f"""
Extract all entities (people, organizations, places, concepts) 
and relationships between them from this text.
Text:
{text}
"""
            }
        ]
    )
    # tool_use block contains our structured output
    for block in response.content:
        if block.type == "tool_use":
            return block.input  # already parsed as dict
    return {"entities": [], "relationships": []}
# ─────────────────────────────────────────
# STEP 3: Entity resolution
# Deduplicate entities across multiple texts
# (Claude decides what's the same entity)
# ─────────────────────────────────────────
def resolve_entities(all_entities: list) -> dict:
    """Ask Claude to deduplicate entities — returns mapping of duplicate id → canonical id."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""
Given these entities extracted from multiple texts, identify duplicates.
Return ONLY a JSON object mapping duplicate IDs to their canonical (keep) ID.
Example: {{"id2": "id1", "id5": "id1"}}
Entities:
{json.dumps(all_entities, indent=2)}
Return only the JSON mapping, no explanation.
"""
            }
        ]
    )
    raw = response.content[0].text.strip()
    # strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {}  # no duplicates found
# ─────────────────────────────────────────
# STEP 4: Build the graph
# ─────────────────────────────────────────
def build_graph(extractions: list, duplicate_map: dict) -> nx.DiGraph:
    """Merge all extractions into a single directed graph."""
    G = nx.DiGraph()
    # collect all entities first
    all_entities = {}
    for extraction in extractions:
        for entity in extraction["entities"]:
            canonical_id = duplicate_map.get(entity["id"], entity["id"])
            all_entities[canonical_id] = entity["name"]
    # add nodes
    for entity_id, name in all_entities.items():
        G.add_node(entity_id, label=name)
    # add edges with deduplication applied
    for extraction in extractions:
        for rel in extraction["relationships"]:
            source = duplicate_map.get(rel["source"], rel["source"])
            target = duplicate_map.get(rel["target"], rel["target"])
            if source in G and target in G:
                G.add_edge(source, target, relation=rel["relation"])
    return G
# ─────────────────────────────────────────
# STEP 5: Multi-hop query
# ─────────────────────────────────────────
def query_graph(G: nx.DiGraph, question: str, graph_data: dict) -> str:
    """Ask Claude a question using the graph as context."""
    # serialize graph for Claude
    nodes = [f"{G.nodes[n]['label']} (id: {n})" for n in G.nodes]
    edges = [
        f"{G.nodes[u]['label']} --[{d['relation']}]--> {G.nodes[v]['label']}"
        for u, v, d in G.edges(data=True)
    ]
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"""
Answer this question using ONLY the knowledge graph below.
Trace your reasoning through the graph step by step.
Question: {question}
Knowledge Graph:
Entities: {json.dumps(nodes, indent=2)}
Relationships: {json.dumps(edges, indent=2)}
"""
            }
        ]
    )
    return response.content[0].text
# ─────────────────────────────────────────
# STEP 6: Visualize
# ─────────────────────────────────────────
def visualize_graph(G: nx.DiGraph):
    """Draw the knowledge graph."""
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    labels = nx.get_node_attributes(G, 'label')
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
    nx.draw_networkx_labels(G, pos, labels, font_size=9)
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=20)
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7)
    plt.title("Knowledge Graph")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("knowledge_graph.png", dpi=150)
    plt.show()
    print("Graph saved to knowledge_graph.png")
# ─────────────────────────────────────────
# MAIN — Run everything
# ─────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json
    filename = sys.argv[1] if len(sys.argv) > 1 else "input.json"
    print(f"Reading from: {filename}")
    with open(filename, "r") as f:
        data = json.load(f)
    documents = data["documents"]
    texts = [doc["text"] for doc in documents]
    print(f"Found {len(texts)} documents\n")
    for doc in documents:
        print(f"  [{doc['id']}] {doc['title']}")
    print()
    print("Step 1: Extracting entities and relationships...")
    extractions = []
    all_entities = []
    for i, (text, doc) in enumerate(zip(texts, documents)):
        print(f"  Processing [{doc['id']}]: {doc['title']}...")
        result = extract_graph(text)
        extractions.append(result)
        all_entities.extend(result["entities"])
        print(f"  Found {len(result['entities'])} entities, {len(result['relationships'])} relationships")
    print("\nStep 2: Resolving duplicate entities...")
    duplicate_map = resolve_entities(all_entities)
    print(f"  Duplicate mappings: {duplicate_map}")
    print("\nStep 3: Building graph...")
    G = build_graph(extractions, duplicate_map)
    print(f"  Graph has {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print("\nStep 4: Multi-hop query...")
    question = "Who leads the company that Microsoft invested in?"
    answer = query_graph(G, question, {})
    print(f"  Q: {question}")
    print(f"  A: {answer}")
    print("\nStep 5: Visualizing...")
    visualize_graph(G)