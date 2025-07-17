"""TeamCity VCS Integration Script

Generates reports about TeamCity builds and their associated VCS repositories.
Can also update TeamCity projects and builds from CSV files.

Usage:
    # Export data to CSV
    python teamcity-vcs.py [--projects] > report.csv
    
    # Import data from CSV
    python teamcity-vcs.py --update-projects --input-file=projects.csv
    python teamcity-vcs.py --update-builds --input-file=builds.csv

Options:
    # Export options
    --builds             List all build configurations and their VCS roots (default)
    --projects           List all projects and their VCS roots
    
    # Import options
    --update-projects    Update projects' VCS roots from CSV file
    --update-builds      Assign VCS roots to builds from CSV file
    --input-file FILE    Specify input CSV file for updates

Output:
    CSV with the following columns:
    - Project/Build ID
    - Project/Build Name
    - VCS Root ID
    - VCS Root Name
    - Fetch URL
    - Default Branch

Environment Variables:
    TEAMCITY_BASE_URL: TeamCity server base URL (default: http://your-teamcity-server.local/app/rest)
    TEAMCITY_ACCESS_TOKEN: TeamCity access token for authentication
"""

import csv
import os
import sys
import argparse
import requests
import warnings
from urllib3.exceptions import NotOpenSSLWarning

# Suppress specific urllib3 warning
warnings.filterwarnings('ignore', category=NotOpenSSLWarning)

