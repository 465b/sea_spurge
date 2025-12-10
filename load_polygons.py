import numpy as np
import json
import pandas as pd
from shapely.geometry import Point, Polygon

from oceantracker.util.cord_transforms import WGS84_to_NZTM
from oceantracker.util.cord_transforms import NZTM_to_WGS84

from simplify_polygons import simplify_polygons

# reading the geojson provided by rafael (oceanintelligence) - 01.09.2025
list_of_new_zealands_coastal_polygons = [
    {
        "name": "NI",
        "long_name": "North Island",
        "path": "./coastal_polygons/polygons_ni_20250827.geojson"
    },
    {
        "name": "SI",
        "long_name": "South Island",
        "path": "./coastal_polygons/polygons_si_20250901.geojson"
    },
    {
        "name": "RI",
        "long_name": "Rakiura Island",
        "path": "./coastal_polygons/polygons_ri_20250901.geojson"
    },
    {
        "name": "EI",
        "long_name": "Extra Islands",
        "path": "./coastal_polygons/polygons_nz_extra_islands.geojson"
    }
]


list_of_marine_reserve_polygons = [
    {
        "name": "MR",
        "long_name": "Marine Reserves",
        "path": "./coastal_polygons/marine_reserves_ballast.geojson"
    },
]


list_of_australian_polygons = [
    {
        "name": "AU",
        "long_name": "Australia Main Island",
        "path": "./coastal_polygons/polygons_australia_20250925.geojson"
    },
    {
        "name": "TA",
        "long_name": "Australia Tasmania Island",
        "path": "./coastal_polygons/polygons_tasmania_20250926.geojson"
    },
]

list_of_sea_spurge_sampling_locations = [
    {
        "path": "./coastal_polygons/sampling_locations.geojson"
    }
]

def load_polygons(list_of_geojsons,source_projection, target_projection, simplify_tolerance=None):
    """
    Load polygons from a list of geojson files, optionally transform coordinates and simplify them.
    Args:
        list_of_geojsons (list): List of dictionaries with keys 'name', 'long_name', and 'path' to geojson files.
        transform_from_WGS84_to_NZTM (bool): Whether to transform coordinates from WGS84 to NZTM. Default is True.
        simplify_tolerance (float or None): Tolerance in the units of the coordinate system for polygon simplification. I.e. typically either degrees (lat,lon) or metersIf None, no simplification is applied. Default is None.
    Returns:
        list: List of processed polygons.
    """
    

    # check if source and target projection are given, if not throw an error

    polygons = read_coastal_polygons_from_geojson(list_of_geojsons)

    if source_projection == target_projection:
        pass
    elif source_projection == "WGS84" and target_projection == "NZTM":
        # Transform them from WGS84 (deg lon lat) to NZTM (meter lon lat)
        for poly in polygons:
            # Transform coordinates from WGS84 to NZTM
            poly['points'] = WGS84_to_NZTM(np.array(poly['points']))
            poly['points'] = poly['points'].tolist()
    elif source_projection == "NZTM" and target_projection == "WGS84":
        # Transform them from NZTM (meter lon lat) to WGS84 (deg lon lat)
        for poly in polygons:
            # Transform coordinates from NZTM to WGS84
            poly['points'] = NZTM_to_WGS84(np.array(poly['points']))
            poly['points'] = poly['points'].tolist()
    else:
        raise ValueError("Unsupported source and target projection combination. Supported combinations are: WGS84 to NZTM and NZTM to WGS84.")
    

    if simplify_tolerance is not None:
        polygons = simplify_polygons(polygons, tolerance=simplify_tolerance)

    return polygons


def read_coastal_polygons_from_geojson(list_of_geojsons,warnings=False):
    """
    Read polygons from a list of geojson files and return them in OceanTracker format.
    Args:
        list_of_geojsons (list): List of dictionaries with keys 'name', 'long_name', and 'path' to geojson files.
    Returns:
        list: List of polygons in OceanTracker format.
    """

    coastal_polygons = []
    for file in list_of_geojsons:
        with open(file['path'], 'r') as f:
            geojson_data = json.load(f)

        tmp = True
        for ii,feature in enumerate(geojson_data['features']):
            if (feature['geometry']['type'] == 'Polygon') \
                or (feature['geometry']['type'] == 'MultiPolygon'):
                
                coordinates = feature['geometry']['coordinates']

                # try: # south island and south south island don't have IDs..
                #     id = feature['properties']['fid']
                id = ii    


                try:
                    # Multipolygon
                    if len(np.array(coordinates[0][0]).shape) == 2:
                        points = coordinates[0][0]
                        # if len (coordinates[0]) > 1:
                        #     print(f"Proper Multipolygon {ii}")
                        #     for jj,subpoly in enumerate(coordinates[0]):
                        #         print(f"Vertex count of subpoly {jj}: {'.'*len(subpoly)} ")

                    # Polygon
                    elif len(np.array(coordinates[0]).shape) == 2:
                        points = coordinates[0]
                    # Weird? Throw error for the time being
                    else:
                        IndexError
                        
                    coastal_polygons.append(
                        {
                            "name": f"{file['long_name']}_{id}",
                            "points": points
                        }
                    )
                except IndexError:
                    if len(coordinates) == 0:
                        if warnings:
                            print(f"Warning: Skipping polygon with fid {id} in {file['long_name']} because it is empty.")
                    else:
                        if warnings:
                            print(f"Warning: Skipping polygon with fid {id} in {file['long_name']} due faulty coordinates.")

                # except KeyError:
                #     print(f'Warning: Skipping polygon without fid in dataset {file['long_name']}')


    return coastal_polygons


