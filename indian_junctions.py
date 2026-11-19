"""
Real-world Indian Urban Junction Models with Coordinates, Incident Arms,
Turn Traffic Demands, and Surrounding Building Obstacles (Zero Demolition Constraint).

Junctions modeled:
1. Central Silk Board Junction, Bengaluru
2. ITO Junction, New Delhi
3. Chandani Chowk, Pune
4. Kathipara Junction, Chennai
"""

from typing import Dict, List, Tuple, Any
from ..topology.graph_base import Graph
from ..topology.pathway_synthesis import BuildingPolygon


def get_silk_board_junction() -> Tuple[Graph, List[BuildingPolygon], Dict[Tuple[str, str], float], List[str]]:
    """
    Central Silk Board Junction, Bengaluru.
    Connects Hosur Road (NH 44), Outer Ring Road (ORR), BTM Layout, and Koramangala.
    """
    G = Graph()
    
    # Coordinates in local metric projection (meters around junction centroid 0,0)
    # Centroid: Central intersection (node_C)
    G.add_node("node_C", x=0.0, y=0.0, node_type="bottleneck_centroid", confidence=0.98)
    
    # Arterial endpoints
    G.add_node("arm_N_Koramangala", x=0.0, y=280.0, node_type="arterial_entry", confidence=0.95)
    G.add_node("arm_S_HosurRd", x=0.0, y=-320.0, node_type="arterial_entry", confidence=0.96)
    G.add_node("arm_E_OuterRingRd", x=340.0, y=10.0, node_type="arterial_entry", confidence=0.95)
    G.add_node("arm_W_BTMLayout", x=-300.0, y=-20.0, node_type="arterial_entry", confidence=0.94)

    # At-grade incident edges with initial surface travel time (20 km/h + 90s signal delay at centroid)
    def add_arterial_edge(g, u, v, eid, length):
        # Surface speed 20 km/h = 5.56 m/s plus 90s signal cycle delay
        t_s = round((length / (20.0 / 3.6)) + 90.0, 1)
        g.add_edge(u, v, edge_id=eid, length_m=length, weight=length, travel_time_s=t_s, is_repaired=False)

    add_arterial_edge(G, "arm_N_Koramangala", "node_C", "e_N", 280.0)
    add_arterial_edge(G, "arm_S_HosurRd", "node_C", "e_S", 320.0)
    add_arterial_edge(G, "arm_E_OuterRingRd", "node_C", "e_E", 340.0)
    add_arterial_edge(G, "arm_W_BTMLayout", "node_C", "e_W", 300.0)

    # Surrounding Buildings (Obstacles - ZERO Demolition allowed)
    buildings = [
        BuildingPolygon(
            building_id="bldg_CSB_hq",
            name="Central Silk Board Head Office Complex",
            vertices=[(40.0, 40.0), (160.0, 40.0), (160.0, 160.0), (40.0, 160.0)]
        ),
        BuildingPolygon(
            building_id="bldg_udupi_grand",
            name="Udupi Grand Commercial Towers",
            vertices=[(30.0, -140.0), (150.0, -140.0), (150.0, -30.0), (30.0, -30.0)]
        ),
        BuildingPolygon(
            building_id="bldg_btm_plaza",
            name="BTM Commercial Plaza",
            vertices=[(-170.0, -130.0), (-50.0, -130.0), (-50.0, -35.0), (-170.0, -35.0)]
        ),
        BuildingPolygon(
            building_id="bldg_teachers_colony",
            name="Teachers Colony High-Rise",
            vertices=[(-160.0, 35.0), (-40.0, 35.0), (-40.0, 150.0), (-160.0, 150.0)]
        )
    ]

    # Traffic turn demand (vehicles per hour in peak rush)
    # Heavy right-turn ORR East -> Hosur Road South and BTM West -> ORR East
    demand = {
        ("arm_E_OuterRingRd", "arm_S_HosurRd"): 2200.0,  # Peak turn to Electronic City
        ("arm_E_OuterRingRd", "arm_W_BTMLayout"): 1400.0,
        ("arm_W_BTMLayout", "arm_E_OuterRingRd"): 1800.0,  # Peak turn towards Bellandur IT corridor
        ("arm_N_Koramangala", "arm_S_HosurRd"): 1600.0,
        ("arm_S_HosurRd", "arm_N_Koramangala"): 1500.0,
        ("arm_W_BTMLayout", "arm_S_HosurRd"): 1100.0
    }

    bottleneck_nodes = ["node_C"]
    return G, buildings, demand, bottleneck_nodes


