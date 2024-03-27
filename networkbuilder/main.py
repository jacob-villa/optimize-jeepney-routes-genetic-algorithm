import pandas as pd
import geopandas as gpd
from shapely import wkt
import osmnx as ox
import folium
import geojson

# Modules
import polygon_helper
import network_generator
import road_helper

# Load amenity data
manila_amenities_df = pd.read_csv('manila_amenities.csv')
manila_amenities_df['geometry'] = manila_amenities_df['geometry'].apply(wkt.loads)
manila_amenities_gdf = gpd.GeoDataFrame(manila_amenities_df, crs='epsg:3123')

# Load population data
manila_population_df = pd.read_csv('manila-population-polygon.csv')
manila_population_df['geometry'] = manila_population_df['geometry'].apply(wkt.loads)
manila_population_gdf = gpd.GeoDataFrame(manila_population_df, crs='epsg:3123')

# Split into polygon and point gdf
manila_amenities_polygon_gdf, manila_amenities_point_gdf = polygon_helper.split_gdf_by_geometry_type(manila_amenities_gdf)
# Store the point amenities into the polygon gdf
manila_amenities_polygon_gdf = polygon_helper.store_points_in_polygons(manila_amenities_polygon_gdf, manila_amenities_point_gdf)

# Creating Initial network
manila_amenities_network = network_generator.create_network(manila_amenities_polygon_gdf, manila_amenities_point_gdf)

# Make a before map
before_map = network_generator.plot_network_on_map(manila_amenities_network, initial_location=[0, 0], zoom_start=100)
before_map.save('before_map.html') # Save the map to an HTML file

# Load graph from graphml file
network_generator.generate_graph()
graph = network_generator.load_graph()

# Get all roads in Manila
manila_road = ox.graph_to_gdfs(graph,nodes=False, edges=True)

# Get all the roads that are not junctions (ex. Roundabouts, intersection, etc.)
filtered_roads = manila_road[manila_road['junction'].isna()]

# Separate roads whose widths are only one value and those that are more than 1 (lists)
rows_with_lists = filtered_roads[filtered_roads['highway'].apply(lambda x: isinstance(x, list))]
rows_with_strings = filtered_roads[filtered_roads['highway'].apply(lambda x: isinstance(x, str))]

filter_options = ['primary', 'secondary', 'tertiary', 'trunk', 'unclassified']
separation_options = ['primary', 'secondary', 'tertiary', 'unclassified']

# Get all the roads with set widths (Widths that are not null)
filtered_roads_strings = rows_with_strings.loc[rows_with_strings['highway'].isin(filter_options)] 
filtered_roads_lists = rows_with_lists[rows_with_lists['highway'].apply(road_helper.check_list)]

# Connecting polygons of same amenity
combined_graph = network_generator.combine_amenities_by_polygon(manila_amenities_network, max_distance=100, max_perimeter=10000)
after_map = network_generator.plot_network_on_map(combined_graph, initial_location=[0, 0], zoom_start=100)
connected_lines = network_generator.connected_lines

# The lines to show the networks
for line in connected_lines:
    line_coords = [[coord[1], coord[0]] for coord in line.coords]
    folium.PolyLine(locations=line_coords, color='black').add_to(after_map)
after_map.save('after_map.html') # Save the map to an HTML file

# Checking the population density of residential areas
threshold = 100
pop_graph = network_generator.check_residential_population_density(graph=combined_graph, population_gdf=manila_population_gdf, threshold=threshold)
pop_map = network_generator.plot_population_zones_map(pop_graph, initial_location=[0, 0], zoom_start=100)
#pop_map.save('pop_map.html') # Save the map to an HTML file

# Create a network of amenities
graph_networks_of_polygons = network_generator.create_zone_network(graph=combined_graph, max_distance=100, pop_graph=pop_graph)
networks_map = network_generator.plot_connected_zones_network_on_map(graph_networks_of_polygons, initial_location=[0, 0], zoom_start=100)
networks_map.save('networks_map.html') # Save the map to an HTML file

feature_collection = network_generator.graph_to_geojson(manila_amenities_network, 'output.geojson')
with open('output.geojson', 'w', encoding='utf-8') as f:
    f.write(geojson.dumps(feature_collection, indent=2))

# FOR VISUALIZATION ONLY
all_roads_map = road_helper.plot_all_roads(filtered_roads_strings, filtered_roads_lists)
all_roads_map.save('all_roads.html')

filtered_road_map = road_helper.plot_all_filtered_roads()
filtered_road_map.save('filtered_road_map.html')