# Configuration
BASE_URL = os.getenv("TEAMCITY_BASE_URL", "http://your-teamcity-server.local/app/rest")
ACCESS_TOKEN = os.getenv("TEAMCITY_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("Error: TEAMCITY_ACCESS_TOKEN environment variable is required", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}

def get_all_projects():
    """Get all projects in a flat list."""
    try:
        resp = requests.get(f"{BASE_URL}/projects", headers=HEADERS)
        resp.raise_for_status()
        return resp.json().get("project", [])
    except requests.RequestException as e:
        print(f"Error fetching projects: {e}", file=sys.stderr)
        return []

def get_build_types(project_id):
    """Get build types for a project."""
    try:
        resp = requests.get(f"{BASE_URL}/projects/id:{project_id}/buildTypes", headers=HEADERS)
        resp.raise_for_status()
        return resp.json().get("buildType", [])
    except requests.RequestException:
        return []

def get_vcs_root_entries(build_type_id):
    """Get VCS root entries for a build type."""
    try:
        resp = requests.get(f"{BASE_URL}/buildTypes/id:{build_type_id}/vcs-root-entries", headers=HEADERS)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json().get("vcs-root-entry", [])
    except requests.RequestException:
        return []

def get_vcs_root_details(vcs_root_id):
    """Get the details of a VCS root including name, fetch URL, and default branch.
    
    Args:
        vcs_root_id: The ID of the VCS root
        
    Returns:
        Tuple: (vcs_name, fetch_url, default_branch) or (None, None, None) if not found
    """
    try:
        resp = requests.get(f"{BASE_URL}/vcs-roots/id:{vcs_root_id}", headers=HEADERS)
        if resp.status_code == 404:
            return None, None, None
        resp.raise_for_status()
        data = resp.json()
        
        vcs_name = data.get("name")
        
        # Extract properties from the response
        properties = data.get("properties", {}).get("property", [])
        fetch_url = None
        default_branch = None
        
        for prop in properties:
            if prop.get("name") == "url":
                fetch_url = prop.get("value")
            elif prop.get("name") == "branch":
                default_branch = prop.get("value")
        
        return vcs_name, fetch_url, default_branch
    except requests.RequestException:
        return None, None, None

def get_vcs_root_name(vcs_root_id):
    """Get the name of a VCS root (legacy function)."""
    vcs_name, _, _ = get_vcs_root_details(vcs_root_id)
    return vcs_name


def get_all_build_details():
    """Get all build details with VCS roots for updating builds.
    
    Returns:
        List of tuples: (build_id, build_name, vcs_root_name, vcs_root_id)
    """
    build_details = set()  # Use set to automatically handle duplicates
    
    # Get all projects
    all_projects = get_all_projects()
    
    for project in all_projects:
        try:
            build_types = get_build_types(project['id'])
            
            for build_type in build_types:
                build_id = build_type['id']
                build_name = build_type['name']
                
                # Get VCS root entries for this build
                vcs_entries = get_vcs_root_entries(build_id)
                
                if vcs_entries:
                    for entry in vcs_entries:
                        vcs_id = entry.get("vcs-root", {}).get("id")
                        if vcs_id:
                            vcs_name, _, _ = get_vcs_root_details(vcs_id)
                            if vcs_name:
                                build_details.add((build_id, build_name, vcs_name, vcs_id))
                else:
                    # No VCS roots found for this build
                    build_details.add((build_id, build_name, "No VCS Root", "None"))
                    
        except Exception as e:
            print(f"Error processing project {project['name']}: {e}", file=sys.stderr)
            continue
    
    return list(build_details)


def get_all_projects_with_vcs_roots():
    """Get all projects with their VCS roots.
    
    Returns:
        List of tuples: (project_id, project_name, vcs_root_name, vcs_root_id, fetch_url, default_branch)
    """
    project_details = set()  # Use set to automatically handle duplicates
    
    # Get all projects
    all_projects = get_all_projects()
    
    for project in all_projects:
        try:
            project_id = project['id']
            project_name = project['name']
            
            # Get build types for this project
            build_types = get_build_types(project_id)
            
            vcs_roots_found = False
            
            # For each build type, get VCS roots
            for build_type in build_types:
                vcs_entries = get_vcs_root_entries(build_type['id'])
                
                if vcs_entries:
                    for entry in vcs_entries:
                        vcs_id = entry.get("vcs-root", {}).get("id")
                        if vcs_id:
                            vcs_name, fetch_url, default_branch = get_vcs_root_details(vcs_id)
                            if vcs_name:
                                project_details.add((project_id, project_name, vcs_name, vcs_id, fetch_url, default_branch))
                                vcs_roots_found = True
            
            # If no VCS roots were found for any build type in this project
            if not vcs_roots_found:
                project_details.add((project_id, project_name, "No VCS Root", "None", "None", "None"))
                
        except Exception as e:
            print(f"Error processing project {project['name']}: {e}")
            continue
    
    return list(project_details)

def read_projects_csv(file_path):
    """Read and validate a CSV file for updating projects.
    
    Expected CSV format:
    Project ID, Project Name, VCS Root ID, VCS Root Name, Fetch URL, Default Branch
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries with project update information
    """
    projects_data = []
    
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate header
            required_fields = ["Project ID", "VCS Root ID", "Fetch URL", "Default Branch"]
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            
            if missing_fields:
                print(f"Error: CSV file is missing required fields: {', '.join(missing_fields)}", file=sys.stderr)
                return []
            
            # Read and validate rows
            for row in reader:
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Validate required fields
                if not row["Project ID"] or not row["VCS Root ID"]:
                    print(f"Warning: Skipping row with missing Project ID or VCS Root ID: {row}", file=sys.stderr)
                    continue
                
                # Add to projects data
                projects_data.append({
                    "project_id": row["Project ID"],
                    "vcs_root_id": row["VCS Root ID"],
                    "fetch_url": row["Fetch URL"],
                    "default_branch": row["Default Branch"]
                })
    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
    
    return projects_data


def read_builds_csv(file_path):
    """Read and validate a CSV file for updating builds.
    
    Expected CSV format:
    Build ID, Build Name, VCS Root ID, VCS Root Name
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries with build update information
    """
    builds_data = []
    
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate header
            required_fields = ["Build ID", "VCS Root ID"]
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            
            if missing_fields:
                print(f"Error: CSV file is missing required fields: {', '.join(missing_fields)}", file=sys.stderr)
                return []
            
            # Read and validate rows
            for row in reader:
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Validate required fields
                if not row["Build ID"] or not row["VCS Root ID"]:
                    print(f"Warning: Skipping row with missing Build ID or VCS Root ID: {row}", file=sys.stderr)
                    continue
                
                # Add to builds data
                builds_data.append({
                    "build_id": row["Build ID"],
                    "vcs_root_id": row["VCS Root ID"]
                })
    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
    
    return builds_data


def update_vcs_root_properties(vcs_root_id, fetch_url=None, default_branch=None):
    """Update the properties of a VCS root.
    
    Args:
        vcs_root_id: The ID of the VCS root to update
        fetch_url: The new fetch URL (optional)
        default_branch: The new default branch (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Skip if both fetch_url and default_branch are None
    if fetch_url is None and default_branch is None:
        return True
    
    # Log high-level operation
    print(f"Updating VCS root: {vcs_root_id}")
    
    try:
        # First, get the current VCS root details
        resp = requests.get(f"{BASE_URL}/vcs-roots/id:{vcs_root_id}", headers=HEADERS)
        if resp.status_code == 404:
            print(f"Error: VCS root not found: {vcs_root_id}", file=sys.stderr)
            return False
        resp.raise_for_status()
        vcs_root_data = resp.json()
        
        # Get the current properties
        properties = vcs_root_data.get("properties", {})
        property_list = properties.get("property", [])
        
        # Update properties
        updated = False
        url_found = False
        branch_found = False
        
        # First, update existing properties
        for prop in property_list:
            if prop.get("name") == "url" and fetch_url is not None:
                prop["value"] = fetch_url
                updated = True
                url_found = True
            elif prop.get("name") == "branch" and default_branch is not None:
                prop["value"] = default_branch
                updated = True
                branch_found = True
        
        # Add properties if they don't exist
        if fetch_url is not None and not url_found:
            property_list.append({"name": "url", "value": fetch_url})
            updated = True
            
        if default_branch is not None and not branch_found:
            property_list.append({"name": "branch", "value": default_branch})
            updated = True
        
        # If no properties were updated, return early
        if not updated:
            return True
        
        # Prepare the update payload
        update_data = {
            "property": property_list
        }
        
        # Update the VCS root
        update_headers = HEADERS.copy()
        update_headers["Content-Type"] = "application/json"
        
        resp = requests.put(
            f"{BASE_URL}/vcs-roots/id:{vcs_root_id}/properties",
            headers=update_headers,
            json=update_data
        )
        
        resp.raise_for_status()
        
        print(f"Successfully updated VCS root: {vcs_root_id}")
        return True
        
    except requests.RequestException as e:
        print(f"Error updating VCS root {vcs_root_id}: {e}", file=sys.stderr)
        return False


def assign_vcs_root_to_build(build_id, vcs_root_id):
    """Assign a VCS root to a build configuration.
    
    Args:
        build_id: The ID of the build configuration
        vcs_root_id: The ID of the VCS root to assign
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First, check if the build exists
        resp = requests.get(f"{BASE_URL}/buildTypes/id:{build_id}", headers=HEADERS)
        if resp.status_code == 404:
            print(f"Error: Build configuration not found: {build_id}", file=sys.stderr)
            return False
        resp.raise_for_status()
        
        # Check if the VCS root exists
        resp = requests.get(f"{BASE_URL}/vcs-roots/id:{vcs_root_id}", headers=HEADERS)
        if resp.status_code == 404:
            print(f"Error: VCS root not found: {vcs_root_id}", file=sys.stderr)
            return False
        resp.raise_for_status()
        
        # Check if the VCS root is already attached to the build
        resp = requests.get(f"{BASE_URL}/buildTypes/id:{build_id}/vcs-root-entries", headers=HEADERS)
        resp.raise_for_status()
        vcs_entries = resp.json().get("vcs-root-entry", [])
        
        for entry in vcs_entries:
            if entry.get("vcs-root", {}).get("id") == vcs_root_id:
                print(f"VCS root {vcs_root_id} is already attached to build {build_id}")
                return True
        
        # Attach the VCS root to the build
        update_headers = HEADERS.copy()
        update_headers["Content-Type"] = "application/json"
        
        vcs_entry_data = {
            "vcs-root": {
                "id": vcs_root_id
            }
        }
        
        resp = requests.post(
            f"{BASE_URL}/buildTypes/id:{build_id}/vcs-root-entries",
            headers=update_headers,
            json=vcs_entry_data
        )
        resp.raise_for_status()
        
        print(f"Successfully assigned VCS root {vcs_root_id} to build {build_id}")
        return True
        
    except requests.RequestException as e:
        print(f"Error assigning VCS root {vcs_root_id} to build {build_id}: {e}", file=sys.stderr)
        return False


def update_projects_from_csv(file_path):
    """Update projects' VCS roots from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        tuple: (success_count, failure_count)
    """
    # Read and validate the CSV file
    projects_data = read_projects_csv(file_path)
    
    if not projects_data:
        print("No valid project data found in the CSV file", file=sys.stderr)
        return 0, 0
    
    success_count = 0
    failure_count = 0
    
    # Process each project
    for project in projects_data:
        project_id = project["project_id"]
        vcs_root_id = project["vcs_root_id"]
        fetch_url = project["fetch_url"]
        default_branch = project["default_branch"]
        
        # Skip if VCS root ID is "None"
        if vcs_root_id == "None":
            print(f"Skipping project {project_id} with no VCS root")
            continue
        
        # Update VCS root properties
        if update_vcs_root_properties(vcs_root_id, fetch_url, default_branch):
            success_count += 1
        else:
            failure_count += 1
    
    return success_count, failure_count


def update_builds_from_csv(file_path):
    """Assign VCS roots to builds from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        tuple: (success_count, failure_count)
    """
    # Read and validate the CSV file
    builds_data = read_builds_csv(file_path)
    
    if not builds_data:
        print("No valid build data found in the CSV file", file=sys.stderr)
        return 0, 0
    
    success_count = 0
    failure_count = 0
    
    # Process each build
    for build in builds_data:
        build_id = build["build_id"]
        vcs_root_id = build["vcs_root_id"]
        
        # Skip if VCS root ID is "None"
        if vcs_root_id == "None":
            print(f"Skipping build {build_id} with no VCS root")
            continue
        
        # Assign VCS root to build
        if assign_vcs_root_to_build(build_id, vcs_root_id):
            success_count += 1
        else:
            failure_count += 1
    
    return success_count, failure_count


def main():
    """Generate reports or update TeamCity based on command line arguments."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="TeamCity VCS Integration Script")
    
    # Create mode group (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--builds", action="store_true", help="List all build configurations and their VCS roots (default)")
    mode_group.add_argument("--projects", action="store_true", help="List all projects and their VCS roots")
    mode_group.add_argument("--update-projects", action="store_true", help="Update projects' VCS roots from CSV file")
    mode_group.add_argument("--update-builds", action="store_true", help="Assign VCS roots to builds from CSV file")
    
    # Add input file option for update modes
    parser.add_argument("--input-file", help="Specify input CSV file for updates")
    
    args = parser.parse_args()
    
    # Validate arguments
    if (args.update_projects or args.update_builds) and not args.input_file:
        print("Error: --input-file is required with --update-projects or --update-builds", file=sys.stderr)
        sys.exit(1)
    
    # Handle export modes (--builds or --projects)
    if not (args.update_projects or args.update_builds):
        # Create CSV writer for export
        writer = csv.writer(sys.stdout)
        
        # Default to builds mode if no arguments provided
        if args.projects:
            # Projects mode
            project_details = get_all_projects_with_vcs_roots()
            
            # Write CSV header
            writer.writerow(["Project ID", "Project Name", "VCS Root ID", "VCS Root Name", "Fetch URL", "Default Branch"])
            
            # Write project data
            for project_id, project_name, vcs_root_name, vcs_root_id, fetch_url, default_branch in sorted(project_details):
                writer.writerow([project_id, project_name, vcs_root_id, vcs_root_name, fetch_url, default_branch])
        else:
            # Builds mode (default)
            build_details = get_all_build_details()
            
            # Write CSV header
            writer.writerow(["Build ID", "Build Name", "VCS Root ID", "VCS Root Name"])
            
            # Write build data
            for build_id, build_name, vcs_root_name, vcs_root_id in sorted(build_details):
                writer.writerow([build_id, build_name, vcs_root_id, vcs_root_name])
    
    # Handle update modes
    else:
        if args.update_projects:
            # Update projects mode
            print(f"Updating projects from {args.input_file}...")
            success_count, failure_count = update_projects_from_csv(args.input_file)
            print(f"Update complete: {success_count} successful, {failure_count} failed")
        elif args.update_builds:
            # Update builds mode
            print(f"Updating builds from {args.input_file}...")
            success_count, failure_count = update_builds_from_csv(args.input_file)
            print(f"Update complete: {success_count} successful, {failure_count} failed")

if __name__ == "__main__":
    main()