def get_ito_junction() -> Tuple[Graph, List[BuildingPolygon], Dict[Tuple[str, str], float], List[str]]:
    """
    ITO Junction (Indraprastha - Bahadur Shah Zafar Marg), New Delhi.
    High-density institutional junction connecting East Delhi (Vikas Marg), Connaught Place, and South Ring Road.
    """
    G = Graph()
    G.add_node("node_ITO_Centroid", x=0.0, y=0.0, node_type="bottleneck_centroid", confidence=0.99)
    
    G.add_node("arm_E_VikasMarg", x=380.0, y=20.0, node_type="arterial_entry", confidence=0.97)
    G.add_node("arm_W_CP_DDUMarg", x=-320.0, y=-10.0, node_type="arterial_entry", confidence=0.96)
    G.add_node("arm_N_BSZMarg", x=10.0, y=310.0, node_type="arterial_entry", confidence=0.95)
    G.add_node("arm_S_TilakBridge", x=-15.0, y=-340.0, node_type="arterial_entry", confidence=0.96)

    def add_arterial_edge(g, u, v, eid, length):
        t_s = round((length / (20.0 / 3.6)) + 90.0, 1)
        g.add_edge(u, v, edge_id=eid, length_m=length, weight=length, travel_time_s=t_s, is_repaired=False)

    add_arterial_edge(G, "arm_E_VikasMarg", "node_ITO_Centroid", "e_ITO_E", 380.0)
    add_arterial_edge(G, "arm_W_CP_DDUMarg", "node_ITO_Centroid", "e_ITO_W", 320.0)
    add_arterial_edge(G, "arm_N_BSZMarg", "node_ITO_Centroid", "e_ITO_N", 310.0)
    add_arterial_edge(G, "arm_S_TilakBridge", "node_ITO_Centroid", "e_ITO_S", 340.0)

    # Heritage & Media / Government Institutional Buildings (STRICT ZERO DEMOLITION)
    buildings = [
        BuildingPolygon("bldg_herald_house", "National Herald House", [(45.0, 35.0), (170.0, 35.0), (170.0, 160.0), (45.0, 160.0)]),
        BuildingPolygon("bldg_engineers_bhawan", "Engineers Bhawan Institutional HQ", [(40.0, -170.0), (180.0, -170.0), (180.0, -40.0), (40.0, -40.0)]),
        BuildingPolygon("bldg_police_hq", "Old Delhi Police Headquarters", [(-180.0, -160.0), (-45.0, -160.0), (-45.0, -35.0), (-180.0, -35.0)]),
        BuildingPolygon("bldg_ugc_complex", "University Grants Commission Complex", [(-170.0, 40.0), (-40.0, 40.0), (-40.0, 175.0), (-170.0, 175.0)])
    ]

    demand = {
        ("arm_E_VikasMarg", "arm_S_TilakBridge"): 2500.0,  # Trans-Yamuna flow to South Delhi
        ("arm_E_VikasMarg", "arm_W_CP_DDUMarg"): 1700.0,
        ("arm_N_BSZMarg", "arm_S_TilakBridge"): 2000.0,
        ("arm_W_CP_DDUMarg", "arm_E_VikasMarg"): 1600.0,
        ("arm_S_TilakBridge", "arm_N_BSZMarg"): 1900.0
    }

    bottleneck_nodes = ["node_ITO_Centroid"]
    return G, buildings, demand, bottleneck_nodes


