"""
Traffic Flow Simulation and Congestion Reduction Analysis.
Uses Bureau of Public Roads (BPR) delay curves and Webster intersection delay
to evaluate the traffic impact of non-stop continuous elevated/curved turn bypasses.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
import math
from ..topology.graph_base import Graph, single_source_dijkstra_path


@dataclass
class TrafficSimulationResult:
    junction_name: str
    scenario: str
    total_vehicle_seconds: float
    avg_trip_duration_s: float
    congestion_delay_veh_hours: float
    bottleneck_vc_ratio: float
    total_demand_vph: float
    non_stop_volume_vph: float
    non_stop_share: float


def compute_bpr_travel_time(free_time_s: float, volume_vph: float, capacity_vph: float,
                            alpha: float = 0.15, beta: float = 4.0) -> float:
    """
    Standard Bureau of Public Roads (BPR) travel time function:
    T = T0 * (1 + alpha * (V / C)^beta)
    """
    vc = volume_vph / max(1.0, capacity_vph)
    return free_time_s * (1.0 + alpha * (vc ** beta))


def simulate_junction_traffic(G: Graph,
                              origin_nodes: List[str],
                              dest_nodes: List[str],
                              demand_matrix_vph: Dict[Tuple[str, str], float],
                              bottleneck_nodes: List[str],
                              has_non_stop_bypass: bool = False,
                              signal_wait_time_s: float = 75.0) -> Dict[str, Any]:
    """
    Simulates traffic assignment and congestion across the junction network.
    Routes OD pairs along shortest paths and computes link volumes and BPR delays.
    """
    # Capacities (vehicles per hour)
    surface_capacity = 1200.0
    elevated_bypass_capacity = 2200.0

    # Initialize link volumes for all edges in G
    link_volumes: Dict[Tuple[str, str], float] = {tuple(sorted((u, v))): 0.0 for (u, v) in G.edges}
    bottleneck_demand = 0.0
    bypass_demand = 0.0

    # Assign demand along paths (routing by estimated travel time)
    for (orig, dest), vol in demand_matrix_vph.items():
        if not G.has_node(orig) or not G.has_node(dest):
            continue

        # Find route using travel_time_s if available, fallback to length_m/weight
        cost_key = "travel_time_s" if any("travel_time_s" in d for d in G.edges.values()) else "weight"
        dist, path = single_source_dijkstra_path(G, orig, dest, weight=cost_key)
        if not path or len(path) < 2:
            continue

        # Traverse path edges and accumulate volume
        used_bypass = False
        for i in range(len(path) - 1):
            edge_key = tuple(sorted((path[i], path[i+1])))
            link_volumes[edge_key] = link_volumes.get(edge_key, 0.0) + vol
            edge_data = G.get_edge_data(path[i], path[i+1], {})
            if edge_data.get("non_stop_flow", False):
                used_bypass = True

        if used_bypass:
            bypass_demand += vol
        else:
            bottleneck_demand += vol

    # Compute travel times on all links
    total_vehicle_seconds = 0.0
    total_free_flow_seconds = 0.0
    total_demand = sum(demand_matrix_vph.values())

    for (u, v), edge_data in G.edges.items():
        vol = link_volumes.get(tuple(sorted((u, v))), 0.0)
        length_m = edge_data.get("length_m", 100.0)
        is_bypass = edge_data.get("non_stop_flow", False)

        if is_bypass:
            speed_mps = 50.0 / 3.6  # 50 km/h design speed
            t0 = length_m / speed_mps
            cap = elevated_bypass_capacity
            link_time = compute_bpr_travel_time(t0, vol, cap)  # Free flow, ZERO signal delay
        else:
            speed_mps = 20.0 / 3.6  # 20 km/h congested surface speed
            t0 = length_m / speed_mps
            cap = surface_capacity
            # Signal delay applied at at-grade intersections
            is_at_bottleneck = (u in bottleneck_nodes or v in bottleneck_nodes)
            sig_delay = signal_wait_time_s if is_at_bottleneck else 0.0
            link_time = compute_bpr_travel_time(t0, vol, cap) + sig_delay

        total_vehicle_seconds += vol * link_time
        total_free_flow_seconds += vol * t0

    total_congestion_delay_veh_hours = max(0.0, (total_vehicle_seconds - total_free_flow_seconds) / 3600.0)
    avg_trip_sec = (total_vehicle_seconds / total_demand) if total_demand > 0 else 0.0
    effective_bottleneck_cap = surface_capacity * max(1, len(bottleneck_nodes))
    bottleneck_vc = (bottleneck_demand / effective_bottleneck_cap)
    non_stop_share = (bypass_demand / total_demand) if total_demand > 0 else 0.0

    return {
        "total_vehicle_seconds": round(total_vehicle_seconds, 2),
        "avg_trip_duration_s": round(avg_trip_sec, 2),
        "congestion_delay_veh_hours": round(total_congestion_delay_veh_hours, 2),
        "bottleneck_vc_ratio": round(bottleneck_vc, 3),
        "total_demand_vph": round(total_demand, 1),
        "non_stop_volume_vph": round(bypass_demand, 1),
        "non_stop_share": round(non_stop_share * 100.0, 1)
    }
