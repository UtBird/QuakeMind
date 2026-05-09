import osmnx as ox
import networkx as nx
from shapely.geometry import LineString
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_route(G, start_lat, start_lon, end_lat, end_lon):
    start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)
    
    def astar_heuristic(u, v):
        u_node = G.nodes[u]
        v_node = G.nodes[v]
        return haversine(u_node['y'], u_node['x'], v_node['y'], v_node['x'])
        
    try:
        path_dijkstra = nx.shortest_path(G, start_node, end_node, weight='length')
    except nx.NetworkXNoPath:
        path_dijkstra = None
        
    try:
        path_astar = nx.astar_path(G, start_node, end_node, heuristic=astar_heuristic, weight='length')
    except nx.NetworkXNoPath:
        path_astar = None
        
    def get_route_line(path):
        if not path:
            return None
        route_coords = []
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            edge_data = min(G[u][v].values(), key=lambda d: d.get('length', float('inf')))
            if 'geometry' in edge_data:
                route_coords.extend([(lat, lon) for lon, lat in edge_data['geometry'].coords])
            else:
                route_coords.extend([(G.nodes[u]['y'], G.nodes[u]['x']), (G.nodes[v]['y'], G.nodes[v]['x'])])
        return route_coords
        
    return get_route_line(path_dijkstra), get_route_line(path_astar)

def analyze_road_network_graph(bounds, w, h, blockage_mask):
    """Fetches OSM graph, evaluates blockages, and returns safe/blocked lists."""
    west, south, east, north = bounds
    try:
        # 'drive' kullanarak sadece araç yollarını çekiyoruz, graph boyutu küçülüyor ve hızlanıyor
        G = ox.graph_from_bbox(bbox=bounds, network_type='drive', simplify=True)
    except Exception as e:
        print("OSMnx error:", e)
        return None, None, None, None

    blocked_edges = []
    safe_edges = []
    edges_to_remove = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        if 'geometry' in data:
            line = data['geometry']
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            line = LineString([(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])])
            
        length = line.length
        # Örnekleme sıklığını ~5 metreye düşürüyoruz (eskiden ~2 metreydi)
        num_samples = max(int(length / 0.00005), 3)
        
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
                
        if has_blocked_part:
            edges_to_remove.append((u, v, key))

    safe_G = G.copy()
    safe_G.remove_edges_from(edges_to_remove)
                
    return G, safe_G, safe_edges, blocked_edges
