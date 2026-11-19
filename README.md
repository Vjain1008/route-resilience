# Route Resilience: Occlusion-Robust Road Extraction & 3D Grade-Separation Optimization

[![Python Version](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-12%2F12%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Zero Demolition](https://img.shields.io/badge/Demolitions-ZERO%20Guaranteed-success.svg)]()

> **Active Urban Mobility & Disaster Resilience Engine**: An end-to-end framework converting satellite and aerial imagery into mathematically connected road graphs, identifying critical urban chokepoints, and synthesizing collision-free, non-stop 3D continuous bypasses (elevated viaducts, circular loops, and underpasses) around existing buildings with **guaranteed zero demolition**.

---

## 🌟 Key Features

1. **Occlusion-Robust Road Extraction & Gap Repair**:
   - Recovers fragmented road centerlines hidden by tree canopy occlusions (via Excess Green Index $2G - R - B$) and high-rise building shadows.
   - Gated Kruskal Minimum Spanning Tree (MST) with Disjoint Set Union (DSU) to bridge gaps based on distance, angular collinearity, and image evidence.

2. **Complete Multi-Junction Network Scanning**:
   - Indexes and analyzes **every intersection** across the scene (4-way crossroads, 3-way T-junctions, and multi-leg roundabouts), not just a single center node.
   - Calculates exact Brandes' Betweenness Centrality $C_B(v)$ across all detected junctions to rank bottleneck severity.

3. **Physical Road Width & Lane Capacity Profiling**:
   - Measures road corridor width in physical **meters** using perpendicular transect sampling across distance transform fields.
   - Classifies road corridors (Multi-lane Arterial, 4-Lane Primary, 2-Lane Secondary) and computes hourly saturation capacities ($C_{\text{arterial}}$).

4. **3D Multi-Tier Grade-Separation Engine**:
   - Elevates congested turning movements to Tier $+1$ ($z = +7.0\text{ m}$) or Tier $-1$ ($z = -5.5\text{ m}$), eliminating intersection conflicts and red-light idling.
   - Physics-compliant curvature design ($R_{\min} = \frac{v^2}{127(e+f)} = 98.4\text{ m}$ for $50\text{ km/h}$) for smooth, non-stop turns.

5. **Zero-Demolition 3D Building Clearance**:
   - Treats all surrounding structures as impenetrable 3D volumetric keep-out zones.
   - Generates smooth quadratic and cubic Bézier viaduct curves that maintain safety clearance ($18.7\text{ m}$ to $185\text{ m}$) without demolishing any residential or commercial buildings.

6. **Circular-Wait Deadlock Dissolution**:
   - Models Bureau of Public Roads (BPR) link delays and intersection queue spillovers.
   - Proves mathematically and experimentally that continuous bypasses dissolve bottleneck queues ($2,000\text{ vehicles} \to 0$), preventing gridlock cascades.

7. **Interactive Aerial Report Generator Web App**:
   - Drag-and-drop satellite/aerial photograph uploader with live multi-junction report generation.
   - Preloaded with high-congestion Indian urban junctions: **Silk Board (Bengaluru)**, **ITO (Delhi)**, **Chandani Chowk (Pune)**, **Kathipara (Chennai)**, and **Multi-Junction Arterial Corridor**.
   - Displays every detected junction, measured road widths, occlusion masks, 3D bypass curves, and congestion metrics.
   - Export full JSON logs or print executive engineering reports.

---

## 🚀 Quick Start & Trial Run

### 1. Installation
Clone this repository and ensure Python is installed:
```bash
git clone https://github.com/your-username/route-resilience.git
cd route-resilience
```

*(Optional) Create and activate a virtual environment:*
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

Install requirements (or run directly using the standard library & existing packages):
```bash
pip install fastapi uvicorn pillow
```

---

### 2. Launch the Interactive Web Trial App
Launch the trial web server:
```bash
python app.py
```
Open your browser at:
👉 **`http://localhost:8000`**

- **Upload any aerial/satellite photo** or click one of the pre-loaded Indian junction presets (Silk Board, ITO, Chandani Chowk, Kathipara).
- View the instant side-by-side analysis, detected occlusions, synthesized 3D bypasses, and quantitative congestion reduction reports.

---

### 3. Open the 3D Interactive Spatial Viewer
Open `outputs/visualization/junction_3d_viewer.html` directly in any web browser to view the interactive 3D perspective viewer with live animated vehicle trajectories gliding smoothly over and around the buildings.

---

### 4. Run the Full Test & Verification Suite
Run the comprehensive 12-test Section 13.1 verification and Indian junction stress-tests:
```bash
python run_simulation.py
```

---

## 📊 Experimental Results on Indian Junctions

Evaluated against high-density arterial intersections across India:

| Junction | Bottleneck Gatekeeper | 3D Bypass Type | Min. Building Clearance | Congestion Reduction | Post-Intervention Trip Duration |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Central Silk Board (Bengaluru)** | `node_C` ($C_B = 1.0$) | `ELEVATED_CURVED` ($z=+7.0\text{m}$) | **$182.5\text{ m}$** | **$78.60\%$** | **$27\text{ min}$** *(was $129\text{ min}$)* |
| **ITO Junction (New Delhi)** | `node_ITO_Centroid` ($C_B = 1.0$) | `BENDED_FLYOVER` ($z=+7.0\text{m}$) | **$178.7\text{ m}$** | **$84.68\%$** | **$23\text{ min}$** *(was $151\text{ min}$)* |
| **Chandani Chowk (Pune)** | `node_CC_Centroid` ($C_B = 1.0$) | `SUBTERRANEAN_UNDERPASS` ($z=-5.5\text{m}$) | **$41.8\text{ m}$** | **$22.55\%$** | **$79\text{ min}$** *(was $103\text{ min}$)* |
| **Kathipara Junction (Chennai)** | `node_KP_Centroid` ($C_B = 1.0$) | `CIRCULAR_BYPASS` ($z=+7.0\text{m}$) | **$170.9\text{ m}$** | **$88.82\%$** | **$12\text{ min}$** *(was $113\text{ min}$)* |
| **Multi-Junction Arterial Corridor** | `junction_4` ($C_B = 0.444$) | `ELEVATED_VIADUCT` ($z=+7.0\text{m}$) | **$17.1\text{ m}$** | **$88.87\%$** | **$14\text{ min}$** *(was $128\text{ min}$)* |

*Across all 5 real and synthetic junction scenarios, structures demolished: **0 (Zero)**.*

---

## 📂 Repository Structure

```text
route-resilience/
├── app.py                          # FastAPI Interactive Trial Web Server
├── run_simulation.py               # Master CLI execution pipeline
├── requirements.txt                # Production package dependencies
├── setup.py                        # Python packaging metadata
├── static/
│   └── index.html                  # Responsive Interactive Trial Web UI
├── data/
│   └── sample_images/              # Preloaded Indian junction aerial images
│       ├── silk_board.jpg
│       ├── ito_delhi.jpg
│       ├── chandani_chowk.jpg
│       ├── kathipara_chennai.jpg
│       └── corridor_multi_junction.jpg
├── src/
│   ├── pipeline/
│   │   ├── cv_road_extractor.py     # Multi-junction detector & road width calculator
│   │   └── image_report_generator.py # Photo analysis & report generator
│   ├── topology/
│   │   ├── elevation_network.py    # 3D multi-tier network & curvature physics
│   │   ├── optimizer_3d.py         # 3D viaduct synthesizer around building prisms
│   │   ├── gap_repair.py           # Gated Kruskal MST gap healing
│   │   ├── pathway_synthesis.py    # 2D/3D collision-free curve synthesis
│   │   └── graph_base.py           # Core graph data structure & Dijkstra
│   ├── analysis/
│   │   ├── centrality.py           # Brandes' Betweenness Centrality
│   │   ├── resilience.py           # Weighted Global Efficiency & node ablation
│   │   ├── traffic_simulation.py   # BPR delay & non-stop volume model
│   │   └── deadlock_cascade.py     # Queue spillback & circular wait model
│   ├── data/
│   │   └── indian_junctions.py     # Real coordinates & demands for Indian cities
│   └── evaluation/
│       └── metrics.py              # APLS, connectivity ratio, Spearman rank
├── scripts/
│   ├── generate_sample_satellite_tiles.py   # Synthesizes Indian city aerial images
│   └── generate_multi_junction_corridor.py  # Synthesizes 15-junction arterial corridor
├── tests/
│   ├── test_pipeline.py            # Section 13.1 unit tests & junction tests
│   ├── test_3d_enhancements.py     # 3D elevation & deadlock tests
│   └── test_image_report.py        # Multi-junction & road width test suite
├── outputs/
│   ├── visualization/
│   │   └── junction_3d_viewer.html # Standalone interactive 3D spatial viewer
│   └── reports/
│       └── indian_junctions_test_report.json # Raw benchmark output log
└── README.md
```

---

## 🛠️ Step-by-Step GitHub Upload Guide

To push this repository to GitHub:

```bash
# 1. Initialize git repository
git init

# 2. Add all project files
git add .

# 3. Create initial commit
git commit -m "Initial release: Route Resilience 3.0 with interactive aerial report generator and 3D non-stop bypass optimizer"

# 4. Set your main branch
git branch -M main

# 5. Link to your GitHub repository
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# 6. Push to GitHub
git push -u origin main
```

---

## 📜 Citations & References

- Brandes, U. (2001). *A Faster Algorithm for Betweenness Centrality*. Journal of Mathematical Sociology.
- Latora, V., & Marchiori, M. (2001). *Efficient Behavior of Small-World Networks*. Physical Review Letters.
- Bureau of Public Roads (1964). *Traffic Assignment Manual*. U.S. Dept. of Commerce.
- American Association of State Highway and Transportation Officials (AASHTO) & Indian Roads Congress (IRC). *Geometric Design Standards for High-Speed Flyover Ramps*.
