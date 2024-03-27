import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import networkx as nx
import shapely
import folium
import geojson
import math
import osmnx as ox
import random

from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from geopy.distance import geodesic

# For units
def degrees_to_meters(angle_degrees):
    return angle_degrees * 6371000 * math.pi / 180

def meters_to_degrees(distance_meters):
    return distance_meters / 6371000 * 180 / math.pi

def create_network(amenities_polygon_gdf, amenities_point_gdf):
    amenities_network = nx.Graph()

   # Add polygon nodes
    for index, row in amenities_polygon_gdf.iterrows():
        # Check if essential columns exist in the row
        if 'geometry' in row and 'amenity' in row and 'name' in row and 'addr_city' in row and 'amenity_points' in row:
            # Generate a unique node identifier for polygons
            node_id = f"polygon_{index}"
            amenities_network.add_node(node_id, polygon_index=index, geometry=row['geometry'], lat=row['geometry'].centroid.y, lon=row['geometry'].centroid.x, amenity=row['amenity'], name=row.get('name', ''), addr_city=row['addr_city'], amenity_points=row['amenity_points'])
        else:
            print(f"Skipping row {index} in amenities_polygon_gdf due to missing data.")

    # Add point nodes
    for index, row in amenities_point_gdf.iterrows():
        # Check if essential columns exist in the row
        if 'geometry' in row and 'amenity' in row and 'name' in row and 'addr_city' in row:
            # Generate a unique node identifier for points
            node_id = f"point_{index}"
            amenities_network.add_node(node_id, point_index=index, geometry=row['geometry'], lat=row['y'], lon=row['x'], amenity=row['amenity'], name=row.get('name', ''), addr_city=row['addr_city'], is_in_polygon=False)
        else:
            print(f"Skipping row {index} in amenities_point_gdf due to missing data.")
            
    return amenities_network

# TEMPORARY SOLUTION FOR NULL NAMES
def combine_names(name1, name2):
    # Combine names ensuring that no null values are included
    if isinstance(name1, str) and isinstance(name2, str):
        return f"{name1}, {name2}"
    elif isinstance(name1, str):
        return name1
    elif isinstance(name2, str):
        return name2
    else:
        return None
        
connected_lines = []

#FUNCTION FOR VISUALIZATION
def connect_polygon_lines(p1, p2, connected_lines):
    centroid1 = p1.centroid
    centroid2 = p2.centroid

    # Create a LineString from the centroids
    line_between_polygons = LineString([centroid1, centroid2])
    connected_lines.append(line_between_polygons)


def find_intersecting_roads(line, filtered_roads_strings, filtered_roads_lists, separation_options):
    for index, row in filtered_roads_strings.iterrows():
        if line.intersects(row['geometry']):
            if row['highway'] in separation_options:
                print("Road found: ", row['name'])
                return True

    for index, row in filtered_roads_lists.iterrows():
        if line.intersects(row['geometry']):
            list_highway = row['highway']
            if any(x in separation_options for x in list_highway):
                print("Road found: ", row['name'])
                return True
                
    print("NO BIG ROADS")
    return False

# V3
# Lines version - Non-Merging
# Creates a copy of a graph and connects non-contiguous and non-overlapping shapes instead of merging

