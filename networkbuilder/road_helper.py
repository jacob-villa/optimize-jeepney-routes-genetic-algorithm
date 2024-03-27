import pandas as pd
import geopandas as gpd
import folium

# For filtering the roads
#Plotting filtered roads FOR VISUALIZATION ONLY
def plot_all_filtered_roads(filtered_roads_strings, filtered_roads_lists):
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=10, tiles='openstreetmap')

    # Iterate through each road
    for index, road in filtered_roads_strings.iterrows():
        line_coords = list(road['geometry'].coords)

        if road['highway'] == 'primary':
            folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='blue').add_to(m)

        if road['highway'] == 'secondary':
            folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='red').add_to(m)

        if road['highway'] == 'tertiary':
            folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='green').add_to(m)

        if road['highway'] == 'unclassified':
            folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='orange').add_to(m)

    for index, road in filtered_roads_lists.iterrows():
        line_coords = list(road['geometry'].coords)
        folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='purple').add_to(m)

    # Return the map
    return m

def plot_all_roads(roads_df):
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=10, tiles='openstreetmap')

    # Iterate through each road
    for index, road in roads_df.iterrows():
        line_coords = list(road['geometry'].coords)
        folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='blue').add_to(m)

    # Return the map
    return m

# TEMPORARY TO BE REMOVED
def plot_private_roads(private_roads_df):
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=10, tiles='openstreetmap')

    # Iterate through each road
    for index, road in private_roads_df.iterrows():
        line_coords = list(road['geometry'].coords)
        folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='blue').add_to(m)

    # Return the map
    return m

# TEMPORARY TO BE REMOVED
def plot_walk(walk_roads_df):
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=10, tiles='openstreetmap')

    # Iterate through each road
    for index, road in walk_roads_df.iterrows():
        line_coords = list(road['geometry'].coords)
        folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='blue').add_to(m)

    # Return the map
    return m
    
# TEMPORARY TO BE REMOVED
def plot_bike(bike_roads_df):
    map_center = (14.599512, 120.984222) # TEMPORARY WILL ZOOM TO MANILA
    m = folium.Map(location=map_center, zoom_start=10, tiles='openstreetmap')

    # Iterate through each road
    for index, road in bike_roads_df.iterrows():
        line_coords = list(road['geometry'].coords)
        folium.PolyLine(locations=[(y, x) for x, y in line_coords], color='blue').add_to(m)

    # Return the map
    return m

# Get the roads whose widths are above the threshold
def check_list(lst, filter_options):
    return any(x in filter_options for x in lst)