"""
Evaluation metrics module conforming to Section 9 of the Route Resilience specification.
Implements:
- Connectivity ratio (percentage increase in largest component after repair)
- Relaxed IoU / buffered road segment matching
- Spearman rank correlation for centrality agreement (Brandes' ranking vs reference)
- Top-k bottleneck overlap
- APLS (Average Path Length Similarity) approximation for routable road graphs
"""

import math
from typing import Dict, List, Tuple, Set, Optional, Any
from ..topology.graph_base import Graph, connected_components, single_source_dijkstra_path_length


def compute_connectivity_ratio(G_raw: Graph, G_repaired: Graph, metric: str = "node_count") -> float:
    """
    Computes connectivity ratio:
    Percentage increase in the largest connected component after repair (Section 9.2).
    """
    raw_comps = connected_components(G_raw)
    rep_comps = connected_components(G_repaired)

    if metric == "node_count":
        raw_max = max((len(c) for c in raw_comps), default=0)
        rep_max = max((len(c) for c in rep_comps), default=0)
    else:
        # Total length
        def comp_len(G, comp):
            l = 0.0
            for u in comp:
                for v, ed in G._adj.get(u, {}).items():
                    if u < v and v in comp:
                        l += ed.get("length_m", 1.0)
            return l
        raw_max = max((comp_len(G_raw, c) for c in raw_comps), default=0.0)
        rep_max = max((comp_len(G_repaired, c) for c in rep_comps), default=0.0)

    if raw_max <= 0:
        return 0.0
    return ((rep_max - raw_max) / raw_max) * 100.0


def compute_spearman_rank_correlation(ranks1: Dict[str, float], ranks2: Dict[str, float]) -> float:
    """
    Computes Spearman rank correlation coefficient between two score dictionaries on common keys.
    rho = 1 - (6 * sum(d_i^2)) / (n * (n^2 - 1))
    """
    common_keys = sorted(list(set(ranks1.keys()) & set(ranks2.keys())))
    n = len(common_keys)
    if n <= 1:
        return 1.0

    # Rank assigning
    sorted_1 = sorted(common_keys, key=lambda k: ranks1[k], reverse=True)
    sorted_2 = sorted(common_keys, key=lambda k: ranks2[k], reverse=True)

    r1 = {k: idx + 1 for idx, k in enumerate(sorted_1)}
    r2 = {k: idx + 1 for idx, k in enumerate(sorted_2)}

    d_squared_sum = sum((r1[k] - r2[k]) ** 2 for k in common_keys)
    rho = 1.0 - (6.0 * d_squared_sum) / (n * (n * n - 1))
    return round(rho, 4)


def compute_top_k_overlap(scores1: Dict[str, float], scores2: Dict[str, float], k: int) -> float:
    """Computes Jaccard overlap between top-k elements of two rankings."""
    if not scores1 or not scores2 or k <= 0:
        return 0.0
    top1 = set(sorted(scores1.keys(), key=lambda x: scores1[x], reverse=True)[:k])
    top2 = set(sorted(scores2.keys(), key=lambda x: scores2[x], reverse=True)[:k])
    intersect = len(top1 & top2)
    union = len(top1 | top2)
    return round(intersect / union, 4) if union > 0 else 0.0


def compute_apls_metric(G_ground_truth: Graph, G_extracted: Graph, sample_sources: Optional[List[str]] = None) -> float:
    """
    Computes Average Path Length Similarity (APLS) metric approximation (Section 9.2).
    APLS = 1 - (1/N) * sum |L(s, t)_gt - L(s, t)_ext| / L(s, t)_gt
    """
    nodes = [n for n in G_ground_truth.nodes if G_extracted.has_node(n)]
    if sample_sources is None:
        sample_sources = nodes
    else:
        sample_sources = [s for s in sample_sources if s in nodes]

    if not sample_sources or len(nodes) <= 1:
        return 1.0

    total_diff_ratio = 0.0
    valid_pairs = 0

    for s in sample_sources:
        d_gt = single_source_dijkstra_path_length(G_ground_truth, s, weight="weight")
        d_ext = single_source_dijkstra_path_length(G_extracted, s, weight="weight")
        for t in nodes:
            if s >= t:
                continue
            if t in d_gt and d_gt[t] < float('inf') and d_gt[t] > 0:
                l_gt = d_gt[t]
                l_ext = d_ext.get(t, float('inf'))
                if l_ext == float('inf'):
                    diff_ratio = 1.0  # Max penalty for disconnected pair
                else:
                    diff_ratio = min(1.0, abs(l_gt - l_ext) / l_gt)
                total_diff_ratio += diff_ratio
                valid_pairs += 1

    if valid_pairs == 0:
        return 1.0
    return round(max(0.0, 1.0 - (total_diff_ratio / valid_pairs)), 4)
