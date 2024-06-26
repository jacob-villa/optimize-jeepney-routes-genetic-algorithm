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

# sample_list = [[14.55820324,120.99271588],[14.67736013,121.06370599],[14.44087539,120.96480535],[14.66010137,121.00552241],[14.67582084,120.97917578],[14.68846586,121.06735489],[14.59969414,121.03524401],[14.51854099,121.03136655],[14.6944043,120.96867543],[14.5563217,121.07754653],[14.58395269,121.009026],[14.71428035,121.05318844],[14.63796946,121.08900077],[14.68840554,121.04276003],[14.62446177,121.03960171],[14.57615011,121.03103186],[14.68047839,121.00882462],[14.61102805,121.03803691],[14.65562362,121.03747689],[14.63428298,121.02315351],[14.59367792,121.08552916],[14.61496911,120.96150489],[14.49455642,121.03632284],[14.52785148,121.07707068],[14.63969782,121.06757377],[14.72545455,120.99808766],[14.65138419,121.07051039],[14.53648099,121.07554772],[14.61327739,120.98706874],[14.7163623,120.99811453],[14.70024841,121.02352652],[14.64942255,121.08590113],[14.44703678,121.01101709],[14.44215199,121.01550486],[14.54165084,121.03013544],[14.63736669,121.00484071],[14.65543842,121.01469844],[14.69615693,121.05405007],[14.59582863,121.04494513],[14.4672852,120.99129503],[14.55859342,121.0016252],[14.57573588,121.07675665],[14.58081946,120.98392977],[14.61193905,121.02728961],[14.4384651,120.9883522],[14.67663015,120.95704148],[14.58188072,121.03112538],[14.58231564,121.01074813],[14.61952633,121.03024989],[14.60702046,121.01301824],[14.69292332,120.98808483],[14.59824403,121.03330051],[14.43566221,120.97401883],[14.69794719,120.98111104],[14.59550621,121.07080338],[14.45936723,121.04212204],[14.53617335,121.07731764],[14.71078316,121.04049493],[14.50735874,121.03907134],[14.6864969,121.08484785],[14.65509136,121.04779834],[14.57888998,121.05292725],[14.67192032,120.97574468],[14.4973495,121.05733039],[14.68184463,121.03149686],[14.72650157,120.97394383],[14.69790796,121.07487706],[14.45344411,121.04490347],[14.63868507,121.04444338],[14.50231075,120.99807186],[14.43959588,121.02509234],[14.68261589,120.96242323],[14.72485542,121.01299281],[14.58322369,121.01447599],[14.67123132,121.04123659],[14.60558001,121.08405982],[14.45011738,120.98999835],[14.66114487,120.96992306],[14.49985795,121.05785851],[14.53736977,121.08187118],[14.53622662,121.02906501],[14.59617857,121.00179193],[14.5388522,121.07337775],[14.43692456,121.01233361],[14.68664721,121.08457592],[14.54565777,121.04755655],[14.52327443,121.0347132],[14.65601779,121.0461127],[14.47007772,121.02008342],[14.6776021,121.04271068],[14.60737226,120.98397032],[14.47543653,121.02949694],[14.60198032,121.00463174],[14.46116767,121.04024682],[14.46144194,121.0395247],[14.59669815,121.07887086],[14.60226846,121.07731067],[14.66798856,121.08055865],[14.55934149,121.06013169],[14.51857845,121.03619419],[14.72091861,120.9731885],[14.54069915,121.02634641],[14.57894624,121.07754012],[14.51553237,121.07041719],[14.68491504,120.95990223],[14.71266055,121.04447903],[14.67047015,121.04743715],[14.49727616,121.02700058],[14.57942463,121.02734004],[14.48682048,121.05306338],[14.60135917,120.98037093],[14.68577896,121.02836462],[14.55474596,121.01697453],[14.62604571,121.04736863],[14.72411477,120.99674891],[14.65876292,121.06815126],[14.53470539,121.08178085],[14.58808667,121.05836262],[14.63250216,120.96704797],[14.4723381,121.0322874],[14.5532874,121.05018914],[14.51615166,121.06814045],[14.47170787,120.98884609],[14.49123999,121.02244802],[14.60675883,121.02864645],[14.47975831,121.0516267],[14.6026604,121.04531354],[14.72153054,121.00523589],[14.57608016,121.04005992],[14.68738844,121.09067366],[14.60252123,121.01272277],[14.68426545,121.02886611],[14.65373801,121.02995595],[14.59770938,121.02927924],[14.62060749,121.03767257],[14.72598521,120.95843269],[14.62558255,121.0379151],[14.522141,121.06813073],[14.68508825,121.02777006],[14.57410668,121.01783286],[14.65167849,121.02623058],[14.7227,121.00275333],[14.71867643,121.03861321],[14.44624564,120.9982853],[14.55042948,121.00487298],[14.67959045,121.02535213],[14.65581958,121.00831317],[14.54399834,121.04911272],[14.49753273,121.03251303],[14.53392981,121.01039963],[14.71428417,120.99603868],[14.62804118,121.03376718],[14.58327883,121.04742346],[14.59202403,120.99922025],[14.64060533,121.01325225],[14.60608361,120.97934671],[14.60184942,121.00164006],[14.52005313,121.07458641],[14.71044623,121.02102646],[14.6324198,120.98870328],[14.63421092,121.0174889],[14.60268225,121.07356315],[14.60206155,120.96739007],[14.71191798,120.99704026]]

