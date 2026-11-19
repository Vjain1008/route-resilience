"""
Resilience and Efficiency Analysis Module conforming to Section 8.2 & 8.3 of Route Resilience.
Implements:
- Weighted Global Network Efficiency E(G)
- Resilience Ratios R_eff, R_L, unreachable share U, and efficiency loss %
- Systematic Node Ablation Stress Testing (targeted removal of top-k bottlenecks vs random failure)
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
from ..topology.graph_base import Graph, single_source_dijkstra_path_length
from .centrality import betweenness_centrality


@dataclass
class ResilienceMetrics:
    scenario_id: str
    baseline_efficiency: float
    perturbed_efficiency: float
    R_eff: float
    efficiency_loss_percent: float
    R_L_matched: float
    unreachable_share_U: float
    newly_unreachable_pairs: int
    baseline_components: int
    perturbed_components: int
    disabled_nodes: List[str]


def global_efficiency(G: Graph, nodes: Optional[List[str]] = None, weight: str = "weight") -> float:
    """
    Computes exact weighted global network efficiency:
    E(G) = 1 / [n*(n-1)] * sum_{i != j} (1 / d(i, j))
    where 1 / d(i, j) = 0 if unreachable.
    """
    if nodes is None:
        nodes = list(G.nodes.keys())
    n = len(nodes)
    if n <= 1:
        return 0.0

    total_inv_d = 0.0
    for s in nodes:
        if not G.has_node(s):
            continue
        dist_map = single_source_dijkstra_path_length(G, s, weight=weight)
        for t in nodes:
            if s != t and t in dist_map and dist_map[t] > 0:
                total_inv_d += 1.0 / dist_map[t]

    return total_inv_d / (n * (n - 1))


def evaluate_resilience(G_base: Graph, G_perturbed: Graph,
                        scenario_id: str = "stress_test",
                        disabled_nodes: Optional[List[str]] = None,
                        weight: str = "weight") -> ResilienceMetrics:
    """
    Evaluates network resilience under node/edge disruption based on surviving node set convention.
    """
    if disabled_nodes is None:
        disabled_nodes = []

    # Surviving nodes convention (Section 8.2)
    surviving_nodes = [n for n in G_base.nodes if n not in disabled_nodes and G_perturbed.has_node(n)]
    n = len(surviving_nodes)

    if n <= 1:
        return ResilienceMetrics(
            scenario_id=scenario_id,
            baseline_efficiency=0.0,
            perturbed_efficiency=0.0,
            R_eff=0.0,
            efficiency_loss_percent=100.0,
            R_L_matched=0.0,
            unreachable_share_U=1.0,
            newly_unreachable_pairs=0,
            baseline_components=len(G_base.nodes),
            perturbed_components=0,
            disabled_nodes=disabled_nodes
        )

    # Compute global efficiency on surviving nodes for both graphs
    e_base = global_efficiency(G_base, nodes=surviving_nodes, weight=weight)
    e_pert = global_efficiency(G_perturbed, nodes=surviving_nodes, weight=weight)

    r_eff = (e_pert / e_base) if e_base > 1e-12 else 0.0
    eff_loss = max(0.0, (1.0 - r_eff) * 100.0)

    # Compute path-length ratio on matched pairs and unreachable share U
    base_lengths = []
    pert_lengths = []
    newly_unreachable = 0
    total_pairs_base_reachable = 0

    for s in surviving_nodes:
        d_base = single_source_dijkstra_path_length(G_base, s, weight=weight)
        d_pert = single_source_dijkstra_path_length(G_perturbed, s, weight=weight)
        for t in surviving_nodes:
            if s >= t:
                continue
            base_reach = (t in d_base and d_base[t] < float('inf'))
            pert_reach = (t in d_pert and d_pert[t] < float('inf'))

            if base_reach:
                total_pairs_base_reachable += 1
                if pert_reach:
                    base_lengths.append(d_base[t])
                    pert_lengths.append(d_pert[t])
                else:
                    newly_unreachable += 1

    avg_base_len = (sum(base_lengths) / len(base_lengths)) if base_lengths else 0.0
    avg_pert_len = (sum(pert_lengths) / len(pert_lengths)) if pert_lengths else 0.0
    r_l = (avg_base_len / avg_pert_len) if avg_pert_len > 1e-12 else 0.0
    u_share = (newly_unreachable / total_pairs_base_reachable) if total_pairs_base_reachable > 0 else 0.0

    # Count connected components
    from ..topology.graph_base import connected_components
    base_comps = len(connected_components(G_base))
    pert_comps = len(connected_components(G_perturbed))

    return ResilienceMetrics(
        scenario_id=scenario_id,
        baseline_efficiency=round(e_base, 6),
        perturbed_efficiency=round(e_pert, 6),
        R_eff=round(r_eff, 4),
        efficiency_loss_percent=round(eff_loss, 2),
        R_L_matched=round(r_l, 4),
        unreachable_share_U=round(u_share, 4),
        newly_unreachable_pairs=newly_unreachable,
        baseline_components=base_comps,
        perturbed_components=pert_comps,
        disabled_nodes=disabled_nodes
    )


def simulate_targeted_ablation(G: Graph, top_k: int = 3, weight: str = "weight") -> List[ResilienceMetrics]:
    """
    Scenario S1: Targeted removal of top-k nodes by Betweenness Centrality.
    Simulates sequential structural failure / bottleneck chokepoint closures.
    """
    history = []
    G_curr = G.copy()
    disabled: List[str] = []

    for step in range(1, top_k + 1):
        # Recalculate betweenness to find the highest-impact remaining gatekeeper node
        bc = betweenness_centrality(G_curr, weight=weight)
        if not bc or max(bc.values()) <= 0:
            # Fallback to degree or break
            deg = {n: G_curr.degree(n) for n in G_curr.nodes}
            if not deg:
                break
            target_node = max(deg, key=deg.get)
        else:
            target_node = max(bc, key=bc.get)

        disabled.append(target_node)
        G_curr.remove_node(target_node)

        report = evaluate_resilience(
            G_base=G,
            G_perturbed=G_curr,
            scenario_id=f"ablation_top_{step}",
            disabled_nodes=list(disabled),
            weight=weight
        )
        history.append(report)

    return history
