"""
Centrality Analysis Module conforming to Section 8.1 of Route Resilience specification.
Implements Brandes' algorithm for exact weighted Betweenness Centrality,
Closeness Centrality, and Degree Centrality.
"""

from typing import Dict, List, Tuple, Set, Optional
import heapq
from ..topology.graph_base import Graph


def betweenness_centrality(G: Graph, weight: Optional[str] = "weight", normalized: bool = True) -> Dict[str, float]:
    """
    Computes Brandes' Betweenness Centrality for all nodes in graph G.
    Handles weighted shortest paths. Matches known-value unit test results.
    """
    CB = {v: 0.0 for v in G.nodes}
    nodes = list(G.nodes.keys())
    n = len(nodes)
    if n <= 2:
        return CB

    for s in nodes:
        # Single-source shortest path counting
        S = []
        P: Dict[str, List[str]] = {w: [] for w in nodes}
        sigma = {w: 0.0 for w in nodes}
        sigma[s] = 1.0
        d: Dict[str, float] = {w: float('inf') for w in nodes}
        d[s] = 0.0

        # Priority queue for Dijkstra
        pq = [(0.0, s)]
        visited = set()

        while pq:
            dist_u, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            S.append(u)

            for v, edge_data in G._adj.get(u, {}).items():
                w = edge_data.get(weight, 1.0) if weight else 1.0
                new_d = dist_u + w
                if new_d < d[v]:
                    d[v] = new_d
                    sigma[v] = sigma[u]
                    P[v] = [u]
                    heapq.heappush(pq, (new_d, v))
                elif abs(new_d - d[v]) < 1e-9:
                    sigma[v] += sigma[u]
                    P[v].append(u)

        # Accumulation of dependencies
        delta = {w: 0.0 for w in nodes}
        while S:
            w = S.pop()
            for v in P[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                CB[w] += delta[w]

    # For undirected graphs, halve the accumulated counts
    for v in CB:
        CB[v] /= 2.0

    if normalized and n > 2:
        scale = 2.0 / ((n - 1) * (n - 2))
        for v in CB:
            CB[v] *= scale

    return CB


def degree_centrality(G: Graph) -> Dict[str, float]:
    n = len(G.nodes)
    if n <= 1:
        return {v: 0.0 for v in G.nodes}
    scale = 1.0 / (n - 1)
    return {v: G.degree(v) * scale for v in G.nodes}


def closeness_centrality(G: Graph, weight: Optional[str] = "weight") -> Dict[str, float]:
    n = len(G.nodes)
    closeness = {}
    if n <= 1:
        return {v: 0.0 for v in G.nodes}

    for u in G.nodes:
        # Dijkstra from u
        distances = {v: float('inf') for v in G.nodes}
        distances[u] = 0.0
        pq = [(0.0, u)]
        visited = set()
        total_dist = 0.0
        reachable_count = 0

        while pq:
            d, curr = heapq.heappop(pq)
            if curr in visited:
                continue
            visited.add(curr)
            if curr != u:
                total_dist += d
                reachable_count += 1
            for nbr, ed in G._adj.get(curr, {}).items():
                w = ed.get(weight, 1.0) if weight else 1.0
                if d + w < distances[nbr]:
                    distances[nbr] = d + w
                    heapq.heappush(pq, (d + w, nbr))

        if total_dist > 0 and reachable_count > 0:
            closeness[u] = (reachable_count / (n - 1)) * (reachable_count / total_dist)
        else:
            closeness[u] = 0.0

    return closeness
