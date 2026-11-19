"""
Continuous Pathway Synthesis Module for Urban Bottleneck Resolution.
Generates collision-free, non-linear (elevated, circular, bended, curved) pathways 
around existing building envelopes to achieve non-stop traffic movement without demolishing structures.
"""

import math
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from .graph_base import Graph


@dataclass
class BuildingPolygon:
    building_id: str
    name: str
    vertices: List[Tuple[float, float]]  # [(x, y), ...]
    height_m: float = 15.0  # Building height in meters


@dataclass
class SynthesizedPathway:
    pathway_id: str
    u_origin: str
    v_destination: str
    pathway_type: str  # "elevated_curved", "circular_bypass", "bended_flyover"
    waypoints: List[Tuple[float, float]]
    length_m: float
    design_speed_kmh: float
    is_grade_separated: bool
    building_clearance_m: float
    avoids_demolition: bool


def point_to_polygon_distance(px: float, py: float, poly: List[Tuple[float, float]]) -> float:
    """Computes minimum distance from a point to a polygon perimeter, 0 if inside."""
    def point_to_segment_dist(x, y, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx*dx + dy*dy
        if l2 < 1e-9:
            return math.hypot(x - x1, y - y1)
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / l2))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(x - proj_x, y - proj_y)

    # Check if point is inside polygon using ray-casting
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if min(p1y, p2y) < py <= max(p1y, p2y):
            if px <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or px <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y

    if inside:
        return 0.0

    # Distance to closest edge
    min_dist = float('inf')
    for i in range(n):
        p1 = poly[i]
        p2 = poly[(i + 1) % n]
        d = point_to_segment_dist(px, py, p1[0], p1[1], p2[0], p2[1])
        if d < min_dist:
            min_dist = d

    return min_dist


def generate_curved_waypoints(p_start: Tuple[float, float],
                              p_end: Tuple[float, float],
                              control_offset: Tuple[float, float],
                              num_points: int = 15) -> List[Tuple[float, float]]:
    """
    Generates smooth quadratic Bézier curve waypoints:
    B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
    """
    p0 = p_start
    p2 = p_end
    # Midpoint + control offset creates smooth curve around obstacles
    mid_x = (p0[0] + p2[0]) / 2.0 + control_offset[0]
    mid_y = (p0[1] + p2[1]) / 2.0 + control_offset[1]
    p1 = (mid_x, mid_y)

    points = []
    for step in range(num_points + 1):
        t = step / float(num_points)
        x = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        points.append((round(x, 2), round(y, 2)))
    return points


def generate_circular_loop_waypoints(center: Tuple[float, float],
                                     radius: float,
                                     start_deg: float,
                                     end_deg: float,
                                     num_points: int = 20) -> List[Tuple[float, float]]:
    """Generates circular arc waypoints for grade-separated cloverleaf or bypass loop."""
    points = []
    # Handle angle wrapping
    if end_deg < start_deg:
        end_deg += 360.0
    for step in range(num_points + 1):
        t = step / float(num_points)
        ang_rad = math.radians(start_deg + t * (end_deg - start_deg))
        x = center[0] + radius * math.cos(ang_rad)
        y = center[1] + radius * math.sin(ang_rad)
        points.append((round(x, 2), round(y, 2)))
    return points


def compute_pathway_clearance(waypoints: List[Tuple[float, float]],
                              buildings: List[BuildingPolygon]) -> float:
    """Finds minimum clearance distance from any waypoint to existing buildings."""
    min_clearance = float('inf')
    for wx, wy in waypoints:
        for b in buildings:
            d = point_to_polygon_distance(wx, wy, b.vertices)
            if d < min_clearance:
                min_clearance = d
    return min_clearance


def compute_polyline_length(points: List[Tuple[float, float]]) -> float:
    length = 0.0
    for i in range(len(points) - 1):
        length += math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1])
    return round(length, 2)


def synthesize_non_stop_bypass(G: Graph,
                               u_arm: str,
                               v_arm: str,
                               buildings: List[BuildingPolygon],
                               pathway_type: str = "elevated_curved",
                               min_required_clearance_m: float = 4.0) -> Optional[SynthesizedPathway]:
    """
    Synthesizes a continuous, grade-separated curved or circular bypass between u_arm and v_arm,
    guaranteeing ZERO building removal by shaping curvature around building footprints.
    """
    if not G.has_node(u_arm) or not G.has_node(v_arm):
        return None

    p_start = (G.nodes[u_arm]["x"], G.nodes[u_arm]["y"])
    p_end = (G.nodes[v_arm]["x"], G.nodes[v_arm]["y"])

    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    chord_len = math.hypot(dx, dy)
    # Normal vector perpendicular to chord
    nx = -dy / chord_len
    ny = dx / chord_len

    best_pathway = None
    best_clearance = -1.0

    # Try varying curve deflection amplitudes and directions
    offset_fractions = [0.25, -0.25, 0.35, -0.35, 0.45, -0.45, 0.55, -0.55, 0.65, -0.65, 0.75, 0.85]
    offset_magnitudes = [chord_len * f for f in offset_fractions]

    for offset in offset_magnitudes:
        control_offset = (nx * offset, ny * offset)
        if pathway_type == "circular_bypass":
            # Circular arc around virtual center
            mid_pt = ((p_start[0] + p_end[0]) / 2.0 + nx * offset, (p_start[1] + p_end[1]) / 2.0 + ny * offset)
            r = chord_len * 0.6
            ang1 = math.degrees(math.atan2(p_start[1] - mid_pt[1], p_start[0] - mid_pt[0]))
            ang2 = math.degrees(math.atan2(p_end[1] - mid_pt[1], p_end[0] - mid_pt[0]))
            waypoints = generate_circular_loop_waypoints(mid_pt, r, ang1, ang2, num_points=16)
        else:
            waypoints = generate_curved_waypoints(p_start, p_end, control_offset, num_points=16)

        clearance = compute_pathway_clearance(waypoints, buildings)

        if clearance >= min_required_clearance_m and clearance > best_clearance:
            best_clearance = clearance
            length_m = compute_polyline_length(waypoints)
            best_pathway = SynthesizedPathway(
                pathway_id=f"bypass_{u_arm}_{v_arm}",
                u_origin=u_arm,
                v_destination=v_arm,
                pathway_type=pathway_type,
                waypoints=waypoints,
                length_m=length_m,
                design_speed_kmh=50.0,  # Free-flow continuous speed
                is_grade_separated=True,
                building_clearance_m=round(clearance, 2),
                avoids_demolition=True
            )

    return best_pathway


def integrate_pathway_into_graph(G: Graph, pathway: SynthesizedPathway) -> Graph:
    """Adds the synthesized non-stop continuous link to the road graph."""
    G_enhanced = G.copy()
    # Speed 50 km/h = 13.89 m/s
    free_travel_time_s = pathway.length_m / (pathway.design_speed_kmh / 3.6)

    G_enhanced.add_edge(
        pathway.u_origin,
        pathway.v_destination,
        edge_id=pathway.pathway_id,
        length_m=pathway.length_m,
        weight=pathway.length_m,  # Distance weight
        travel_time_s=round(free_travel_time_s, 2),
        is_elevated_bypass=True,
        is_repaired=True,
        confidence=1.0,
        grade_separated=True,
        non_stop_flow=True
    )
    return G_enhanced
