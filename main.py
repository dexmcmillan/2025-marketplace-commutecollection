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
    Calls the Google Routes API for a list of routes and saves to CSV.

    Args:
        routes: A list of tuples, where each tuple contains an origin,
                a destination string (e.g., "Disneyland", "Universal Studios Hollywood"),
                and a travel mode.
        project_id: The Google Cloud project ID to use for billing.
        bucket_name: The Google Cloud Storage bucket to upload the file to.
        output_filename_prefix: The prefix for the output CSV file.
    """
    # Authenticate using gcloud user credentials.
    # Ensure you have run "gcloud auth application-default login"
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

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{output_filename_prefix}_{timestamp_str}.csv"
    
    # Use gcsfs to write directly to the GCS bucket
    gcs = gcsfs.GCSFileSystem(project=project_id, token=credentials)
    gcs_path = f"gs://{bucket_name}/{output_filename}"

    rows_to_write = []
    header = ["origin", "destination", "travel_mode", "distance_km", "duration_min", "warnings", "line_geometry", "timestamp"]
    rows_to_write.append(header)

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
                # The field mask is used to specify which fields to return in the response.
                # https://developers.google.com/maps/documentation/routes/reference/rpc/google.maps.routing.v2/routes.service#computeroutes
                metadata=[('x-goog-fieldmask', 'routes.duration,routes.distanceMeters,routes.warnings,routes.polyline.encodedPolyline')]
            )
            # Assuming at least one route is found
            if response.routes:
                route = response.routes[0]
                distance_km = route.distance_meters / 1000
                duration_min = int(route.duration.seconds / 60)
                warnings = "; ".join(route.warnings) if route.warnings else ""
                
                line_geometry = ""
                if route.polyline and route.polyline.encoded_polyline:
                    decoded_polyline = polyline.decode(route.polyline.encoded_polyline)
                    # WKT LINESTRING format is "LINESTRING (lon1 lat1, lon2 lat2, ...)"
                    line_geometry = f"LINESTRING ({', '.join([f'{lon} {lat}' for lat, lon in decoded_polyline])})"
                
                timestamp = datetime.now().isoformat()
                rows_to_write.append([origin, destination, travel_mode, f"{distance_km:.2f}", duration_min, warnings, line_geometry, timestamp])
            else:
                timestamp = datetime.now().isoformat()
                rows_to_write.append([origin, destination, travel_mode, "N/A", "N/A", "No routes found", "", timestamp])

        except Exception as e:
            timestamp = datetime.now().isoformat()
            rows_to_write.append([origin, destination, travel_mode, "N/A", "N/A", f"Error: {e}", "", timestamp])

    with gcs.open(gcs_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(rows_to_write)
    
    print(f"Done. Results saved to {gcs_path}")

## No main() function needed. This file is now a library for the timezone scripts.
