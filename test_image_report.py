"""
Test script for verifying dynamic image report generator across all sample aerial images.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline.image_report_generator import analyze_photograph_and_generate_report

def main():
    print("Testing dynamic image report generator on all sample images...")
    sample_dir = "data/sample_images"
    for s in sorted(os.listdir(sample_dir)):
        if s.endswith(".jpg"):
            path = os.path.join(sample_dir, s)
            with open(path, "rb") as f:
                report = analyze_photograph_and_generate_report(f.read(), junction_name=s)
            
            print(f"\n[OK] Tested: {s}")
            print(f"  * Detected Junctions Count: {len(report['detected_junctions'])}")
            for j in report['detected_junctions']:
                pri_tag = " [PRIMARY BOTTLENECK]" if j.get('is_primary_bottleneck') else ""
                print(f"    - Junction {j['junction_id']}: ({j['x']}, {j['y']}) | Type: {j['junction_type']} ({j['degree']}-Way) | Betweenness C_B={j['betweenness_centrality']:.4f}{pri_tag}")
            
            print(f"  * Road Size & Capacity Profiles:")
            for rp in report['road_size_profiles']:
                print(f"    - Segment {rp['segment_id']}: Width={rp['width_m']}m ({rp['lane_count']} Lanes) | Class: {rp['road_class']} | Capacity: {int(rp['capacity_vph'])} vph")
            
            print(f"  * Total Occlusion: {report['occlusion_analysis']['total_occlusion_percent']}%")
            print(f"  * Congestion Delay Drop: {report['traffic_impact']['congestion_delay_reduction_percent']}%")
            print(f"  * Minimum Building Clearance: {report['synthesized_bypass']['min_building_clearance_m']} m")
            print(f"  * Zero Demolition Guaranteed: {report['synthesized_bypass']['zero_demolition_verified']}")

if __name__ == "__main__":
    main()