def combine_amenities_by_polygon(graph, max_distance, max_perimeter):
    combined_graph = nx.Graph()
    list_to_merge = []
    
    for node_key, node_data in list(graph.nodes.items()):
        if 'geometry' in node_data and node_data['geometry'].geom_type in ['Polygon', 'MultiPolygon']:
            nodes_to_merge = []
            contained_points = []
            
            # Add this node to the list as default
            nodes_to_merge.append((node_key, 0))
            
            for other_node_key, other_node_data in list(graph.nodes.items()):
                
                if 'geometry' in other_node_data and other_node_data['geometry'].geom_type in ['Polygon', 'MultiPolygon']:
                    # Check if its not the same node, it is the same amenity, and is not already in the list to merge
                    if node_key != other_node_key and node_data['amenity'] == other_node_data['amenity']:
                        
                        distance = degrees_to_meters(node_data['geometry'].distance(other_node_data['geometry']))

                        # Check if they are within distance of each other
                        if distance <= max_distance:

                            # Check if any other amenities intersect the line between centroids
                            line_between_centroids = LineString([node_data['geometry'].centroid, other_node_data['geometry'].centroid])
                            amenities_intersecting = any(graph.nodes[amenity_key]['geometry'].intersects(line_between_centroids) for amenity_key in graph.nodes if amenity_key != node_key and amenity_key != other_node_key)
                            print("Polygons: ", node_data['name'], ", ", other_node_data['name']) 
                            # If no other amenities intersecting and if there is no big road in the middle
                            if not amenities_intersecting and not find_intersecting_roads(line_between_centroids):    
                                nodes_to_merge.append((other_node_key, distance))
                                
                                # Checks if contiguous, if not add a line - FOR VISUALIZATION
                                if not graph.nodes[node_key]['geometry'].intersects(graph.nodes[other_node_key]['geometry']):
                                    connect_polygon_lines(node_data['geometry'], other_node_data['geometry'])
                
                elif 'geometry' in other_node_data and other_node_data['geometry'].geom_type == 'Point':
                    #Add the point to the new graph if it is not there yet
                    if other_node_key not in combined_graph.nodes:
                        combined_graph.add_node(other_node_key, **other_node_data)
                        
                    if node_data['geometry'].intersects(other_node_data['geometry']) and not other_node_data.get('is_in_polygon', False):
                        contained_points.append(other_node_key)
            
            nodes_to_merge.sort(key=lambda x: x[1])
            list_to_merge.append(nodes_to_merge) # Add to the list to connect the polygons later

            for point_key in contained_points:
                graph.nodes[point_key]['is_in_polygon'] = True
    
    
    # Now we will finally connect all polygons in the list
    nodes_added = [] # TO make sure there are no duplicates
    for merge_list in list_to_merge:
        first = True
        added = False
        for node_key, distance in merge_list:
            if node_key not in nodes_added:
                if first:
                    combined_node_amenity = graph.nodes[node_key]['amenity']
                    combined_node_key = node_key
                    combined_node_geometry = graph.nodes[node_key]['geometry']
                    combined_node_name = graph.nodes[node_key]['name']
                    combined_node_lat = graph.nodes[node_key]['lat']
                    combined_node_lon = graph.nodes[node_key]['lon']
                    combined_node_points = graph.nodes[node_key]['amenity_points']
                    nodes_added.append(node_key)
                    first = False
                    added = True
                else:
                    combined_node = shapely.ops.unary_union([combined_node_geometry, graph.nodes[node_key]['geometry']])
                    if degrees_to_meters(combined_node.length) < max_perimeter:
                        combined_node_geometry = combined_node
                        combined_node_name = combine_names(combined_node_name, graph.nodes[node_key].get('name'))
                        combined_node_lat = combined_node_geometry.centroid.x
                        combined_node_lon = combined_node_geometry.centroid.x
                        combined_node_points += graph.nodes[node_key].get('amenity_points', 0)
                        nodes_added.append(node_key)
                    else:
                        break
                        
        if added:
            combined_graph.add_node(combined_node_key, geometry=combined_node_geometry, name=combined_node_name, lat=combined_node_lat, amenity=combined_node_amenity,
                                    lon=combined_node_lon, amenity_points=combined_node_points)

    return combined_graph

# To merge duplicates in lists
def to_graph(nodes):
    G = nx.Graph()
    for part in nodes:
        G.add_nodes_from(part)
        G.add_edges_from(to_edges(part))

    return G

def to_edges(nodes):
    it = iter(nodes)
    last = next(it)

    for current in it:
        yield last, current
        last = current
        
def graph_to_list(G):
    connected_components = nx.connected_components(G)
    lists = [list(component) for component in connected_components]

    return lists

def generate_graph():
    place = 'Manila, Philippines'
    mode = 'drive'
    graph = ox.graph_from_place(place, network_type = mode) # Generate graph of Metro manila
    ox.save_graphml(graph, 'map/Manila.graphml') # Save it as a file

def load_graph():
    graph = ox.load_graphml('map/Manila.graphml')
    
    print("Graph loaded successfully")
    print("NUMBER OF EDGES: ", graph.number_of_edges())
    print("NUMBER OF NODES: ", graph.number_of_nodes())
    print('\n')
    return graph

