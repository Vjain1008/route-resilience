"""
Comprehensive Test Suite for Route Resilience System.
Covers:
1. Section 13.1 Known-Value Unit Tests from Specification
2. Indian Urban Junction Benchmark & Non-Stop Turn Movement Experiments
   (Silk Board, ITO, Chandani Chowk, Kathipara)
"""

import sys
import os
import math
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.topology.graph_base import Graph
from src.topology.gap_repair import (
    GapRepairConfig, repair_graph_kruskal, repair_baseline_r1, repair_baseline_r2,
    _segments_intersect, CandidateLink, passes_hard_gates
)
from src.topology.pathway_synthesis import (
    synthesize_non_stop_bypass, integrate_pathway_into_graph, BuildingPolygon
)
from src.analysis.centrality import (
    betweenness_centrality, degree_centrality, closeness_centrality
)
from src.analysis.resilience import (
    global_efficiency, evaluate_resilience, simulate_targeted_ablation
)
from src.analysis.traffic_simulation import simulate_junction_traffic
from src.evaluation.metrics import (
    compute_connectivity_ratio, compute_spearman_rank_correlation, compute_top_k_overlap
)
from src.data.indian_junctions import (
    get_silk_board_junction, get_ito_junction, get_chandani_chowk_junction, get_kathipara_junction
)