sample_list =[[14.6174803, 120.979948], [14.6020369, 121.0186477], [14.60376340723475, 121.01683659691342]]


def add_markers(map_obj, coordinates):
    for coord in coordinates:
        folium.Marker(location=coord, popup=str(coord)).add_to(map_obj)

def load_graph():
    graph = ox.load_graphml('routeGenerator/map/MetroManila.graphml')
    
    print("Graph loaded successfully")
    print("NUMBER OF EDGES: ", graph.number_of_edges())
    print("NUMBER OF NODES: ", graph.number_of_nodes())
    print('\n')
    return graph

def is_within_graph(G, latitude, longitude, threshold_distance=100):
    nearest_node = ox.distance.nearest_nodes(G, longitude, latitude)
    if nearest_node is not None:
        # Check if the nearest node is within the specified threshold distance
        node_coords = G.nodes[nearest_node]['y'], G.nodes[nearest_node]['x']
        distance = ox.distance.great_circle_vec(latitude, longitude, *node_coords)
        if distance > threshold_distance:
            return False  # The point is not within the graph
        # Check if the nearest node is not part of a water-related feature
        
        print(G.nodes[nearest_node])
        if 'water' in G.nodes[nearest_node]:
            return False  # The point is in a water-related feature
        return True  # The point is within the graph and not in water
    else:
        return False  # The point is not within the graph

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


# Load graph
graph = load_graph()

# Generate stops from coordinates
stops = sample_list

route = []
for i in range(len(stops)-1):
    orig_node = ox.distance.nearest_nodes(graph, sample_list[i][1], sample_list[i][0])
    dest_node = ox.distance.nearest_nodes(graph, sample_list[i+1][1], sample_list[i+1][0])
    shortest_route = nx.shortest_path(graph, orig_node, dest_node)
    distance_travelled = 0
    route.append(shortest_route)

for r in route:
    for i in range(len(r)-1):
        node_data = graph.nodes[r[i]]
        next_node_data = graph.nodes[r[i+1]]
        distance_travelled += haversine(node_data['y'], node_data['x'], next_node_data['y'], next_node_data['x'])

                
map_center = (sample_list[0][0], sample_list[0][1])

map_obj = folium.Map(location=sample_list[0], zoom_start=12)
add_markers(map_obj, sample_list)

# route_coordinates = []
# for node in route:
#     for i in node:
#         node_data = graph.nodes[i]
#         route_coordinates.append([node_data['y'], node_data['x']])
# folium.PolyLine(locations=route_coordinates, color="blue").add_to(map_obj)

for r in route:
    # Pass color to polyline_opts
    polyline_opts = {"color": "red"}
    ox.plot_route_folium(graph, r,route_map=map_obj, tiles='openstreetmap', polyline_opts=polyline_opts)



# Save the map to an HTML file and open it in a web browser
map_obj.save('multiple_routes_map.html')
webbrowser.open("multiple_routes_map.html")