def plot_network_on_map(amenities_network, initial_location=[0, 0], zoom_start=10):
    # Create a map centered at the initial location
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles='openstreetmap')
    
    #Colours for Visualization
    amenity_colors = {
        'education': 'green',
        'finance': 'blue',
        'government offices': 'red',
        'grocery': 'orange',
        'health': 'magenta',
        'malls': 'yellow',
        'residential areas': 'brown',
        'security': 'gray'
    }

    # Iterate over the nodes in the network
    for node, data in amenities_network.nodes(data=True):
        # Check if the node has a geometry attribute
        if 'geometry' in data:
            # Get the geometry of the node
            geometry = data['geometry']

            # Check the geometry type and plot accordingly
            if geometry.geom_type == 'Point':
                # Plot a marker for points    
                #folium.Marker(location=[geometry.y, geometry.x], popup=f"{data['name']}").add_to(m)
                continue
            elif geometry.geom_type in ['Polygon', 'MultiPolygon']:
                # Plot polygons or multipolygons
                color = amenity_colors[data.get('amenity')]
                if geometry.geom_type == 'Polygon':
                    polygons = [geometry]
                else:
                    polygons = geometry.geoms

                for polygon in polygons:
                    coordinates = []
                    for point in polygon.exterior.coords:
                        coordinates.append([point[1], point[0]])
                    folium.Polygon(locations=coordinates, fill=True, color=color, fill_opacity=0.4).add_to(m)

    # Return the map
    return m

# Uses the combined graph
# Formula: Population Density = Total Population / Total Area

def check_residential_population_density(graph, population_gdf, threshold):
    # Create an empty array to store points
    points = []
    
    pop_graph = nx.Graph()
    for index, row in population_gdf.iterrows():
        # Append the point to the points array
        points.append((row['latitude'], row['longitude'], row['phl_general_2020']))
    
    
    nodes = []
    for node_key, node_data in list(graph.nodes.items()):
        # Check if its a polygon and is a residential area
        if 'geometry' in node_data and node_data['geometry'].geom_type in ['Polygon', 'MultiPolygon'] and node_data['amenity'] == "residential areas":
            total_pop = 0
            
            for point in points:
                if Point(point[1], point[0]).within(node_data['geometry']):
                    total_pop += point[2] # Add the density
                    points.remove(point)
            
            density = total_pop / node_data['geometry'].area
            
            if (density > 0):
                node_data["is_a_zone"] = True
            else:
                node_data["is_a_zone"] = False
                
            nodes.append((node_key, density))
            pop_graph.add_node(node_key, **node_data)
                
    return pop_graph

# This is to better visualize which residential areas can become zones
def plot_population_zones_map(graph, initial_location=[0, 0], zoom_start=10):
    # Create a map centered at the initial location
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles='openstreetmap')

    # Iterate over the nodes in the network
    for node, data in graph.nodes(data=True):
        # Check if the node has a geometry attribute
        if 'geometry' in data:
            # Get the geometry of the node
            geometry = data['geometry']

            # Check the geometry type and plot accordingly
            if geometry.geom_type == 'Point':
                # Plot a marker for points    
                #folium.Marker(location=[geometry.y, geometry.x], popup=f"{data['name']}").add_to(m)
                continue
            elif geometry.geom_type in ['Polygon', 'MultiPolygon']:
                if geometry.geom_type == 'Polygon':
                    polygons = [geometry]
                else:
                    polygons = geometry.geoms

                for polygon in polygons:
                    coordinates = []
                    for point in polygon.exterior.coords:
                        coordinates.append([point[1], point[0]])
                    
                    if (data['is_a_zone']):
                        folium.Polygon(locations=coordinates, fill=True, color="green", fill_opacity=0.4).add_to(m)
                    else:
                        folium.Polygon(locations=coordinates, fill=True, color="red", fill_opacity=0.4).add_to(m)

    # Return the map
    return m