def run_known_value_unit_tests():
    print("=" * 70)
    print("SECTION 13.1: KNOWN-VALUE UNIT TESTS")
    print("=" * 70)
    passed = 0
    total = 0

    # 1. Betweenness on a path (3 nodes a-b-c, unweighted -> node b has normalized betweenness 1.0)
    total += 1
    g1 = Graph()
    g1.add_edge("a", "b", weight=1.0)
    g1.add_edge("b", "c", weight=1.0)
    bc1 = betweenness_centrality(g1, weight=None, normalized=True)
    assert abs(bc1["b"] - 1.0) < 1e-6 and abs(bc1["a"] - 0.0) < 1e-6, f"Failed BC on path: {bc1}"
    print(f"[{total}/12] PASSED: Betweenness on path (node b = {bc1['b']:.2f})")
    passed += 1

    # 2. Efficiency on a path (Same graph -> E = 5/6, about 0.833)
    total += 1
    e1 = global_efficiency(g1, weight="weight")
    expected_e = 5.0 / 6.0
    assert abs(e1 - expected_e) < 1e-4, f"Failed efficiency on path: got {e1}, expected {expected_e}"
    print(f"[{total}/12] PASSED: Efficiency on path (E = {e1:.4f}, expected {expected_e:.4f})")
    passed += 1

    # 3. Closure disconnects (Remove node b from path -> Surviving nodes a and c are unreachable; E = 0, R_eff = 0)
    total += 1
    g1_perturbed = g1.copy()
    g1_perturbed.remove_node("b")
    res1 = evaluate_resilience(g1, g1_perturbed, disabled_nodes=["b"], weight="weight")
    assert abs(res1.perturbed_efficiency - 0.0) < 1e-6 and abs(res1.R_eff - 0.0) < 1e-6
    print(f"[{total}/12] PASSED: Closure disconnects (perturbed E = {res1.perturbed_efficiency:.2f}, R_eff = {res1.R_eff:.2f})")
    passed += 1

    # 4. Complete graph (Any n, unit weights -> E = 1)
    total += 1
    g_k4 = Graph()
    k_nodes = ["n1", "n2", "n3", "n4"]
    for i in range(len(k_nodes)):
        for j in range(i + 1, len(k_nodes)):
            g_k4.add_edge(k_nodes[i], k_nodes[j], weight=1.0)
    e_k4 = global_efficiency(g_k4, weight="weight")
    assert abs(e_k4 - 1.0) < 1e-6, f"Failed complete graph efficiency: got {e_k4}"
    print(f"[{total}/12] PASSED: Complete graph efficiency (E = {e_k4:.4f})")
    passed += 1

    # 5. Weights respected (Two routes with different lengths -> efficiency uses shorter weighted route)
    total += 1
    g_weights = Graph()
    g_weights.add_edge("s", "x", weight=10.0)
    g_weights.add_edge("x", "t", weight=10.0)  # path s-x-t length 20
    g_weights.add_edge("s", "y", weight=1.0)
    g_weights.add_edge("y", "t", weight=1.0)   # path s-y-t length 2
    from src.topology.graph_base import single_source_dijkstra_path_length
    dist_s = single_source_dijkstra_path_length(g_weights, "s", weight="weight")
    assert dist_s["t"] == 2.0, f"Failed weighted path: expected 2.0, got {dist_s['t']}"
    print(f"[{total}/12] PASSED: Weights respected (shortest distance s-t = {dist_s['t']:.1f})")
    passed += 1

    # 6. Repair accepts collinear endpoints 10 m apart
    total += 1
    cfg = GapRepairConfig(d_max_m=40.0, theta_max_deg=45.0, q_min=0.15, S_max=0.60)
    g_collinear = Graph()
    g_collinear.add_node("u0", x=0.0, y=0.0)
    g_collinear.add_node("u", x=50.0, y=0.0, confidence=0.9)
    g_collinear.add_edge("u0", "u", length_m=50.0)
    g_collinear.add_node("v", x=60.0, y=0.0, confidence=0.9)
    g_collinear.add_node("v0", x=110.0, y=0.0)
    g_collinear.add_edge("v", "v0", length_m=50.0)
    g_repaired, r_log = repair_graph_kruskal(g_collinear, cfg)
    assert g_repaired.has_edge("u", "v"), "Failed collinear endpoints repair acceptance"
    print(f"[{total}/12] PASSED: Repair accepts collinear endpoints 10 m apart (accepted)")
    passed += 1

    # 7. Repair rejects angle (Perpendicular endpoints)
    total += 1
    g_perp = Graph()
    g_perp.add_node("u0", x=0.0, y=0.0)
    g_perp.add_node("u", x=50.0, y=0.0, confidence=0.9)
    g_perp.add_edge("u0", "u", length_m=50.0)
    # v is placed at 90-degree perpendicular angle relative to u's tangent
    g_perp.add_node("v", x=50.0, y=25.0, confidence=0.9)
    g_perp.add_node("v0", x=80.0, y=25.0)
    g_perp.add_edge("v", "v0", length_m=30.0)
    g_perp_rep, r_perp_log = repair_graph_kruskal(g_perp, cfg)
    assert not g_perp_rep.has_edge("u", "v"), "Failed perpendicular endpoints rejection"
    print(f"[{total}/12] PASSED: Repair rejects perpendicular endpoints (rejected by theta gate)")
    passed += 1

    # 8. Repair rejects distance (Collinear endpoints beyond d_max)
    total += 1
    g_far = Graph()
    g_far.add_node("u0", x=0.0, y=0.0)
    g_far.add_node("u", x=50.0, y=0.0, confidence=0.9)
    g_far.add_edge("u0", "u", length_m=50.0)
    g_far.add_node("v", x=105.0, y=0.0, confidence=0.9)  # 55 m > d_max (40 m)
    g_far.add_node("v0", x=155.0, y=0.0)
    g_far.add_edge("v", "v0", length_m=50.0)
    g_far_rep, _ = repair_graph_kruskal(g_far, cfg)
    assert not g_far_rep.has_edge("u", "v"), "Failed distance rejection"
    print(f"[{total}/12] PASSED: Repair rejects collinear endpoints beyond d_max (dist 55m > 40m)")
    passed += 1

    # 9. Repair rejects crossing (Candidate crosses an existing edge)
    total += 1
    g_cross = Graph()
    g_cross.add_node("u0", x=0.0, y=0.0)
    g_cross.add_node("u", x=30.0, y=0.0, confidence=0.9)
    g_cross.add_edge("u0", "u", length_m=30.0)
    g_cross.add_node("v", x=60.0, y=0.0, confidence=0.9)
    g_cross.add_node("v0", x=90.0, y=0.0)
    g_cross.add_edge("v", "v0", length_m=30.0)
    # Blocking vertical road across x=45
    g_cross.add_node("b1", x=45.0, y=-20.0)
    g_cross.add_node("b2", x=45.0, y=20.0)
    g_cross.add_edge("b1", "b2", length_m=40.0)
    g_cross_rep, cross_log = repair_graph_kruskal(g_cross, cfg)
    assert not g_cross_rep.has_edge("u", "v"), "Failed crossing edge rejection"
    print(f"[{total}/12] PASSED: Repair rejects candidate crossing existing edge")
    passed += 1

    # 10. One link per endpoint (Three mutually close endpoints)
    total += 1
    g_three = Graph()
    g_three.add_node("u0", x=0.0, y=0.0)
    g_three.add_node("u", x=40.0, y=0.0, confidence=0.9)
    g_three.add_edge("u0", "u", length_m=40.0)
    g_three.add_node("v1", x=50.0, y=2.0, confidence=0.9)
    g_three.add_node("v1_end", x=80.0, y=2.0)
    g_three.add_edge("v1", "v1_end", length_m=30.0)
    g_three.add_node("v2", x=50.0, y=-2.0, confidence=0.9)
    g_three.add_node("v2_end", x=80.0, y=-2.0)
    g_three.add_edge("v2", "v2_end", length_m=30.0)
    g_three_rep, _ = repair_graph_kruskal(g_three, cfg)
    u_rep_count = sum(1 for nbr in g_three_rep.neighbors("u") if g_three_rep.get_edge_data("u", nbr).get("is_repaired", False))
    assert u_rep_count == 1, f"Expected exactly 1 repair for endpoint u, got {u_rep_count}"
    print(f"[{total}/12] PASSED: One link per endpoint enforced (connected: {u_rep_count})")
    passed += 1

    # 11. Raw preserved (Run repair -> Raw graph unchanged)
    total += 1
    num_edges_raw_before = g_collinear.number_of_edges()
    _ = repair_graph_kruskal(g_collinear, cfg)
    assert g_collinear.number_of_edges() == num_edges_raw_before, "Raw graph was mutated!"
    print(f"[{total}/12] PASSED: Raw graph preserved immutably")
    passed += 1

    # 12. Determinism (Same seed and config twice -> Identical outputs)
    total += 1
    g_rep_1, log_1 = repair_graph_kruskal(g_collinear, cfg)
    g_rep_2, log_2 = repair_graph_kruskal(g_collinear, cfg)
    assert g_rep_1.edges == g_rep_2.edges and log_1 == log_2, "Non-deterministic repair output!"
    print(f"[{total}/12] PASSED: Determinism verified (identical output on repeated runs)")
    passed += 1

    print("\nALL 12/12 UNIT TESTS PASSED SUCCESSFULLY!\n")


