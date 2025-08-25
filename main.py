import os
import csv
import re
import polyline
import google.auth
import gspread
import pandas as pd
import gcsfs
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.maps.routing_v2 import RoutesClient
from google.maps.routing_v2.types import ComputeRoutesRequest, Waypoint
from datetime import datetime


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def authenticate_google_sheets():
    """Authenticates with Google Sheets API using OAuth 2.0."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json not found. Please download it from the Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_routes_from_google_sheet(sheet_url):
    """Reads and filters commute routes from a Google Sheet."""
    creds = authenticate_google_sheets()
    if not creds:
        return []
    
    gc = gspread.authorize(creds)
    
    try:
        spreadsheet = gc.open_by_url(sheet_url)
        worksheet = spreadsheet.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Check for required columns
        required_columns = ['start_location', 'end_location', 'commute_type', 'transportation_mode']
        if not all(col in df.columns for col in required_columns):
            print(f"Error: Missing one or more required columns in the Google Sheet: {required_columns}")
            return []

        # Filter the DataFrame
        # gspread can return empty strings for empty cells, so check for that.
        filtered_df = df[
            (df['commute_type'] == 'full commute') &
            (df['start_location'].astype(str).str.strip() != '') &
            (df['end_location'].astype(str).str.strip() != '') &
            (df['transportation_mode'].astype(str).str.strip() != '')
        ]
        
        return list(zip(filtered_df['start_location'], filtered_df['end_location'], filtered_df['transportation_mode']))
            
    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet not found. Please check the URL and your permissions.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the Google Sheet: {e}")
        return []

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

def main():
    sheet_url = "https://docs.google.com/spreadsheets/d/17VkS5Z81iI2HdpsDdPjMFAKpqzm2kgfRbYlG5ODfDZk/edit?gid=0#gid=0"
    commute_routes = get_routes_from_google_sheet(sheet_url)

    if not commute_routes:
        print("Could not retrieve routes from Google Sheet. Exiting.")
        return

    project_id = "dig-es-nws-gemini-projects" # <--- CHANGE THIS
    bucket_name = "marketplace-commutes" # <--- CHANGE THIS
    if project_id == "your-google-cloud-project-id":
        print("Please change the project_id variable in main.py")
        return
    if bucket_name == "your-gcs-bucket-name":
        print("Please change the bucket_name variable in main.py")
        return

    print("Hello from 2025-marketplace-commuteroutes!")
    print(f"Found {len(commute_routes)} routes in the Google Sheet.")
    print("Fetching commute routes...")
    get_commute_routes(commute_routes, project_id, bucket_name)


if __name__ == "__main__":
    main()
