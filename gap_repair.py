"""
Topological Gap Healing Module conforming to Section 7 of the Route Resilience specification.
Implements:
- DisjointSet (Union-Find)
- Gated Kruskal MST Gap Repair (Method R4)
- Baseline methods R0 (No repair), R1 (Nearest endpoint no gates), R2 (Gated without Union-Find)
- Hard geometric gates (distance, angular alignment, edge intersection, confidence evidence)
"""

import math
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass, asdict
from .graph_base import Graph, connected_components, SpatialIndex2D


class DisjointSet:
    """Disjoint Set Union (DSU) data structure with path compression and union by rank."""
    def __init__(self, elements: List[str]):
        self.parent: Dict[str, str] = {e: e for e in elements}
        self.rank: Dict[str, int] = {e: 0 for e in elements}

    def find(self, item: str) -> str:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1: str, item2: str) -> bool:
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 == root2:
            return False
        if self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        elif self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
        return True


@dataclass
class GapRepairConfig:
    d_max_m: float = 40.0
    theta_max_deg: float = 45.0
    q_min: float = 0.15
    S_max: float = 0.60
    alpha: float = 0.40
    beta: float = 0.30
    gamma: float = 0.30
    loop_closure: bool = False


@dataclass
class CandidateLink:
    candidate_id: str
    u: str
    v: str
    d_m: float
    theta_u_deg: float
    theta_v_deg: float
    q: float
    score: float
    decision: str = "pending"
    reason: str = ""


def _segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float],
                        p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
    """Checks if line segment p1-p2 strictly intersects line segment p3-p4."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    
    # Check if endpoints are shared
    eps = 1e-6
    if (abs(p1[0]-p3[0]) < eps and abs(p1[1]-p3[1]) < eps) or \
       (abs(p1[0]-p4[0]) < eps and abs(p1[1]-p4[1]) < eps) or \
       (abs(p2[0]-p3[0]) < eps and abs(p2[1]-p3[1]) < eps) or \
       (abs(p2[0]-p4[0]) < eps and abs(p2[1]-p4[1]) < eps):
        return False

    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))


def estimate_outward_vector(G: Graph, endpoint: str) -> Tuple[float, float]:
    """
    Estimates outward direction vector t_u pointing away from the incident road.
    t_u = normalize(pos(endpoint) - pos(neighbor)).
    """
    nbrs = list(G.neighbors(endpoint))
    if not nbrs:
        return (1.0, 0.0)
    nbr = nbrs[0]
    ux, uy = G.nodes[endpoint].get("x", 0.0), G.nodes[endpoint].get("y", 0.0)
    nx, ny = G.nodes[nbr].get("x", 0.0), G.nodes[nbr].get("y", 0.0)
    dx = ux - nx
    dy = uy - ny
    mag = math.hypot(dx, dy)
    if mag > 1e-6:
        return (dx / mag, dy / mag)
    return (1.0, 0.0)


def angle_between_vectors_deg(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Computes angle in degrees [0, 180] between two 2D vectors."""
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    if mag1 < 1e-6 or mag2 < 1e-6:
        return 0.0
    cos_val = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_val))


