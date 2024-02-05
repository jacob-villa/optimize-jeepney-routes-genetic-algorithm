import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2
import webbrowser
import folium


ox.settings.log_console=True
ox.settings.use_cache=True

sample_list = [[14.549782711255753, 121.00515608352754],[14.549163881741926, 121.00433654028181], [14.54816721998631, 121.00252036521498],
               [14.547892358182233, 120.99867935257014], [14.548951532876389, 120.99845743761652], [14.54975898911636, 120.99826284183357]]


# IF FIRST TIME RUNNING, RUN THIS CODE TO GENERATE THE GRAPH
#place     = 'Metro Manila, Philippines'
#mode      = 'drive'

#graph = ox.graph_from_place(place, network_type = mode) # Generate graph of Metro manila
#ox.save_graphml(graph, './map/MetroManila.graphml') # Save it as a file


# Load the graph from the file
graph = ox.load_graphml('./map/MetroManila.graphml')
# Plot the road network graph with larger nodes
#fig, ax = ox.plot_graph(graph, node_size=10, bgcolor='k', show=False, close=False)

print("Graph loaded successfully")
print("NUMBER OF EDGES: ", graph.number_of_edges())
print("NUMBER OF NODES: ", graph.number_of_nodes())
print('\n')

map_center = (sample_list[0][0], sample_list[0][1])
m = folium.Map(location=map_center, zoom_start=15, tiles='openstreetmap')

routes = []
optimizer = 'time'
for i in range(len(sample_list)-1):
    print("Calculating route from", sample_list[i], "to", sample_list[i+1])
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
        
rc = ['r', 'y', 'c', 'm', 'g']
fig, ax = ox.plot_graph_routes(graph, routes, route_colors=rc, route_linewidth=6, node_size=0)


#m.save("shortest_route_map.html")
# Open the HTML file in a web browser to view the map
#webbrowser.open("shortest_route_map.html")
    







# TO CALCULATE DISTANCE
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = 6371 * c  # Radius of earth in kilometers
    return distance