def get_chandani_chowk_junction() -> Tuple[Graph, List[BuildingPolygon], Dict[Tuple[str, str], float], List[str]]:
    """
    Chandani Chowk / Paud Road Junction, Pune.
    Intersects NH 48 (Mumbai-Bengaluru highway), Paud Road (to Mulshi), Bavdhan, and Kothrud.
    """
    G = Graph()
    G.add_node("node_CC_Centroid", x=0.0, y=0.0, node_type="bottleneck_centroid", confidence=0.97)

    G.add_node("arm_NH48_Mumbai", x=-180.0, y=320.0, node_type="arterial_entry", confidence=0.96)
    G.add_node("arm_NH48_Bengaluru", x=220.0, y=-300.0, node_type="arterial_entry", confidence=0.97)
    G.add_node("arm_PaudRd_Mulshi", x=-350.0, y=-50.0, node_type="arterial_entry", confidence=0.94)
    G.add_node("arm_Kothrud_Pune", x=310.0, y=120.0, node_type="arterial_entry", confidence=0.95)
    G.add_node("arm_Bavdhan", x=30.0, y=290.0, node_type="arterial_entry", confidence=0.93)

    def add_arterial_edge(g, u, v, eid, length):
        t_s = round((length / (20.0 / 3.6)) + 90.0, 1)
        g.add_edge(u, v, edge_id=eid, length_m=length, weight=length, travel_time_s=t_s, is_repaired=False)

    add_arterial_edge(G, "arm_NH48_Mumbai", "node_CC_Centroid", "e_CC_Mumb", 367.0)
    add_arterial_edge(G, "arm_NH48_Bengaluru", "node_CC_Centroid", "e_CC_Blr", 372.0)
    add_arterial_edge(G, "arm_PaudRd_Mulshi", "node_CC_Centroid", "e_CC_Paud", 353.0)
    add_arterial_edge(G, "arm_Kothrud_Pune", "node_CC_Centroid", "e_CC_Koth", 332.0)
    add_arterial_edge(G, "arm_Bavdhan", "node_CC_Centroid", "e_CC_Bav", 291.0)

    # Foothill & Commercial Retail Complexes
    buildings = [
        BuildingPolygon("bldg_paud_commercial", "Paud Road Commercial Complex", [(-180.0, -180.0), (-60.0, -180.0), (-60.0, -60.0), (-180.0, -60.0)]),
        BuildingPolygon("bldg_bavdhan_plaza", "Bavdhan Hillside Enclave", [(50.0, 50.0), (180.0, 50.0), (180.0, 180.0), (50.0, 180.0)]),
        BuildingPolygon("bldg_kothrud_mall", "Kothrud Gateway Plaza", [(80.0, -150.0), (200.0, -150.0), (200.0, -40.0), (80.0, -40.0)])
    ]

    demand = {
        ("arm_NH48_Mumbai", "arm_NH48_Bengaluru"): 2800.0,
        ("arm_PaudRd_Mulshi", "arm_Kothrud_Pune"): 1900.0,
        ("arm_NH48_Mumbai", "arm_Kothrud_Pune"): 1600.0,
        ("arm_Bavdhan", "arm_NH48_Bengaluru"): 1400.0,
        ("arm_Kothrud_Pune", "arm_NH48_Mumbai"): 1500.0
    }

    bottleneck_nodes = ["node_CC_Centroid"]
    return G, buildings, demand, bottleneck_nodes


def get_kathipara_junction() -> Tuple[Graph, List[BuildingPolygon], Dict[Tuple[str, str], float], List[str]]:
    """
    Kathipara Junction, Chennai.
    Cloverleaf gateway connecting GST Road (Airport), Anna Salai, Inner Ring Road, and Mount-Poonamallee Road.
    """
    G = Graph()
    G.add_node("node_KP_Centroid", x=0.0, y=0.0, node_type="bottleneck_centroid", confidence=0.98)

    G.add_node("arm_AnnaSalai", x=-20.0, y=350.0, node_type="arterial_entry", confidence=0.97)
    G.add_node("arm_GSTRd_Airport", x=10.0, y=-360.0, node_type="arterial_entry", confidence=0.98)
    G.add_node("arm_InnerRingRd", x=330.0, y=-15.0, node_type="arterial_entry", confidence=0.96)
    G.add_node("arm_MountPoonamallee", x=-340.0, y=10.0, node_type="arterial_entry", confidence=0.95)

    def add_arterial_edge(g, u, v, eid, length):
        t_s = round((length / (20.0 / 3.6)) + 90.0, 1)
        g.add_edge(u, v, edge_id=eid, length_m=length, weight=length, travel_time_s=t_s, is_repaired=False)

    add_arterial_edge(G, "arm_AnnaSalai", "node_KP_Centroid", "e_KP_Anna", 350.0)
    add_arterial_edge(G, "arm_GSTRd_Airport", "node_KP_Centroid", "e_KP_GST", 360.0)
    add_arterial_edge(G, "arm_InnerRingRd", "node_KP_Centroid", "e_KP_IRR", 330.0)
    add_arterial_edge(G, "arm_MountPoonamallee", "node_KP_Centroid", "e_KP_MP", 340.0)

    buildings = [
        BuildingPolygon("bldg_guindy_industrial", "Guindy Industrial Tech Park", [(50.0, 45.0), (170.0, 45.0), (170.0, 165.0), (50.0, 165.0)]),
        BuildingPolygon("bldg_metro_annex", "Chennai Metro Operations Wing", [(-165.0, 40.0), (-45.0, 40.0), (-45.0, 160.0), (-165.0, 160.0)]),
        BuildingPolygon("bldg_sidco_complex", "SIDCO Trade Towers", [(-170.0, -170.0), (-50.0, -170.0), (-50.0, -45.0), (-170.0, -45.0)])
    ]

    demand = {
        ("arm_GSTRd_Airport", "arm_InnerRingRd"): 2400.0,  # Airport to Koyambedu freight/commuter
        ("arm_GSTRd_Airport", "arm_AnnaSalai"): 2100.0,    # Airport to Central Chennai
        ("arm_MountPoonamallee", "arm_AnnaSalai"): 1800.0,
        ("arm_InnerRingRd", "arm_GSTRd_Airport"): 1700.0
    }

    bottleneck_nodes = ["node_KP_Centroid"]
    return G, buildings, demand, bottleneck_nodes
