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

ox.settings.log_console=True
ox.settings.use_cache=True



#sample_list = [[14.549782711255753, 121.00515608352754],[14.549163881741926, 121.00433654028181], [14.54816721998631, 121.00252036521498],
#               [14.547892358182233, 120.99867935257014], [14.548951532876389, 120.99845743761652], [14.54975898911636, 120.99826284183357]]


MAX_DISTANCE = 5
WALKING_DISTANCES = [300,550,800]

sample_list = [[14.554747648304462, 120.99708773241291],
            [14.55682541697913, 120.9966188462127], [14.558134432084954, 120.99631901422849], [14.562959814489666, 120.9951164965514],
            [14.56521038861722, 120.99407027429525], [14.567639994973721, 120.99291241244708], [14.571400341625692, 120.99106589101036], 
            [14.57326454125839, 120.99002386850968], [14.574683418006057, 120.99015017430045], [14.576316206390171, 120.98877434369244],
            [14.578573276306315, 120.9869744866499], [14.580597203953493, 120.9858397325545], [14.583103926540224, 120.9844243629383],
            [14.58378673371261, 120.98401469555728], [14.584495235716412, 120.98363916714366], [14.58520740641153, 120.98324467266578], [14.585805774843385, 120.982929835702],
            [14.586943775676762, 120.98223290339324], [14.58772940326058, 120.98388821313192]] 

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


def connect_stops():
    routes = []
    print(f"NUMBER OF POINTS: {len(sample_list)}")
    for i in range(len(sample_list)-1):
        #print("Calculating route from", sample_list[i], "to", sample_list[i+1])
        orig_node = ox.distance.nearest_nodes(graph, sample_list[i][1], sample_list[i][0])
        dest_node = ox.distance.nearest_nodes(graph, sample_list[i+1][1], sample_list[i+1][0])
        
        if orig_node is None or dest_node is None:
            print("Unable to find valid nodes. Please verify the start and end coordinates.")
        elif not nx.has_path(graph, orig_node, dest_node):
            print("No valid path found between the start and end nodes.")
        else:
            shortest_route = nx.shortest_path(graph, orig_node, dest_node)
            # shortest_route_map = ox.plot_route_folium(graph, shortest_route, tiles='openstreetmap')
            # shortest_route_map.save("shortest_route_map.html")
            
            routes.append(shortest_route)
    return routes

def generate_route_network(stop_nodes, max_walking_dist):
    stop_node_coordinates = sample_list
    stop_nodes_kd_tree = KDTree(stop_node_coordinates)
    
    route_network = generate_route(stop_nodes, stop_nodes_kd_tree, max_walking_dist)

    return route_network

def generate_route(stop_nodes, stop_nodes_kd_tree, max_walking_dist):
    route = []
    enable_stop_nodes(stop_nodes)
    #selected_node = random.choice(stop_nodes)
    selected_node = stop_nodes[0] # TEMPORARY
    next_nodes = [nodes for nodes in stop_nodes if nodes != selected_node]
    totalDistance = 0

    while not all_nodes_disabled(next_nodes) and totalDistance <= MAX_DISTANCE:
        used_stops.append(selected_node)
        print(f"Selected node is {selected_node.getLat()}, {selected_node.getLong()}")
        disable_surrounding_nodes(next_nodes, stop_nodes_kd_tree, selected_node, max_walking_dist)
        enabled_nodes = [n for n in next_nodes if n.enabled]
        orig_node = ox.distance.nearest_nodes(graph, selected_node.getLong(), selected_node.getLat())
        old_node = selected_node
        selected_node = get_enabled_node_with_highest_edge_probability(selected_node, enabled_nodes)
        if (selected_node == None):
            break
        
        next_nodes.remove(selected_node)
        dest_node = ox.distance.nearest_nodes(graph, selected_node.getLong(), selected_node.getLat())
        
        if orig_node is None or dest_node is None:
            print("Unable to find valid nodes. Please verify the start and end coordinates.")
        elif not nx.has_path(graph, orig_node, dest_node):
            print("No valid path found between the start and end nodes.")
        else:
            shortest_route = nx.shortest_path(graph, orig_node, dest_node)
            totalDistance += haversine(old_node.getLat(), old_node.getLong(), selected_node.getLat(), selected_node.getLong())
            route.append(shortest_route)

    print(f"Total Distance: {totalDistance}km")
    return route