def run_indian_junction_experiments():
    print("=" * 70)
    print("INDIAN URBAN JUNCTIONS: ROUTE RESILIENCE & NON-STOP TURN FACILITATION")
    print("=" * 70)

    junctions = [
        ("Central Silk Board Junction (Bengaluru)", get_silk_board_junction,
         ("arm_E_OuterRingRd", "arm_S_HosurRd"), "elevated_curved"),
        ("ITO Junction (New Delhi)", get_ito_junction,
         ("arm_E_VikasMarg", "arm_S_TilakBridge"), "bended_flyover"),
        ("Chandani Chowk (Pune)", get_chandani_chowk_junction,
         ("arm_PaudRd_Mulshi", "arm_Kothrud_Pune"), "elevated_curved"),
        ("Kathipara Junction (Chennai)", get_kathipara_junction,
         ("arm_GSTRd_Airport", "arm_InnerRingRd"), "circular_bypass")
    ]

    all_results = []

    for name, loader, critical_turn, bypass_type in junctions:
        print(f"\n--- Testing Junction: {name} ---")
        G_raw, buildings, demand, bottleneck_nodes = loader()

        # Step 1: Structural Criticality
        bc = betweenness_centrality(G_raw, weight="weight")
        top_node = max(bc, key=bc.get)
        base_eff = global_efficiency(G_raw, weight="weight")
        print(f"  [1] Critical Gatekeeper Node Identified: '{top_node}' with Betweenness = {bc[top_node]:.4f}")
        print(f"      Baseline Network Global Efficiency E(G) = {base_eff:.6f}")

        # Step 2: Stress-Test / Bottleneck Failure Simulation (Disaster / Flood / Chokepoint Gridlock)
        G_perturbed = G_raw.copy()
        G_perturbed.remove_node(top_node)
        res_report = evaluate_resilience(G_raw, G_perturbed, scenario_id=f"failure_{top_node}", disabled_nodes=[top_node])
        print(f"  [2] Stress Test (Complete Failure of Gatekeeper '{top_node}'):")
        print(f"      - Perturbed Efficiency E(G'): {res_report.perturbed_efficiency:.6f}")
        print(f"      - Efficiency Loss: {res_report.efficiency_loss_percent:.2f}%")
        print(f"      - Unreachable Pair Share U: {res_report.unreachable_share_U * 100:.1f}%")
        print(f"      - Components: {res_report.baseline_components} -> {res_report.perturbed_components}")

        # Step 3: Synthesis of Non-Stop Continuous Bypass without Building Demolition
        u_turn, v_turn = critical_turn
        print(f"  [3] Synthesizing Non-Stop Continuous Turn: {u_turn} -> {v_turn}")
        pathway = synthesize_non_stop_bypass(
            G=G_raw,
            u_arm=u_turn,
            v_arm=v_turn,
            buildings=buildings,
            pathway_type=bypass_type,
            min_required_clearance_m=4.0
        )
        assert pathway is not None, f"Failed to synthesize pathway for {name}"
        assert pathway.avoids_demolition is True
        print(f"      - Geometry: {pathway.pathway_type.upper()}")
        print(f"      - Length: {pathway.length_m} m | Design Speed: {pathway.design_speed_kmh} km/h")
        print(f"      - Building Demolition: ZERO (Maintained clearance of {pathway.building_clearance_m} m from all structures)")
        for b in buildings:
            from src.topology.pathway_synthesis import point_to_polygon_distance
            d_b = min(point_to_polygon_distance(w[0], w[1], b.vertices) for w in pathway.waypoints)
            print(f"        * Clearance to '{b.name}': {d_b:.1f} m [Preserved intact]")

        # Step 4: Traffic Congestion & Non-Stop Flow Simulation (Before vs After)
        G_enhanced = integrate_pathway_into_graph(G_raw, pathway)
        
        sim_before = simulate_junction_traffic(
            G=G_raw,
            origin_nodes=[critical_turn[0]],
            dest_nodes=[critical_turn[1]],
            demand_matrix_vph=demand,
            bottleneck_nodes=bottleneck_nodes,
            has_non_stop_bypass=False,
            signal_wait_time_s=90.0
        )

        sim_after = simulate_junction_traffic(
            G=G_enhanced,
            origin_nodes=[critical_turn[0]],
            dest_nodes=[critical_turn[1]],
            demand_matrix_vph=demand,
            bottleneck_nodes=bottleneck_nodes,
            has_non_stop_bypass=True,
            signal_wait_time_s=90.0
        )

        cong_reduction = ((sim_before["total_vehicle_seconds"] - sim_after["total_vehicle_seconds"]) /
                          sim_before["total_vehicle_seconds"]) * 100.0
        eff_enhanced = global_efficiency(G_enhanced, weight="weight")
        resilience_gain = ((eff_enhanced - base_eff) / base_eff) * 100.0

        print(f"  [4] Traffic Simulation & Congestion Impact:")
        print(f"      - Baseline Average Trip Duration: {sim_before['avg_trip_duration_s']:.1f} s (Congestion delay: {sim_before['congestion_delay_veh_hours']:.1f} veh-hrs)")
        print(f"      - Post-Intervention Trip Duration: {sim_after['avg_trip_duration_s']:.1f} s (Congestion delay: {sim_after['congestion_delay_veh_hours']:.1f} veh-hrs)")
        print(f"      - Bottleneck Volume/Capacity (V/C): {sim_before['bottleneck_vc_ratio']:.2f} -> {sim_after['bottleneck_vc_ratio']:.2f}")
        print(f"      - Congestion Reduction: {cong_reduction:.2f}%")
        print(f"      - Non-Stop Diverted Flow Share: {sim_after['non_stop_share']:.1f}%")
        print(f"      - Network Resilience Improvement: +{resilience_gain:.2f}%")

        all_results.append({
            "junction": name,
            "gatekeeper_node": top_node,
            "betweenness": bc[top_node],
            "baseline_efficiency": base_eff,
            "stress_test_loss_percent": res_report.efficiency_loss_percent,
            "unreachable_share": res_report.unreachable_share_U,
            "critical_turn": f"{u_turn} -> {v_turn}",
            "bypass_type": pathway.pathway_type,
            "pathway_length_m": pathway.length_m,
            "min_building_clearance_m": pathway.building_clearance_m,
            "buildings_demolished": 0,
            "before_trip_duration_s": sim_before["avg_trip_duration_s"],
            "after_trip_duration_s": sim_after["avg_trip_duration_s"],
            "congestion_reduction_percent": round(cong_reduction, 2),
            "non_stop_flow_share_percent": sim_after["non_stop_share"],
            "resilience_gain_percent": round(resilience_gain, 2)
        })

    # Save test results to JSON
    os.makedirs("outputs/reports", exist_ok=True)
    report_path = "outputs/reports/indian_junctions_test_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[DONE] Detailed Indian Junctions Test Report saved to: {report_path}")
    return all_results


if __name__ == "__main__":
    run_known_value_unit_tests()
    results = run_indian_junction_experiments()
