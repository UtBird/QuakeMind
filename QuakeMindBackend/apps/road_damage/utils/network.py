import osmnx as ox
import networkx as nx
from shapely.geometry import LineString

def analyze_road_network_graph(bounds, w, h, blockage_mask):
    """Fetches OSM graph, evaluates blockages, and returns safe/blocked lists."""
    west, south, east, north = bounds
    try:
        G = ox.graph_from_bbox(bbox=bounds, network_type='all', simplify=True)
    except Exception as e:
        print("OSMnx error:", e)
        return None, None, None

    blocked_edges = []
    safe_edges = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        if 'geometry' in data:
            line = data['geometry']
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            line = LineString([(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])])
            
        length = line.length
        # Sample every ~2 meters to accurately capture small blockages
        num_samples = max(int(length / 0.00002), 5)
        
        current_type = None
        current_segment = []
        has_blocked_part = False
        
        for i in range(num_samples):
            pt = line.interpolate(float(i) / (num_samples - 1), normalized=True)
            px = int((pt.x - west) / (east - west) * w)
            py = int((north - pt.y) / (north - south) * h)
            
            is_blocked = False
            if 0 <= px < w and 0 <= py < h:
                if blockage_mask[py, px] > 0:
                    is_blocked = True
                    has_blocked_part = True
                    
            if current_type is None:
                current_type = is_blocked
                current_segment.append((pt.x, pt.y))
            elif current_type == is_blocked:
                current_segment.append((pt.x, pt.y))
            else:
                current_segment.append((pt.x, pt.y)) # connect lines
                if len(current_segment) > 1:
                    if current_type:
                        blocked_edges.append((u, v, key, LineString(current_segment)))
                    else:
                        safe_edges.append((u, v, key, LineString(current_segment)))
                
                current_type = is_blocked
                current_segment = [(pt.x, pt.y)]

        if len(current_segment) > 1:
            if current_type:
                blocked_edges.append((u, v, key, LineString(current_segment)))
            else:
                safe_edges.append((u, v, key, LineString(current_segment)))
                
    return G, safe_edges, blocked_edges
