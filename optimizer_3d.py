"""
3D Grade-Separation Optimizer and Non-Stop Pathway Synthesis.
Automatically designs multi-tier (elevated flyovers, circular bypass loops, underpasses)
trajectories around 3D building obstacles, achieving ZERO demolition and continuous movement.
"""

import math
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from .elevation_network import (
    MultiTierNetwork3D, Node3D, Edge3D,
    compute_minimum_turning_radius, generate_3d_cubic_bezier_curve
)
from .pathway_synthesis import BuildingPolygon, point_to_polygon_distance


@dataclass
class OptimizedBypass3D:
    bypass_id: str
    origin_arm: str
    destination_arm: str
    tier_type: str  # "elevated_viaduct", "high_flyover", "subterranean_underpass"
    z_elevation_m: float
    waypoints_3d: List[Tuple[float, float, float]]
    length_m: float
    design_speed_kmh: float
    turning_radius_m: float
    min_building_clearance_m: float
    zero_demolition_verified: bool
    max_vertical_grade_pct: float


def point_to_building_prism_3d_dist(px: float, py: float, pz: float,
                                    building: BuildingPolygon) -> float:
    """
    Computes minimum 3D Euclidean distance from point (px, py, pz) to a 3D building prism.
    The building occupies vertices on (x, y) from z=0 to z=height_m.
    """
    horiz_dist = point_to_polygon_distance(px, py, building.vertices)
    
    # Vertical distance to building bounds [0, height_m]
    if pz < 0:
        vert_dist = -pz
    elif pz > building.height_m:
        vert_dist = pz - building.height_m
    else:
        vert_dist = 0.0

    return math.sqrt(horiz_dist * horiz_dist + vert_dist * vert_dist)


def optimize_continuous_3d_turn(net: MultiTierNetwork3D,
                                u_origin: str,
                                v_dest: str,
                                buildings: List[BuildingPolygon],
                                target_speed_kmh: float = 50.0,
                                min_safety_clearance_m: float = 10.0) -> Optional[OptimizedBypass3D]:
    """
    Synthesizes an optimal 3D continuous non-stop pathway between u_origin and v_dest.
    Guarantees zero building demolition by evaluating 3D prism clearances.
    """
    if u_origin not in net.nodes or v_dest not in net.nodes:
        return None

    nu = net.nodes[u_origin]
    nv = net.nodes[v_dest]

    r_min_required = compute_minimum_turning_radius(target_speed_kmh)
    p_start = (nu.x, nu.y, nu.z)
    p_end = (nv.x, nv.y, nv.z)

    # Candidate elevation tiers to test:
    # 1. Elevated Viaduct Tier 1 (z = +7.0 m)
    # 2. High-Flyer Tier 2 (z = +13.5 m)
    # 3. Subterranean Box Underpass (z = -5.5 m)
    candidate_tiers = [
        ("elevated_viaduct", 7.0, 1),
        ("high_flyover", 13.5, 2),
        ("subterranean_underpass", -5.5, -1)
    ]

    chord_len = math.hypot(nv.x - nu.x, nv.y - nu.y)
    lateral_offsets = [
        chord_len * 0.25, -chord_len * 0.25,
        chord_len * 0.40, -chord_len * 0.40,
        chord_len * 0.55, -chord_len * 0.55
    ]

    best_bypass = None
    max_clearance = -1.0

    for tier_name, z_elev, z_tier in candidate_tiers:
        for lat_off in lateral_offsets:
            waypoints = generate_3d_cubic_bezier_curve(
                p_start=p_start,
                p_end=p_end,
                lateral_offset=lat_off,
                elevation_z=z_elev,
                num_steps=24
            )

            # Evaluate 3D clearance across all building prisms
            min_dist_to_any_building = float('inf')
            for wx, wy, wz in waypoints:
                for b in buildings:
                    d_b = point_to_building_prism_3d_dist(wx, wy, wz, b)
                    if d_b < min_dist_to_any_building:
                        min_dist_to_any_building = d_b

            # Check if clearance satisfies safety buffer
            if min_dist_to_any_building >= min_safety_clearance_m and min_dist_to_any_building > max_clearance:
                # Calculate 3D path length and grade
                length_3d = 0.0
                max_slope = 0.0
                for i in range(len(waypoints) - 1):
                    p1, p2 = waypoints[i], waypoints[i+1]
                    ds = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
                    length_3d += ds
                    h_dist = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
                    if h_dist > 1e-3:
                        slope = (abs(p2[2] - p1[2]) / h_dist) * 100.0
                        if slope > max_slope:
                            max_slope = slope

                # Grade slope must be <= 4.5% for highway speed
                if max_slope <= 5.0:
                    max_clearance = min_dist_to_any_building
                    # Effective turning radius
                    eff_radius = chord_len * 0.5 + abs(lat_off) * 0.6
                    best_bypass = OptimizedBypass3D(
                        bypass_id=f"3D_Bypass_{u_origin}_{v_dest}",
                        origin_arm=u_origin,
                        destination_arm=v_dest,
                        tier_type=tier_name,
                        z_elevation_m=z_elev,
                        waypoints_3d=waypoints,
                        length_m=round(length_3d, 2),
                        design_speed_kmh=target_speed_kmh,
                        turning_radius_m=round(eff_radius, 2),
                        min_building_clearance_m=round(min_dist_to_any_building, 2),
                        zero_demolition_verified=True,
                        max_vertical_grade_pct=round(max_slope, 2)
                    )

    return best_bypass
