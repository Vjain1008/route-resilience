"""
Core graph data structures and spatial algorithms implemented in pure Python.
Provides NetworkX-compatible API signatures for nodes, edges, weights, and spatial search.
Conforms to Route Resilience Specification Section 8 & 10.
"""

import math
import heapq
from typing import Dict, List, Tuple, Set, Any, Optional, Iterator

class Graph:
    """Undirected weighted graph with spatial attributes."""
    def __init__(self):
        self._adj: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._nodes: Dict[str, Dict[str, Any]] = {}

    def add_node(self, node_id: str, **attrs):
        if node_id not in self._adj:
            self._adj[node_id] = {}
        if node_id not in self._nodes:
            self._nodes[node_id] = {}
        self._nodes[node_id].update(attrs)

    def add_edge(self, u: str, v: str, **attrs):
        if u not in self._adj:
            self.add_node(u)
        if v not in self._adj:
            self.add_node(v)
        
        # Default weight to length_m or 1.0 if not specified
        if "weight" not in attrs and "length_m" in attrs:
            attrs["weight"] = float(attrs["length_m"])
        elif "weight" not in attrs:
            attrs["weight"] = 1.0

        if v in self._adj[u]:
            self._adj[u][v].update(attrs)
            self._adj[v][u].update(attrs)
        else:
            self._adj[u][v] = dict(attrs)
            self._adj[v][u] = dict(attrs)

    def remove_node(self, node_id: str):
        if node_id in self._adj:
            neighbors = list(self._adj[node_id].keys())
            for nbr in neighbors:
                del self._adj[nbr][node_id]
            del self._adj[node_id]
        if node_id in self._nodes:
            del self._nodes[node_id]

    def remove_edge(self, u: str, v: str):
        if u in self._adj and v in self._adj[u]:
            del self._adj[u][v]
            del self._adj[v][u]

    def has_node(self, n: str) -> bool:
        return n in self._nodes

    def has_edge(self, u: str, v: str) -> bool:
        return u in self._adj and v in self._adj[u]

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        seen = set()
        edges_dict = {}
        for u in self._adj:
            for v, data in self._adj[u].items():
                edge_key = tuple(sorted((u, v)))
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges_dict[edge_key] = data
        return edges_dict

    def neighbors(self, u: str) -> Iterator[str]:
        if u in self._adj:
            return iter(self._adj[u].keys())
        return iter(())

    def degree(self, u: str) -> int:
        return len(self._adj.get(u, {}))

    def get_edge_data(self, u: str, v: str, default=None):
        return self._adj.get(u, {}).get(v, default)

    def copy(self) -> 'Graph':
        new_g = Graph()
        for n, attrs in self._nodes.items():
            new_g.add_node(n, **dict(attrs))
        for (u, v), attrs in self.edges.items():
            new_g.add_edge(u, v, **dict(attrs))
        return new_g

    def number_of_nodes(self) -> int:
        return len(self._nodes)

    def number_of_edges(self) -> int:
        return sum(len(nbrs) for nbrs in self._adj.values()) // 2

    def __len__(self):
        return len(self._nodes)

    def __iter__(self):
        return iter(self._nodes)

    def __contains__(self, n):
        return n in self._nodes


def connected_components(G: Graph) -> List[Set[str]]:
    visited = set()
    components = []
    for node in G.nodes:
        if node not in visited:
            comp = set()
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                comp.add(curr)
                for nbr in G.neighbors(curr):
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
            components.append(comp)
    return components


def single_source_dijkstra_path_length(G: Graph, source: str, weight: str = "weight") -> Dict[str, float]:
    """Computes shortest path distances from source to all reachable nodes."""
    distances: Dict[str, float] = {source: 0.0}
    pq = [(0.0, source)]
    visited = set()

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        if curr_dist > distances.get(u, float('inf')):
            continue

        for v, edge_data in G._adj.get(u, {}).items():
            w = edge_data.get(weight, 1.0)
            new_dist = curr_dist + w
            if v not in distances or new_dist < distances[v]:
                distances[v] = new_dist
                heapq.heappush(pq, (new_dist, v))

    return distances


def single_source_dijkstra_path(G: Graph, source: str, target: str, weight: str = "weight") -> Tuple[float, List[str]]:
    """Returns (distance, path_nodes) between source and target."""
    distances: Dict[str, float] = {source: 0.0}
    predecessors: Dict[str, Optional[str]] = {source: None}
    pq = [(0.0, source)]
    visited = set()

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if u == target:
            break
        if u in visited:
            continue
        visited.add(u)

        for v, edge_data in G._adj.get(u, {}).items():
            w = edge_data.get(weight, 1.0)
            new_dist = curr_dist + w
            if v not in distances or new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    if target not in distances:
        return float('inf'), []

    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = predecessors[curr]
    path.reverse()
    return distances[target], path


class SpatialIndex2D:
    """Lightweight 2D spatial candidate search for Euclidean neighbor queries."""
    def __init__(self, points: List[Tuple[str, float, float]]):
        self.points = points  # (id, x, y)

    def query_radius(self, x: float, y: float, radius: float) -> List[Tuple[str, float]]:
        results = []
        r2 = radius * radius
        for pid, px, py in self.points:
            dx = px - x
            dy = py - y
            d2 = dx * dx + dy * dy
            if d2 <= r2:
                results.append((pid, math.sqrt(d2)))
        results.sort(key=lambda t: t[1])
        return results
