# TeamCity VCS Integration Script

## Overview
This script generates a CSV report of all TeamCity builds and their associated VCS repositories. It connects to the TeamCity REST API to extract build configurations and their linked version control systems.

## Usage

### Basic Usage
```bash
python3 teamcity-vcs.py > builds_report.csv
```

### Environment Variables
The script requires the following environment variables:

- `TEAMCITY_ACCESS_TOKEN` (required): TeamCity access token for authentication
- `TEAMCITY_BASE_URL` (optional): TeamCity server base URL 
  - Default: `http://your-teamcity-server.local/app/rest`

### Example
```bash
export TEAMCITY_ACCESS_TOKEN="your_token_here"
python3 teamcity-vcs.py > builds_report.csv
```

## Output Format
The script generates a CSV file with the following columns:
- **Build ID**: TeamCity build configuration ID
- **Build Name**: Human-readable build configuration name
- **VCS Root Name**: Name of the associated VCS repository

### Sample Output
```csv
Build ID,Build Name,VCS Root Name
ProjectA_Build1,Project A Build 1,VCS-Repo-1
ProjectA_Build2,Project A Build 2,VCS-Repo-1
ProjectB_Build1,Project B Build 1,VCS-Repo-2
```

## Dependencies
- Python 3.6+
- `requests` library

Install dependencies:
```bash
pip install requests
```

## Error Handling
The script includes comprehensive error handling:
- Network connectivity issues
- Authentication failures
- Missing or invalid build configurations
- API rate limiting

Errors are logged to stderr while the CSV output continues to stdout.

## Security Notes
- Never hardcode access tokens in the script
- Use environment variables for sensitive configuration
- Ensure the access token has appropriate read-only permissions
- Consider using a dedicated service account for API access

## Changelog

### Version 2.0 (Current)
- **BREAKING**: Removed all dead code and unused functions
- **SECURITY**: Moved access token to environment variable
- **PERFORMANCE**: Simplified API calls, removed redundant tree traversal
- **RELIABILITY**: Added comprehensive error handling
- **MAINTENANCE**: Reduced code complexity by 70%

### Removed Features
- Complex project tree traversal (`traverse_projects`, `traverse_projects_with_vcs_type`)
- VCS type detection (`get_vcs_type`, `get_vcs_info`)
- Hierarchical project structure building (`build_project_tree`)
- Debug output functions (`print_build_details`)

### Migration Notes
If you were using the previous version's tree traversal features, this version focuses solely on generating the CSV report. The output format remains the same.