def disable_surrounding_nodes(next_nodes, stop_nodes_kd_tree, source_node, max_distance):
    source = (source_node.getLat(), source_node.getLong())
    
    for node in next_nodes:
        point = (node.getLat(), node.getLong())
        distance = geodesic(source, point).meters
        if distance <= max_distance:
            node.disable()
            print(f"Disabled node {node.getLat()}, {node.getLong()}")
        


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

# def euclidean(x, y):
#     sum_square = 0.0
#     for i in range(len(x)):
#         sum_square += (x[i] - y[i]) ** 2

#     return sum_square ** 0.5

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






#MAIN -----------------------------------------------------------

# Generate stops from coordinates
stops = []
for coord in sample_list:
    stops.append(stopCandidate(coord[0], coord[1]))

# Load graph
graph = load_graph()
#old_routes = connect_stops() # OLD CONNECT FUNCTION -> FOR TESTING ONLY

# Generate route network
used_stops = []
route_network = generate_route_network(stops, WALKING_DISTANCES[0]) # Default max walking distance is 300m



map_center = (sample_list[0][0], sample_list[0][1])
# Folium map 1 ----------------------------------------------------------
# m1 = folium.Map(location=map_center, zoom_start=15, tiles='openstreetmap')

# # Add markers to the map
# for point in sample_list:
#     folium.Marker(location=[point[0], point[1]]).add_to(m1)

# for route in old_routes:
#     route_coordinates = []
#     for node in route:
#         node_data = graph.nodes[node]
#         route_coordinates.append([node_data['y'], node_data['x']])
#     folium.PolyLine(locations=route_coordinates, color='blue').add_to(m1)

# m1.save("Map1.html")

# Folium map2 -----------------------------------------------------------
m2 = folium.Map(location=map_center, zoom_start=15, tiles='openstreetmap')

for stop in used_stops:
    folium.Marker(location=[stop.getLat(), stop.getLong()]).add_to(m2)
    
for route in route_network:
    route_coordinates = []
    for node in route:
        node_data = graph.nodes[node]
        route_coordinates.append([node_data['y'], node_data['x']])
    folium.PolyLine(locations=route_coordinates, color='blue').add_to(m2)

m2.save("Map2.html")

# Open the HTML file in a web browser to view the map
webbrowser.open("Map2.html")

#rc = ['r', 'y', 'c', 'm', 'g']
#ox.plot_graph_routes(graph, routes, route_colors=rc, route_linewidth=6, node_size=0)







# Constraints
# - Route does not go above 15km (LTFRB)
# - Route does no go below the radius

# Manhattan distance(Manhattan Distance = | x 1 − x 2 | + | y 1 − y 2 |)


# def manhattan_distance(lat1, lon1, lat2, lon2):





# def generate_route_network(stop_nodes, max_walking_dist, num_generations):
#     # k-dimensional tree is built only once per route for optimization
#     stop_node_coordinates = [n.latlng for n in stop_nodes]
#     stop_nodes_kd_tree = KDTree(stop_node_coordinates)
#     possible_start_nodes = [x for x in stop_nodes]

#     route_network = []
#     for i in range(num_generations):
#         route_network.append(generate_route(stop_nodes, possible_start_nodes, stop_nodes_kd_tree, max_walking_dist))

#     return route_network


# def generate_route(stop_nodes, possible_start_nodes, stop_nodes_kd_tree, max_walking_dist):
#     route = []
#     enable_stop_nodes(stop_nodes)
#     selected_node = random.choice(possible_start_nodes)
#     possible_start_nodes.remove(selected_node)

#     while not all_nodes_disabled(stop_nodes):
#         route.append(selected_node)
#         disable_surrounding_nodes(stop_nodes, stop_nodes_kd_tree, selected_node, max_walking_dist / 111111)
#         enabled_nodes = [n for n in stop_nodes if n.enabled]
#         selected_node = get_enabled_node_with_highest_edge_probability(selected_node, enabled_nodes)

#     return route