def generate_candidate_links(G: Graph, endpoints: List[str], cfg: GapRepairConfig, prob_map_func=None) -> List[CandidateLink]:
    """Generates candidate links between endpoints in different components."""
    points = [(n, G.nodes[n].get("x", 0.0), G.nodes[n].get("y", 0.0)) for n in endpoints]
    spatial_idx = SpatialIndex2D(points)
    candidates: List[CandidateLink] = []
    seen_pairs = set()
    cid_counter = 1

    for u in endpoints:
        ux, uy = G.nodes[u].get("x", 0.0), G.nodes[u].get("y", 0.0)
        tu = estimate_outward_vector(G, u)
        nearby = spatial_idx.query_radius(ux, uy, cfg.d_max_m)

        for v, dist in nearby:
            if u == v or dist < 1e-3:
                continue
            pair = tuple(sorted((u, v)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            vx, vy = G.nodes[v].get("x", 0.0), G.nodes[v].get("y", 0.0)
            tv = estimate_outward_vector(G, v)

            # Chord direction u -> v and v -> u
            chord_uv = ((vx - ux) / dist, (vy - uy) / dist)
            chord_vu = (-chord_uv[0], -chord_uv[1])

            theta_u = angle_between_vectors_deg(tu, chord_uv)
            theta_v = angle_between_vectors_deg(tv, chord_vu)

            # Sample road probability evidence q(u, v)
            if prob_map_func is not None:
                q = prob_map_func(ux, uy, vx, vy)
            else:
                # Default synthetic confidence based on node confidence
                q_u = G.nodes[u].get("confidence", 0.8)
                q_v = G.nodes[v].get("confidence", 0.8)
                q = (q_u + q_v) / 2.0

            # Score computation: Eq from Section 7.2
            # S(u, v) = alpha*(d/d_max) + beta*((theta_u + theta_v)/(2*theta_max)) + gamma*(1 - q)
            norm_d = min(1.0, dist / cfg.d_max_m)
            norm_theta = min(1.0, (theta_u + theta_v) / (2.0 * max(1e-3, cfg.theta_max_deg)))
            norm_q = max(0.0, min(1.0, 1.0 - q))
            score = (cfg.alpha * norm_d) + (cfg.beta * norm_theta) + (cfg.gamma * norm_q)

            cand = CandidateLink(
                candidate_id=f"c_{cid_counter:04d}",
                u=u,
                v=v,
                d_m=round(dist, 2),
                theta_u_deg=round(theta_u, 2),
                theta_v_deg=round(theta_v, 2),
                q=round(q, 3),
                score=round(score, 4)
            )
            cid_counter += 1
            candidates.append(cand)

    return candidates


def passes_hard_gates(cand: CandidateLink, G: Graph, cfg: GapRepairConfig) -> Tuple[bool, str]:
    """Applies hard rejection gates (angular alignment, evidence threshold, edge crossing)."""
    # Gate 1: Angular alignment at both endpoints
    if cand.theta_u_deg > cfg.theta_max_deg or cand.theta_v_deg > cfg.theta_max_deg:
        return False, f"exceeded_theta_max (u={cand.theta_u_deg}°, v={cand.theta_v_deg}° > {cfg.theta_max_deg}°)"

    # Gate 2: Road evidence / probability
    if cand.q < cfg.q_min:
        return False, f"insufficient_evidence_q ({cand.q} < {cfg.q_min})"

    # Gate 3: Candidate must not cross existing edges
    pu = (G.nodes[cand.u].get("x", 0.0), G.nodes[cand.u].get("y", 0.0))
    pv = (G.nodes[cand.v].get("x", 0.0), G.nodes[cand.v].get("y", 0.0))
    for (e1, e2) in G.edges:
        if e1 in (cand.u, cand.v) or e2 in (cand.u, cand.v):
            continue
        pe1 = (G.nodes[e1].get("x", 0.0), G.nodes[e1].get("y", 0.0))
        pe2 = (G.nodes[e2].get("x", 0.0), G.nodes[e2].get("y", 0.0))
        if _segments_intersect(pu, pv, pe1, pe2):
            return False, f"crosses_existing_edge ({e1}-{e2})"

    # Gate 4: Score threshold
    if cand.score > cfg.S_max:
        return False, f"score_too_high ({cand.score} > {cfg.S_max})"

    return True, "passed"


def repair_graph_kruskal(G_raw: Graph, cfg: GapRepairConfig, prob_map_func=None) -> Tuple[Graph, List[Dict[str, Any]]]:
    """
    Proposed Gated Kruskal MST Gap Repair (R4).
    Guarantees raw graph is preserved; produces deterministic repaired graph.
    """
    G = G_raw.copy()
    components = connected_components(G)
    uf = DisjointSet(list(G.nodes.keys()))

    endpoints = [n for n in G.nodes if G.degree(n) == 1]
    candidates = generate_candidate_links(G, endpoints, cfg, prob_map_func)

    # Sort candidates by increasing score (lower score = higher plausibility)
    candidates.sort(key=lambda c: c.score)

    used_endpoints: Set[str] = set()
    repair_log: List[Dict[str, Any]] = []

    for c in candidates:
        passed, gate_reason = passes_hard_gates(c, G, cfg)
        if not passed:
            c.decision = "rejected"
            c.reason = gate_reason
            repair_log.append(asdict(c))
            continue

        if not cfg.loop_closure and uf.find(c.u) == uf.find(c.v):
            c.decision = "rejected"
            c.reason = "same_component_loop_closure_disabled"
            repair_log.append(asdict(c))
            continue

        if c.u in used_endpoints or c.v in used_endpoints:
            c.decision = "rejected"
            c.reason = "endpoint_already_repaired"
            repair_log.append(asdict(c))
            continue

        # Accept candidate link
        c.decision = "accepted"
        c.reason = "passed_gates_lowest_score"
        repair_log.append(asdict(c))

        used_endpoints.add(c.u)
        used_endpoints.add(c.v)
        uf.union(c.u, c.v)

        G.add_edge(c.u, c.v,
                   edge_id=f"repaired_{c.candidate_id}",
                   length_m=c.d_m,
                   weight=c.d_m,
                   confidence=c.q,
                   is_repaired=True,
                   repair_score=c.score)

    return G, repair_log


def repair_baseline_r1(G_raw: Graph, cfg: GapRepairConfig) -> Graph:
    """Baseline R1: Nearest endpoint within d_max, no gates."""
    G = G_raw.copy()
    endpoints = [n for n in G.nodes if G.degree(n) == 1]
    for u in endpoints:
        ux, uy = G.nodes[u].get("x", 0.0), G.nodes[u].get("y", 0.0)
        best_v = None
        min_d = float('inf')
        for v in endpoints:
            if u == v:
                continue
            vx, vy = G.nodes[v].get("x", 0.0), G.nodes[v].get("y", 0.0)
            d = math.hypot(vx - ux, vy - uy)
            if d <= cfg.d_max_m and d < min_d:
                min_d = d
                best_v = v
        if best_v and not G.has_edge(u, best_v):
            G.add_edge(u, best_v, length_m=min_d, weight=min_d, is_repaired=True)
    return G


def repair_baseline_r2(G_raw: Graph, cfg: GapRepairConfig) -> Graph:
    """Baseline R2: Gated greedy without Union-Find (allows cycles/redundant links)."""
    G = G_raw.copy()
    endpoints = [n for n in G.nodes if G.degree(n) == 1]
    candidates = generate_candidate_links(G, endpoints, cfg)
    candidates.sort(key=lambda c: c.score)

    for c in candidates:
        passed, _ = passes_hard_gates(c, G, cfg)
        if passed and not G.has_edge(c.u, c.v):
            G.add_edge(c.u, c.v, length_m=c.d_m, weight=c.d_m, is_repaired=True, repair_score=c.score)
    return G
