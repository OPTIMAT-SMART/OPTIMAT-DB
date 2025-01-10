"""
Script to generate GeoJSON files for services and their respective cities.

This script uses the Overpass API for OpenStreetMap to fetch precise city boundaries 
and generate GeoJSON files. Each service in the dictionary is assigned its own GeoJSON 
file, saved in a directory named `service_zones`. The script is modular and ensures 
code reusability and efficiency.

Modules:
    - fetch_city_boundary: Fetches city boundary data from the Overpass API.
    - extract_coordinates: Extracts polygon coordinates from Overpass API data.
    - generate_geojson: Generates a GeoJSON object for a list of cities.
    - save_geojson_file: Saves a GeoJSON object to a file.
    - main: Orchestrates the process and creates files for all services.

Dependencies:
    - requests
    - json
    - os
    - time
    - geopy

Usage:
    Run the script directly. It will generate the `service_zones` directory and save GeoJSON 
    files for each service in the dictionary.
"""

import requests
import json
import os
import time
from geopy import geocoders
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim

# Path Configuration
ZONES_DIR = "service_zones"
SERVICES_FILE = "services.json"
OUTPUT_DIR = os.path.join(ZONES_DIR, "zones2")

# Construct absolute paths
SERVICES_PATH = os.path.join(ZONES_DIR, SERVICES_FILE)
OUTPUT_PATH = OUTPUT_DIR

def clean_polygon_geometry(geojson_geometry):
    """
    Clean and validate polygon geometry for Leaflet display.
    - Ensures polygons are closed (first point = last point)
    - Removes any invalid coordinates
    - Converts MultiPolygon to single polygon if needed
    """
    if not geojson_geometry or 'coordinates' not in geojson_geometry:
        return None

    def is_valid_coord(coord):
        return (len(coord) >= 2 and 
                isinstance(coord[0], (int, float)) and 
                isinstance(coord[1], (int, float)) and 
                -180 <= coord[0] <= 180 and 
                -90 <= coord[1] <= 90)

    def close_ring(ring):
        if not ring:
            return ring
        # Filter out invalid coordinates
        ring = [coord for coord in ring if is_valid_coord(coord)]
        if not ring:
            return None
        # Ensure the ring is closed
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        return ring

    cleaned_coords = []
    coordinates = geojson_geometry['coordinates']

    # Handle both Polygon and MultiPolygon
    if geojson_geometry['type'] == 'Polygon':
        coordinates = [coordinates]
    
    for polygon in coordinates:
        cleaned_polygon = []
        # Clean outer ring
        outer_ring = close_ring(polygon[0])
        if outer_ring:
            cleaned_polygon.append(outer_ring)
            # Clean holes (inner rings)
            for hole in polygon[1:]:
                cleaned_hole = close_ring(hole)
                if cleaned_hole:
                    cleaned_polygon.append(cleaned_hole)
            if cleaned_polygon:
                cleaned_coords.append(cleaned_polygon)

    return {
        "type": "MultiPolygon" if len(cleaned_coords) > 1 else "Polygon",
        "coordinates": cleaned_coords if len(cleaned_coords) > 1 else cleaned_coords[0]
    }

def fetch_city_boundary(city_name, country="USA"):
    """
    Fetch city boundary (polygon) data using Nominatim API.

    Args:
        city_name (str): Name of the city.
        country (str): Country where the city is located.

    Returns:
        dict or None: GeoJSON geometry for the city boundary.
    """
    geolocator = Nominatim(user_agent="my_service_zones_app")
    
    try:
        # Search for the city with full name including country
        location = geolocator.geocode(
            f"{city_name}, California, {country}",
            exactly_one=True,
            geometry='geojson'
        )
        
        if location and location.raw.get('geojson'):
            # Clean the geometry before returning
            cleaned_geometry = clean_polygon_geometry(location.raw['geojson'])
            return cleaned_geometry
        else:
            print(f"Boundary not found for {city_name}")
            return None
            
    except Exception as e:
        print(f"Error fetching data for {city_name}: {str(e)}")
        return None

def extract_coordinates(relation, elements):
    """
    Extract polygon coordinates from Overpass API data.

    Args:
        relation (dict): Relation data containing the boundary.
        elements (list): List of elements from Overpass API response.

    Returns:
        list: List of coordinates (longitude, latitude).
    """
    nodes = {el["id"]: el for el in elements if el["type"] == "node"}
    way_coordinates = []

    for member in relation["members"]:
        if member["type"] == "way":
            way = next((el for el in elements if el["type"] == "way" and el["id"] == member["ref"]), None)
            if way:
                way_coordinates.extend([(nodes[node]["lon"], nodes[node]["lat"]) for node in way["nodes"]])

    # Ensure the coordinates form a closed loop
    if way_coordinates and way_coordinates[0] != way_coordinates[-1]:
        way_coordinates.append(way_coordinates[0])
    return way_coordinates

def generate_geojson(service_name, cities):
    """
    Generate a GeoJSON file with precise city boundaries for a service.

    Args:
        service_name (str): Name of the service.
        cities (list): List of city names.

    Returns:
        dict: GeoJSON FeatureCollection.
    """
    features = []
    for city in cities:
        print(f"Fetching boundary for: {city} (Service: {service_name})")
        boundary = fetch_city_boundary(city)
        if boundary:
            features.append({
                "type": "Feature",
                "geometry": boundary,
                "properties": {"name": city}
            })
        time.sleep(1)  # Respect Nominatim's rate limit

    return {
        "type": "FeatureCollection",
        "features": features
    }

def save_geojson_file(service_name, geojson_data, output_dir=OUTPUT_PATH):
    """
    Save a GeoJSON object to a file.

    Args:
        service_name (str): Name of the service.
        geojson_data (dict): GeoJSON object.
        output_dir (str): Directory to save the files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"{service_name.replace(' ', '_')}.geojson")
    with open(file_path, "w") as f:
        json.dump(geojson_data, f, indent=2)
    print(f"GeoJSON file created: {file_path}")

def main():
    """
    Main function to generate GeoJSON files for all services in the dictionary.
    """
    # Load services from configuration file
    services = json.load(open(SERVICES_PATH))

    # Generate GeoJSON for each service
    for service_name, cities in services.items():
        geojson_data = generate_geojson(service_name, cities)
        save_geojson_file(service_name, geojson_data)

if __name__ == "__main__":
    main()