# V2
# Function to connect zones in a network
def create_zone_network(graph, max_distance, pop_graph):
    connect_graph = nx.Graph()
    network_id = 1
    list_to_connect = []
    
    for node_key, node_data in list(graph.nodes.items()):
        if 'geometry' in node_data and node_data['geometry'].geom_type in ['Polygon', 'MultiPolygon']:
            connect_nodes = []
            
            #Check first if it is already in a list of polygons to be connected
            for connect_list in list_to_connect:
                if node_key in connect_list:
                    connect_nodes = connect_list
                    break
            
            # If this is a new node that is not part of any list, add itself to the list for merging later
            if not connect_nodes:
                connect_nodes.append(node_key)
                
            # If this is not a res
            if node_key not in pop_graph or not pop_graph.nodes[node_key]['is_a_zone']:
                for other_node_key, other_node_data in list(graph.nodes.items()):
                    if 'geometry' in other_node_data and other_node_data['geometry'].geom_type in ['Polygon', 'MultiPolygon']:
                        if node_key != other_node_key:

                            distance = degrees_to_meters(node_data['geometry'].distance(other_node_data['geometry']))

                            # Check if they are within distance of each other
                            if distance <= max_distance:
                                line_between_centroids = LineString([node_data['geometry'].centroid, other_node_data['geometry'].centroid])
                                amenities_intersecting = any(graph.nodes[amenity_key]['geometry'].intersects(line_between_centroids) for amenity_key in graph.nodes if amenity_key != node_key and amenity_key != other_node_key)
                                if not amenities_intersecting and not find_intersecting_roads(line_between_centroids):
                                    if other_node_key not in pop_graph or not pop_graph.nodes[other_node_key]['is_a_zone']:
                                        connect_nodes.append(other_node_key)
                                
            if connect_nodes not in list_to_connect:
                list_to_connect.append(connect_nodes) # Add to the list to merge the polygons later
                
    temp_graph = to_graph(list_to_connect)
    lists = graph_to_list(temp_graph)

                
    # Connect them to one network
    for network in lists:
        for node_key in network:
            if node_key not in connect_graph.nodes:
                node_attributes = graph.nodes[node_key]
                node_attributes["network_id"] = network_id
                connect_graph.add_node(node_key, **node_attributes)
        network_id += 1
                
    return connect_graph

# This is to better visualize the networks
def plot_connected_zones_network_on_map(graph, initial_location=[0, 0], zoom_start=10):
    # Create a map centered at the initial location
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles='openstreetmap')
    
    #Colours for Visualization
    colors = [
    "Red", "Green", "Blue", "Yellow", "Orange", "Purple", "Cyan", "Magenta", "Maroon",
    "Olive", "Lime", "Teal", "Navy", "Aqua", "Fuchsia", "Coral", "Indigo", "Violet"]
    
    color_map = {}

    # Iterate over the nodes in the network
    for node, data in graph.nodes(data=True):
        # Check if the node has a geometry attribute
        if 'geometry' in data:
            # Get the geometry of the node
            geometry = data['geometry']

            # Check the geometry type and plot accordingly
            if geometry.geom_type == 'Point':
                # Plot a marker for points    
                #folium.Marker(location=[geometry.y, geometry.x], popup=f"{data['name']}").add_to(m)
                continue
            elif geometry.geom_type in ['Polygon', 'MultiPolygon']:
                
                network_id = data["network_id"]
                
                if network_id not in color_map:
                    color = random.choice(colors)
                    color_map[network_id] = color
                else:
                    color = color_map[network_id]
                
                if geometry.geom_type == 'Polygon':
                    polygons = [geometry]
                else:
                    polygons = geometry.geoms

                for polygon in polygons:
                    coordinates = []
                    for point in polygon.exterior.coords:
                        coordinates.append([point[1], point[0]])
                    folium.Polygon(locations=coordinates, fill=True, color=color, fill_opacity=0.4).add_to(m)

    # Return the map
    return m

# Extract the graph into a geojson for loading into QGIS
def graph_to_geojson(graph, filename):
    # Initialize an empty list to hold GeoJSON features
    features = []

    # Iterate over the nodes in the graph
    for node, data in graph.nodes(data=True):
        # Check if the node has a geometry attribute
        if 'geometry' in data:
            # Convert the geometry to a GeoJSON-compatible format
            geometry = shapely.geometry.shape(data['geometry'])
            # Create a copy of the properties to check for NaN values
            properties = data.copy()
            # Remove the geometry from the properties
            properties.pop('geometry', None)
            # Check for NaN values in the properties
            if all(not (isinstance(value, float) and np.isnan(value)) for value in properties.values()):
                # Create a GeoJSON feature for the node
                feature = geojson.Feature(geometry=geometry, properties=properties)
                # Add the feature to the list
                features.append(feature)

    # Create a GeoJSON FeatureCollection
    feature_collection = geojson.FeatureCollection(features)

    # Return the GeoJSON FeatureCollection
    return feature_collection