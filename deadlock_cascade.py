"""
Deadlock Cascade and Queue Spillback Analysis Engine.
Simulates intersection queue accumulation, spillback into upstream junctions,
and demonstrates how grade-separated continuous non-stop bypasses dissolve circular wait deadlocks.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from ..topology.graph_base import Graph


@dataclass
class DeadlockAnalysisResult:
    junction_name: str
    scenario: str
    initial_queue_veh: float
    steady_state_queue_veh: float
    queue_spillback_occurred: bool
    upstream_junctions_blocked: List[str]
    deadlock_detected: bool
    spillback_reduction_percent: float


def simulate_queue_spillback(G: Graph,
                             junction_id: str,
                             inflow_vph: float,
                             outflow_cap_vph: float,
                             link_length_m: float = 350.0,
                             avg_vehicle_spacing_m: float = 7.5,
                             simulation_duration_hours: float = 2.0) -> Dict[str, Any]:
    """
    Simulates temporal queue dynamics at a bottleneck intersection:
    Physical storage capacity = link_length_m / avg_vehicle_spacing_m
    Spillback occurs when queue exceeds physical capacity.
    """
    storage_capacity_veh = link_length_m / avg_vehicle_spacing_m
    net_inflow_rate = inflow_vph - outflow_cap_vph

    # Track queue over time (in 15-minute intervals)
    queue_history = []
    current_queue = 0.0
    spillback = False
    spillback_time_min = None

    steps = int(simulation_duration_hours * 4)  # 15-minute steps
    for step in range(steps):
        t_hrs = (step + 1) * 0.25
        delta_q = net_inflow_rate * 0.25
        current_queue = max(0.0, current_queue + delta_q)

        if current_queue >= storage_capacity_veh:
            spillback = True
            if spillback_time_min is None:
                spillback_time_min = t_hrs * 60.0

        queue_history.append((t_hrs * 60.0, min(current_queue, storage_capacity_veh * 1.5)))

    upstream_neighbors = list(G.neighbors(junction_id)) if G.has_node(junction_id) else []
    blocked_upstream = upstream_neighbors if spillback else []

    return {
        "max_queue_vehicles": round(current_queue, 1),
        "storage_capacity_vehicles": round(storage_capacity_veh, 1),
        "spillback_occurred": spillback,
        "spillback_onset_minutes": spillback_time_min,
        "deadlock_cycle_formed": spillback and len(blocked_upstream) >= 2,
        "blocked_upstream_junctions": blocked_upstream
    }
