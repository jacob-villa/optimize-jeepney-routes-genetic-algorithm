import pandas as pd
import geopandas as gpd


def split_gdf_by_geometry_type(amenities_gdf):
    amenities_polygon_gdf = amenities_gdf[amenities_gdf['geometry'].geom_type == 'Polygon']
    amenities_point_gdf = amenities_gdf[amenities_gdf['geometry'].geom_type == 'Point']
    amenities_multipoly_gdf = amenities_gdf[amenities_gdf['geometry'].geom_type == 'MultiPolygon']
    
    # Append multipolygons to the polygon dataframe
    amenities_polygon_gdf = gpd.GeoDataFrame(pd.concat([amenities_polygon_gdf, amenities_multipoly_gdf], ignore_index=True))

    # Reset point dataframe index
    amenities_point_gdf.reset_index(drop=True, inplace=True)

    # Add a column to the polygon dataframe to store a list of Amenity Points within the polygon
    amenities_polygon_gdf['amenity_points'] = None

    return amenities_polygon_gdf, amenities_point_gdf

def store_points_in_polygons(amenities_polygon_gdf, amenities_point_gdf):
    # For each polygon in the polygon dataframe, find all the points from the point dataframe lying inside that polygon
    # Store the list of points in the 'amenity_points' column of the polygon dataframe as a list of point indices
    for i, polygon in amenities_polygon_gdf.iterrows():
        points_within_polygon = []

        for j, point in amenities_point_gdf.iterrows():
            try:
                if polygon['geometry'].intersects(point['geometry']):
                    # Append the index of the current point
                    points_within_polygon.append(j)
            except Exception as e:
                print(f"Error processing polygon {i} point {j}: {e}")
        amenities_polygon_gdf.at[i, 'amenity_points'] = points_within_polygon

    return amenities_polygon_gdf