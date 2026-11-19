"""
Route Resilience - Main Execution Pipeline.
Executes end-to-end topological analysis, gap healing, node ablation stress tests,
and continuous non-stop pathway synthesis across Indian urban junctions.
"""

import sys
import os

# Set root directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_pipeline import run_known_value_unit_tests, run_indian_junction_experiments
from tests.test_3d_enhancements import run_3d_elevation_tests
from tests.test_image_report import main as run_image_report_tests

def main():
    print("=" * 80)
    print("ROUTE RESILIENCE: OCCLUSION-ROBUST ROAD EXTRACTION & GRAPH CRITICALITY ANALYSIS")
    print("Route Resilience 3.0: Zero-Demolition 3D Continuous Non-Stop Flow Engine")
    print("=" * 80)
    
    # 1. Execute Formal Specification Unit Tests
    run_known_value_unit_tests()
    
    # 2. Execute Indian Urban Junctions Benchmark
    results = run_indian_junction_experiments()

    # 3. Execute 3D Multi-Tier Elevation & Deadlock Dissolution Tests
    run_3d_elevation_tests()

    # 4. Execute Dynamic Aerial Photograph Extraction & Report Tests
    run_image_report_tests()
    
    print("\n[SUCCESS] Pipeline execution finished.")
    print(f"Evaluated {len(results)} major Indian junctions and 4 aerial image tiles.")
    print("Interactive 3D Visualizer available at: outputs/visualization/junction_3d_viewer.html")
    print("Interactive Web Trial Server available via: python app.py")

if __name__ == "__main__":
    main()
