from __future__ import annotations

import networkx as nx
import pandas as pd


def build_network(df: pd.DataFrame) -> dict:
    graph = nx.DiGraph()
    transitions: dict[tuple[str, str], int] = {}

    previous = None
    for row in df.itertuples(index=False):
        graph.add_node(row.sender)
        if previous is not None:
            key = (previous.sender, row.sender)
            transitions[key] = transitions.get(key, 0) + 1
        previous = row

    for (source, target), weight in transitions.items():
        graph.add_edge(source, target, weight=weight)

    edges = [
        {"source": source, "target": target, "weight": int(data["weight"])}
        for source, target, data in graph.edges(data=True)
    ]
    total_weight = sum(data["weight"] for _, _, data in graph.edges(data=True))
    centrality = {
        node: (graph.degree(node, weight="weight") / (2 * total_weight) if total_weight else 0)
        for node in graph.nodes
    }
    return {
        "nodes": [{"id": node, "centrality": round(float(centrality[node]), 3)} for node in graph.nodes],
        "edges": edges,
    }