def read_marine_reserve_polygons_from_geojson(list_of_geojsons, names_of_polygons_to_read=None):
    """
    Read polygons from a list of geojson files and return them in OceanTracker format.
    Args:
        list_of_geojsons (list): List of dictionaries with keys 'name', 'long_name', and 'path' to geojson files.
        names_of_polygons_to_read (list, optional): List of polygon names to read. If None, all polygons are read.
    Returns:
        list: List of polygons in OceanTracker format.
    """

    coastal_polygons = []
    for file in list_of_geojsons:
        with open(file['path'], 'r') as f:
            geojson_data = json.load(f)

        for feature in geojson_data['features']:
            if feature['geometry']['type'] == 'Polygon':
                if feature['properties']['RegionName'] not in names_of_polygons_to_read:
                    continue

                region_name = feature['properties']['RegionName']
                coordinates = feature['geometry']['coordinates']
                
                try:
                    id = feature['properties']['ORIG_FID']
                except KeyError:
                    print('Warning: Skipping polygon without fid')

                try:
                    coastal_polygons.append(
                        {
                            "name": f"{region_name}_{id}",
                            "points": coordinates[0]
                        }
                    )
                except IndexError:
                    print(f"Warning: Skipping polygon with fid {id} in {file['long_name']} due to missing coordinates.")

    return coastal_polygons



# malcolms method to read from pickle
def create_catch_polys_from_df(df):
    # # Load the processed polygon data
    # df = pd.read_pickle(r'/hpcfreenas/malc/PCEPlastics/polygon_data_with_coordinates.pkl')
    # print(f"Loaded {len(df)} polygons from {len(df['Region'].unique())} regions")
    # print(f"Regions: {df['Region'].unique()}")

    catchPolys = []
    
    for index, row in df.iterrows():
        # Skip SI_10 polygon if it exists
        if row["Name"] == 'SI_10':
            continue
            
        # Convert coordinates to the expected format
        xy = np.asarray(row['NZTM_Coordinates']).tolist()
        
        catchPolys.append({
            'points': xy, 
            'name': row["Name"].replace(' ', '_')
        })
    
    return catchPolys


def load_sampling_locations(list_of_geojsons):

    locations = []
    for file in list_of_geojsons:
        geojson_path = file["path"]

        with open(geojson_path, 'r') as f:
            data = json.load(f)
        
        for feature in data['features']:
            # Skip features with null geometry
            if feature['geometry'] is None:
                continue
                
            coords = feature['geometry']['coordinates']
            # Use 'code' field as name if available, otherwise use 'sample'
            properties = feature.get('properties', {})
            name = properties.get('code') or properties.get('sample') or f'Point_{len(locations)}'
            
            locations.append({
                'coordinates': coords,  # [lon, lat]
                'name': name
            })
    
    return locations


def find_containing_polygons(sampling_locations, coastal_polygons):
    """
    Find which coastal polygons contain the sampling locations.
    
    Parameters:
    -----------
    sampling_locations : list of dict
        List of sampling location dicts with 'coordinates' and 'name' keys
    coastal_polygons : list of dict
        List of polygon dicts with 'points' and 'name' keys
        
    Returns:
    --------
    list
        Sorted list of unique polygon indices that contain at least one sampling location
    """
    containing_polygon_indices = set()
    
    for location in sampling_locations:
        lon, lat = location['coordinates']
        point = Point(lon, lat)
        
        for idx, poly_dict in enumerate(coastal_polygons):
            # Create Shapely polygon from points
            polygon = Polygon(poly_dict['points'])
            
            # Check if point is within polygon
            if polygon.contains(point):
                containing_polygon_indices.add(idx)
    
    return sorted(list(containing_polygon_indices))


def prepare_polygons():
    nz_coastal_polygons = load_polygons(
    list_of_new_zealands_coastal_polygons,
    source_projection="WGS84",
    target_projection="WGS84",
    #  meter/
    simplify_tolerance=1000 / 1e5,
)
    au_coastal_polygons = load_polygons(
    list_of_australian_polygons,
    source_projection="WGS84",
    target_projection="WGS84",
    simplify_tolerance=5000 / 1e5,
)
    print("* polygons loaded")

# Find which polygons contain the sampling locations
# and slice for those
    sampling_locations = load_sampling_locations(list_of_sea_spurge_sampling_locations)
    au_sampled_subset = find_containing_polygons(sampling_locations, au_coastal_polygons)
    au_coastal_polygons = [au_coastal_polygons[poly] for poly in au_sampled_subset]
    print("* polygons sliced for known sampling locations")

# The original polygon set from Raf contained a bunch of ill defined polygons with 3 points in a line.
# They luckily are the only ones that have 3 points post "simplification", so we can just drop the
# three-points polies
    buggy_polygons = [
    ii for ii, item in enumerate(au_coastal_polygons) if len(item["points"]) < 4
]
    for index in sorted(buggy_polygons, reverse=True):
        au_coastal_polygons.pop(index)
    print("* removed ill-defined polygons")
    return nz_coastal_polygons,au_coastal_polygons