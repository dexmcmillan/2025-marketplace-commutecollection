import os
import csv
import re
import polyline
import google.auth
import pandas as pd
import gcsfs
from google.maps.routing_v2 import RoutesClient
from google.maps.routing_v2.types import ComputeRoutesRequest, Waypoint
from datetime import datetime



def create_waypoint(place):
    """Creates a Waypoint object, detecting if 'place' is an address or lat/lng."""
    # Check if the place string is a lat,lng pair
    if isinstance(place, str) and re.match(r'^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$', place):
        try:
            lat_str, lng_str = place.split(',')
            lat = float(lat_str.strip())
            lng = float(lng_str.strip())
            return Waypoint(location={'lat_lng': {'latitude': lat, 'longitude': lng}})
        except (ValueError, TypeError):
            # Fallback to address if parsing fails for some reason
            return Waypoint(address=place)
    else:
        return Waypoint(address=place)

def get_commute_routes(routes, project_id, bucket_name, output_filename_prefix="commute_routes"):
    """
    Calls the Google Routes API for a list of routes and appends to a CSV in GCS.

    Args:
        routes: A list of tuples, where each tuple contains an origin,
                a destination string (e.g., "Disneyland", "Universal Studios Hollywood"),
                and a travel mode.
        project_id: The Google Cloud project ID to use for billing.
        bucket_name: The Google Cloud Storage bucket to upload the file to.
        output_filename_prefix: The prefix for the output CSV file.
    """
    # Authenticate using gcloud user credentials.
    try:
        credentials, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform'])
    except google.auth.exceptions.DefaultCredentialsError:
        print("Authentication failed. Please run 'gcloud auth application-default login' in your terminal.")
        return

    # Create a Routes client
    client = RoutesClient(
        credentials=credentials,
        client_options={"quota_project_id": project_id}
    )

    output_filename = f"{output_filename_prefix}.csv"
    
    # Use gcsfs to interact with the GCS bucket
    gcs = gcsfs.GCSFileSystem(project=project_id, token=credentials)
    gcs_path = f"gs://{bucket_name}/{output_filename}"

    new_rows = []
    header = ["origin", "destination", "travel_mode", "distance_km", "duration_min", "warnings", "line_geometry", "timestamp"]

    for origin, destination, travel_mode in routes:
        print(f"Processing route from {origin} to {destination} via {travel_mode}...")
        origin_waypoint = create_waypoint(origin)
        destination_waypoint = create_waypoint(destination)

        # Create a request for the route
        request = ComputeRoutesRequest(
            origin=origin_waypoint,
            destination=destination_waypoint,
            travel_mode=travel_mode.upper(),
        )
        if travel_mode.upper() == "DRIVE":
            request.routing_preference="TRAFFIC_AWARE"

        # Make the request
        try:
            response = client.compute_routes(
                request=request,
                metadata=[('x-goog-fieldmask', 'routes.duration,routes.distanceMeters,routes.warnings,routes.polyline.encodedPolyline')]
            )
            if response.routes:
                route = response.routes[0]
                distance_km = route.distance_meters / 1000
                duration_min = int(route.duration.seconds / 60)
                warnings = "; ".join(route.warnings) if route.warnings else ""
                
                line_geometry = ""
                if route.polyline and route.polyline.encoded_polyline:
                    decoded_polyline = polyline.decode(route.polyline.encoded_polyline)
                    line_geometry = f"LINESTRING ({', '.join([f'{lon} {lat}' for lat, lon in decoded_polyline])})"

                new_rows.append([
                    origin,
                    destination,
                    travel_mode,
                    distance_km,
                    duration_min,
                    warnings,
                    line_geometry,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
        except Exception as e:
            print(f"An error occurred during the Routes API call: {e}")

    if not new_rows:
        print("No new routes to add.")
        return

    # Create a DataFrame for the new data
    new_df = pd.DataFrame(new_rows, columns=header)

    # Check if the file already exists in GCS
    if gcs.exists(gcs_path):
        print(f"Appending data to existing file: {gcs_path}")
        # Read the existing data
        with gcs.open(gcs_path, 'r') as f:
            existing_df = pd.read_csv(f)
        
        # Append the new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        print(f"Creating new file: {gcs_path}")
        combined_df = new_df

    # Write the combined data back to GCS, overwriting the file
    with gcs.open(gcs_path, 'w', newline='') as f:
        combined_df.to_csv(f, index=False)
    
    print(f"Successfully wrote {len(new_df)} new routes to {gcs_path}")

## No main() function needed. This file is now a library for the timezone scripts.
