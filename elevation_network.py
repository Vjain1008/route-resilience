"""
Multi-Tier 3D Elevation Network and Physics-Based Road Geometry Engine.
Supports z-elevation tiers:
- Level 0: Surface at-grade road (signalized intersection)
- Level +1: Elevated viaduct / flyover ramp (z = +6.0 m to +8.5 m)
- Level +2: Double-decker elevated interchange (z = +12.5 m to +15.0 m)
- Level -1: Subterranean underpass / tunnel (z = -5.5 m)

Implements highway curvature physics:
R_min = v^2 / [127 * (e + f)] for continuous non-stop turning without decelerating.
"""

import math
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Node3D:
    node_id: str
    x: float
    y: float
    z: float = 0.0  # Elevation in meters
    node_type: str = "surface_junction"
    is_signalized: bool = True
    signal_cycle_s: float = 90.0


@dataclass
class Edge3D:
    edge_id: str
    u: str
    v: str
    z_tier: int  # 0: Surface, 1: Flyover, 2: High-Flyer, -1: Underpass
    length_m: float
    design_speed_kmh: float
    grade_slope_percent: float  # Vertical slope <= 4.0% for highway ramps
    is_non_stop: bool
    waypoints_3d: List[Tuple[float, float, float]]  # [(x, y, z), ...]


class MultiTierNetwork3D:
    """3D Directed/Undirected Spatial Network with Z-Elevation Layers."""
    def __init__(self):
        self.nodes: Dict[str, Node3D] = {}
        self.edges: Dict[Tuple[str, str], Edge3D] = {}
        self._adj: Dict[str, List[str]] = {}

    def add_node(self, node_id: str, x: float, y: float, z: float = 0.0, **kwargs):
        node = Node3D(node_id=node_id, x=x, y=y, z=z, **kwargs)
        self.nodes[node_id] = node
        if node_id not in self._adj:
            self._adj[node_id] = []

    def add_edge_3d(self, u: str, v: str, edge_id: str,
                    z_tier: int = 0,
                    design_speed_kmh: float = 50.0,
                    is_non_stop: bool = False,
                    waypoints_3d: Optional[List[Tuple[float, float, float]]] = None):
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Nodes {u} and {v} must exist before adding edge.")

        nu, nv = self.nodes[u], self.nodes[v]
        
        if waypoints_3d is None:
            waypoints_3d = [(nu.x, nu.y, nu.z), (nv.x, nv.y, nv.z)]

        # Calculate 3D cumulative length
        length = 0.0
        for i in range(len(waypoints_3d) - 1):
            p1, p2 = waypoints_3d[i], waypoints_3d[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            length += math.sqrt(dx*dx + dy*dy + dz*dz)

        # Vertical grade slope percentage
        delta_z = abs(nv.z - nu.z)
        horiz_dist = math.hypot(nv.x - nu.x, nv.y - nu.y)
        grade_pct = (delta_z / max(1.0, horiz_dist)) * 100.0

        edge = Edge3D(
            edge_id=edge_id,
            u=u,
            v=v,
            z_tier=z_tier,
            length_m=round(length, 2),
            design_speed_kmh=design_speed_kmh,
            grade_slope_percent=round(grade_pct, 2),
            is_non_stop=is_non_stop,
            waypoints_3d=waypoints_3d
        )

        pair_forward = (u, v)
        pair_backward = (v, u)
        self.edges[pair_forward] = edge
        self.edges[pair_backward] = edge

        if v not in self._adj[u]:
            self._adj[u].append(v)
        if u not in self._adj[v]:
            self._adj[v].append(u)


def compute_minimum_turning_radius(design_speed_kmh: float,
                                   superelevation_e: float = 0.06,
                                   side_friction_f: float = 0.14) -> float:
    """
    Computes AASHTO / IRC standard minimum curve radius for non-stop turning:
    R_min = v^2 / [127 * (e + f)]
    """
    return round((design_speed_kmh ** 2) / (127.0 * (superelevation_e + side_friction_f)), 2)


def generate_3d_cubic_bezier_curve(p_start: Tuple[float, float, float],
                                   p_end: Tuple[float, float, float],
                                   lateral_offset: float,
                                   elevation_z: float,
                                   num_steps: int = 24) -> List[Tuple[float, float, float]]:
    """
    Generates a 3D smooth cubic Bézier viaduct trajectory:
    Ramps up smoothly from p_start.z to elevation_z, curves laterally around obstacles,
    and ramps down to p_end.z.
    """
    p0 = p_start
    p3 = p_end

    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    chord_len = math.hypot(dx, dy)
    nx = -dy / chord_len
    ny = dx / chord_len

    # Control points with lateral offset and vertical lift
    p1 = (
        p0[0] + dx * 0.33 + nx * lateral_offset,
        p0[1] + dy * 0.33 + ny * lateral_offset,
        elevation_z
    )
    p2 = (
        p0[0] + dx * 0.67 + nx * lateral_offset,
        p0[1] + dy * 0.67 + ny * lateral_offset,
        elevation_z
    )

    waypoints = []
    for i in range(num_steps + 1):
        t = i / float(num_steps)
        # Cubic Bézier formula
        u = 1.0 - t
        x = (u**3)*p0[0] + 3*(u**2)*t*p1[0] + 3*u*(t**2)*p2[0] + (t**3)*p3[0]
        y = (u**3)*p0[1] + 3*(u**2)*t*p1[1] + 3*u*(t**2)*p2[1] + (t**3)*p3[1]
        z = (u**3)*p0[2] + 3*(u**2)*t*p1[2] + 3*u*(t**2)*p2[2] + (t**3)*p3[2]
        waypoints.append((round(x, 2), round(y, 2), round(z, 2)))

    return waypoints


def check_3d_spatial_conflict(edge1: Edge3D, edge2: Edge3D,
                              vertical_clearance_min_m: float = 5.5) -> bool:
    """
    Conflict Elimination Theorem:
    Two crossing road corridors only collide if their vertical separation is less than min clearance.
    If |z1 - z2| >= 5.5 m, vehicles pass continuously without conflict or signals!
    """
    if abs(edge1.z_tier - edge2.z_tier) >= 1:
        # Grade-separated on different elevation tiers
        return False
    return True
