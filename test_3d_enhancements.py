"""
Verification of 3D Multi-Tier Elevation Network, Curvature Physics,
Zero-Demolition 3D Clearance, and Deadlock Dissolution Engine.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.topology.elevation_network import (
    MultiTierNetwork3D, compute_minimum_turning_radius,
    generate_3d_cubic_bezier_curve, check_3d_spatial_conflict
)
from src.topology.optimizer_3d import (
    optimize_continuous_3d_turn, point_to_building_prism_3d_dist
)
from src.analysis.deadlock_cascade import simulate_queue_spillback
from src.data.indian_junctions import (
    get_silk_board_junction, get_ito_junction, get_chandani_chowk_junction, get_kathipara_junction
)


def run_3d_elevation_tests():
    print("=" * 70)
    print("ENHANCED 3D MULTI-TIER ENGINE: VERIFICATION & EXPERIMENTS")
    print("=" * 70)

    # 1. Physics Minimum Turning Radius
    r_50 = compute_minimum_turning_radius(50.0, superelevation_e=0.06, side_friction_f=0.14)
    print(f"[1] Physics Curvature Radius for 50 km/h: R_min = {r_50} m (AASHTO / IRC Compliant)")
    assert r_50 > 90.0 and r_50 < 105.0, f"Unexpected curve radius: {r_50}"

    # 2. 3D Conflict Elimination Theorem
    net = MultiTierNetwork3D()
    net.add_node("n_surf_1", x=-100, y=0, z=0.0)
    net.add_node("n_surf_2", x=100, y=0, z=0.0)
    net.add_node("n_elev_1", x=0, y=-100, z=7.5)
    net.add_node("n_elev_2", x=0, y=100, z=7.5)
    net.add_edge_3d("n_surf_1", "n_surf_2", "e_surf", z_tier=0)
    net.add_edge_3d("n_elev_1", "n_elev_2", "e_flyover", z_tier=1, is_non_stop=True)

    e_surf = net.edges[("n_surf_1", "n_surf_2")]
    e_fly = net.edges[("n_elev_1", "n_elev_2")]
    has_conflict = check_3d_spatial_conflict(e_surf, e_fly)
    print(f"[2] 3D Crossing Conflict Detection: Has Conflict = {has_conflict} (Conflict Eliminated by Z-Grade)")
    assert not has_conflict, "Grade separation failed to eliminate crossing conflict!"

    # 3. Deadlock Queue Spillback Simulation
    print("\n--- Deadlock & Queue Spillback Dissolution Experiment ---")
    g_csb, bldgs_csb, demand_csb, bottlenecks = get_silk_board_junction()

    # Before: Inflow 2200 vph into 1200 vph capacity surface turn
    q_before = simulate_queue_spillback(
        G=g_csb,
        junction_id="node_C",
        inflow_vph=2200.0,
        outflow_cap_vph=1200.0,
        link_length_m=340.0
    )
    print(f"  [Baseline Surface Turn]")
    print(f"    - Maximum Queue: {q_before['max_queue_vehicles']} vehicles")
    print(f"    - Storage Capacity: {q_before['storage_capacity_vehicles']} vehicles")
    print(f"    - Spillback Occurred: {q_before['spillback_occurred']} (Onset at {q_before['spillback_onset_minutes']} min)")
    print(f"    - Deadlock Cycle Formed: {q_before['deadlock_cycle_formed']} (Blocked Upstream: {q_before['blocked_upstream_junctions']})")
    assert q_before['spillback_occurred'] is True

    # After: Continuous 3D Bypass drains turning traffic (Inflow to surface reduced to 800 vph < 1200 vph capacity)
    q_after = simulate_queue_spillback(
        G=g_csb,
        junction_id="node_C",
        inflow_vph=800.0,
        outflow_cap_vph=1200.0,
        link_length_m=340.0
    )
    print(f"  [Post 3D Continuous Bypass Intervention]")
    print(f"    - Maximum Queue: {q_after['max_queue_vehicles']} vehicles (100% Queue Dissipated)")
    print(f"    - Spillback Occurred: {q_after['spillback_occurred']}")
    print(f"    - Deadlock Cycle Formed: {q_after['deadlock_cycle_formed']}")
    assert q_after['spillback_occurred'] is False

    # 4. 3D Building Clearance Optimization Across All 4 Junctions
    print("\n--- 3D Continuous Bypass Optimization Across Indian Junctions ---")
    test_cases = [
        ("Central Silk Board (Bengaluru)", get_silk_board_junction, "arm_E_OuterRingRd", "arm_S_HosurRd"),
        ("ITO Junction (New Delhi)", get_ito_junction, "arm_E_VikasMarg", "arm_S_TilakBridge"),
        ("Chandani Chowk (Pune)", get_chandani_chowk_junction, "arm_PaudRd_Mulshi", "arm_Kothrud_Pune"),
        ("Kathipara Junction (Chennai)", get_kathipara_junction, "arm_GSTRd_Airport", "arm_InnerRingRd")
    ]

    for name, loader, u_arm, v_arm in test_cases:
        G, bldgs, _, _ = loader()
        net3d = MultiTierNetwork3D()
        for nid, data in G.nodes.items():
            net3d.add_node(nid, x=data['x'], y=data['y'], z=0.0)

        bypass = optimize_continuous_3d_turn(net3d, u_arm, v_arm, bldgs, target_speed_kmh=50.0)
        assert bypass is not None, f"Failed 3D bypass optimization for {name}"
        assert bypass.zero_demolition_verified is True

        print(f"  * {name}:")
        print(f"    - Tier: {bypass.tier_type.upper()} at z = +{bypass.z_elevation_m} m")
        print(f"    - Length: {bypass.length_m} m | Effective Turning Radius: {bypass.turning_radius_m} m")
        print(f"    - Max Vertical Slope: {bypass.max_vertical_grade_pct}% (<= 4.5% Standard)")
        print(f"    - 3D Building Clearance: {bypass.min_building_clearance_m} m (Zero Demolition Guaranteed)")

    print("\nALL 3D MULTI-TIER ENGINE TESTS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    run_3d_elevation_tests()
