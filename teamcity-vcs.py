"""TeamCity VCS Integration Script

Generates a CSV report of all TeamCity builds and their associated VCS repositories.

Usage:
    python teamcity-vcs.py > builds_report.csv

Environment Variables:
    TEAMCITY_BASE_URL: TeamCity server base URL (default: http://your-teamcity-server.local/app/rest)
    TEAMCITY_ACCESS_TOKEN: TeamCity access token for authentication
"""

import csv
import os
import sys
import requests

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

def get_vcs_root_name(vcs_root_id):
    """Get the name of a VCS root."""
    try:
        resp = requests.get(f"{BASE_URL}/vcs-roots/id:{vcs_root_id}", headers=HEADERS)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("name")
    except requests.RequestException:
        return None


def get_all_build_details():
    """Get all build details with VCS roots for updating builds.
    
    Returns:
        List of tuples: (build_id, build_name, vcs_root_name)
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
                            vcs_name = get_vcs_root_name(vcs_id)
                            if vcs_name:
                                build_details.add((build_id, build_name, vcs_name))
                else:
                    # No VCS roots found for this build
                    build_details.add((build_id, build_name, "No VCS Root"))
                    
        except Exception as e:
            print(f"Error processing project {project['name']}: {e}")
            continue
    
    return list(build_details)


def main():
    """Generate CSV report of all builds and their VCS roots."""
    # Get all build details
    build_details = get_all_build_details()
    
    # Create CSV writer
    writer = csv.writer(sys.stdout)
    
    # Write CSV header
    writer.writerow(["Build ID", "Build Name", "VCS Root Name"])
    
    # Write build data
    for build_id, build_name, vcs_root_name in sorted(build_details):
        writer.writerow([build_id, build_name, vcs_root_name])

if __name__ == "__main__":
    main()