# Pacific Time Zone: Surrey, Victoria
import pandas as pd
import sys
import os

# Add the parent directory to the path to import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import get_commute_routes

PACIFIC_CITIES = ['Surrey', 'Victoria']

def get_routes_from_csv(file_path):
    """Reads commute routes from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        # Ensure required columns exist
        required_columns = ['origin', 'destination', 'travel_mode', 'city']
        if not all(col in df.columns for col in required_columns):
            print(f"Error: Missing one or more required columns in the CSV file: {required_columns}")
            return []
        
        # gspread can return empty strings for empty cells, so check for that.
        filtered_df = df[
            (df['origin'].astype(str).str.strip() != '') &
            (df['destination'].astype(str).str.strip() != '') &
            (df['travel_mode'].astype(str).str.strip() != '') &
            (df['city'].astype(str).str.strip() != '')
        ].copy()

        return list(zip(filtered_df['origin'], filtered_df['destination'], filtered_df['travel_mode'], filtered_df['city']))
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return []

def filter_routes_by_city(routes):
    return [route for route in routes if route[3] in PACIFIC_CITIES]

if __name__ == "__main__":
    csv_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'commute_routes.csv'))
    all_routes = get_routes_from_csv(csv_file)
    pacific_routes = filter_routes_by_city(all_routes)
    project_id = "dig-es-nws-gemini-projects"
    bucket_name = "marketplace-commutes"
    if pacific_routes:
        # Strip the city from the tuples before passing to get_commute_routes
        routes_to_process = [(r[0], r[1], r[2]) for r in pacific_routes]
        print(f"Found {len(routes_to_process)} routes for the Pacific time zone.")
        get_commute_routes(routes_to_process, project_id, bucket_name, output_filename_prefix="commute_routes_pacific")
    else:
        print("No routes found for the Pacific time zone.")
