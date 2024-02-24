from __future__ import absolute_import, division
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2, exp
import webbrowser
import folium
import random
from scipy.spatial import KDTree
from scipy.spatial.distance import euclidean
from geopy.distance import geodesic

from stopCandidate import stopCandidate
from stopCandidate import get_stopCandidates

ox.settings.log_console=True
ox.settings.use_cache=True


MAX_DISTANCE = 15
WALKING_DISTANCES = [300,550,800]
#colors = ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'cyan', 'magenta', 'lime', 'pink']
colors = ['red', 'blue', 'green', 'orange']

# IF FIRST TIME RUNNING, RUN THIS CODE TO GENERATE THE GRAPH
def generate_graph():
    place = 'Metro Manila, Philippines'
    mode = 'drive'
    graph = ox.graph_from_place(place, network_type = mode) # Generate graph of Metro manila
    ox.save_graphml(graph, 'map/MetroManila.graphml') # Save it as a file

# Load the graph from the file
def load_graph():
    graph = ox.load_graphml('routeGenerator/map/MetroManila.graphml')
    
    print("Graph loaded successfully")
    print("NUMBER OF EDGES: ", graph.number_of_edges())
    print("NUMBER OF NODES: ", graph.number_of_nodes())
    print('\n')
    return graph

# Generate Route Network from connected routes
def generate_route_network(stop_nodes, max_walking_dist):
    stop_node_coordinates = locs
    stop_nodes_kd_tree = KDTree(stop_node_coordinates)
    next_nodes = [n for n in stop_nodes]
    enable_stop_nodes(next_nodes)
    route_network = []
    
    while not all_nodes_disabled(next_nodes) and len(next_nodes) != 0:
        selected_node = random.choice(next_nodes) # For the first node
        next_nodes.remove(selected_node)
        used_stops.append(selected_node)
        
        route_network.append(generate_route(selected_node, next_nodes, stop_nodes_kd_tree, max_walking_dist))

    return route_network

# Generate route from stop nodes
def generate_route(source, next_nodes, stop_nodes_kd_tree, max_walking_dist):
    route = []
    totalDistance = 0
    selected_node = source
    
    # TODO: Have a prior checking if next possible node is within the max distance
    while not all_nodes_disabled(next_nodes) and totalDistance < MAX_DISTANCE:
        #print(f"Selected node is {selected_node.getLat()}, {selected_node.getLong()}")
        disable_surrounding_nodes(next_nodes, stop_nodes_kd_tree, selected_node, max_walking_dist)
        enabled_nodes = [n for n in next_nodes if n.enabled]
        orig_node = ox.distance.nearest_nodes(graph, selected_node.getLong(), selected_node.getLat())
        old_node = selected_node
        selected_node = get_enabled_node_with_highest_edge_probability(selected_node, enabled_nodes)
        
        
        if (selected_node == None or selected_node == old_node):
            break
        
        next_nodes.remove(selected_node)
        dest_node = ox.distance.nearest_nodes(graph, selected_node.getLong(), selected_node.getLat())
        
        if orig_node is None or dest_node is None:
            print("Unable to find valid nodes. Please verify the start and end coordinates.")
        elif not nx.has_path(graph, orig_node, dest_node):
            print("No valid path found between the start and end nodes.")
        else:
            shortest_route = nx.shortest_path(graph, orig_node, dest_node)
            distance_travelled = 0
            # TODO: Get the total distance travelled
            for i in range(len(shortest_route)-1):
                node_data = graph.nodes[shortest_route[i]]
                next_node_data = graph.nodes[shortest_route[i+1]]
                distance_travelled += haversine(node_data['y'], node_data['x'], next_node_data['y'], next_node_data['x'])
                
            if totalDistance + distance_travelled <= MAX_DISTANCE:
                totalDistance += distance_travelled
                used_stops.append(selected_node)
                route.append(shortest_route)
            else:
                break
            

    print(f"Total Distance: {totalDistance}km")
    return route

# Disable surrounding nodes
def disable_surrounding_nodes(next_nodes, stop_nodes_kd_tree, source_node, max_distance):
    source = (source_node.getLat(), source_node.getLong())
    
    for node in next_nodes:
        point = (node.getLat(), node.getLong())
        distance = geodesic(source, point).meters
        if distance <= max_distance:
            node.disable()
            #print(f"Disabled node {node.getLat()}, {node.getLong()}")
        


def get_enabled_node_with_highest_edge_probability(source_node, enabled_nodes):
    highest_edge_prob = 0
    highest_edge_prob_node = None

    for n in enabled_nodes:
        edge_prob = get_edge_probability(source_node, n, len(enabled_nodes))
        if edge_prob > highest_edge_prob:
            highest_edge_prob = edge_prob
            highest_edge_prob_node = n

    return highest_edge_prob_node


def get_edge_probability(source, destination, normalization_factor):
    source_coord = [source.getLat(), source.getLong()]
    dest_coord = [destination.getLat(), destination.getLong()]
    return exp(-(euclidean(source_coord, dest_coord))) / float(normalization_factor)




def radius(stops):
    circles = []
    for stop in stops:
        stop_point = Point(stop[1], stop[0])  # Create a Point object from [lat, lon] coordinates
        circle = stop_point.buffer(radius / 111000)  # Buffer the Point to create a circle (assuming 1 degree is approximately 111000 meters)
        circles.append(circle)
    return circles

def enable_stop_nodes(stop_nodes):
    for n in stop_nodes:
        n.enable()

def all_nodes_disabled(stop_nodes):
    return get_num_disabled(stop_nodes) == len(stop_nodes)


def get_num_disabled(stop_nodes):
    return sum(1 for n in stop_nodes if not n.enabled)

# TO CALCULATE DISTANCE
def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = 6371 * c  # Radius of earth in kilometers
    return distance


# Markers for visualization purposes
def add_markers(used_stops):
    for stop in used_stops:
        popup_text = f"Name: {stop.name}<br>Type: {stop.a_type}<br>Coordinates: {stop.getLat()}, {stop.getLong()}"
        folium.Marker(location=[stop.road_lat, stop.road_long], popup=popup_text).add_to(map)

#MAIN TEST -----------------------------------------------------------

# Load graph
graph = load_graph()

# Generate stops from coordinates
locations = get_stopCandidates()
locs = []
road_stops = [] # To store all the road stops
for loc in locations:
    node = ox.distance.nearest_nodes(graph, loc.getLong(), loc.getLat())
    if graph.has_node(node):
        loc.road_lat = graph.nodes[node]['y']
        loc.road_long = graph.nodes[node]['x']
        locs.append([loc.getLat(), loc.getLong()])
        road_stops.append(loc)
        

# Generate route network
used_stops = []
route_network = generate_route_network(road_stops, WALKING_DISTANCES[2]) # Default max walking distance is 300m


# Creating Map
map_center = (14.599512, 120.984222)
map = folium.Map(location=map_center, zoom_start=10, tiles='openstreetmap')

# Plotting in the Map
add_markers(used_stops)
    
for route in route_network:
    random_color = random.choice(colors)
    for connection in route:
        ox.plot_route_folium(graph, connection, route_map=map, tiles='openstreetmap', route_color=random_color)

map.save("Map2.html")

# Open the HTML file in a web browser to view the map
webbrowser.open("Map2.html")






