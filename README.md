# TeamCity VCS Integration Script

## Overview
This script provides tools for managing TeamCity build configurations and their associated VCS repositories. It connects to the TeamCity REST API to extract, report, and update build configurations and their linked version control systems.

## Features
- Generate CSV reports of builds and their VCS roots
- Generate CSV reports of projects and their VCS roots
- Update VCS root properties for projects from a CSV file
- Attach or detach VCS roots from builds using a CSV file

## Usage

### Environment Variables
The script requires the following environment variables:

- `TEAMCITY_ACCESS_TOKEN` (required): TeamCity access token for authentication
- `TEAMCITY_BASE_URL` (optional): TeamCity server base URL 
  - Default: `http://your-teamcity-server.local/app/rest`

### Command-Line Arguments

```
usage: teamcity-vcs.py [-h] [--builds | --projects | --update-projects | --update-builds] [--input-file INPUT_FILE]

TeamCity VCS Integration Script

options:
  -h, --help            show this help message and exit
  --builds              List all build configurations and their VCS roots (default)
  --projects            List all projects and their VCS roots
  --update-projects     Update projects' VCS roots from CSV file
  --update-builds       Update VCS roots for builds from CSV file (attach or detach)
  --input-file INPUT_FILE
                        Specify input CSV file for updates
```

### Basic Usage Examples

#### Generate a report of all builds and their VCS roots
```bash
python teamcity-vcs.py > builds_report.csv
```
or explicitly:
```bash
python teamcity-vcs.py --builds > builds_report.csv
```

#### Generate a report of all projects and their VCS roots
```bash
python teamcity-vcs.py --projects > projects_report.csv
```

#### Update projects' VCS roots from a CSV file
```bash
python teamcity-vcs.py --update-projects --input-file projects.csv
```

#### Update builds' VCS roots from a CSV file
```bash
python teamcity-vcs.py --update-builds --input-file builds.csv
```

## CSV Formats

### Output Format: Builds Report (--builds)
The script generates a CSV file with the following columns:
- **Build ID**: TeamCity build configuration ID
- **Build Name**: Human-readable build configuration name
- **VCS Root ID**: ID of the associated VCS repository
- **VCS Root Name**: Name of the associated VCS repository

#### Sample Output (Builds)
```csv
Build ID,Build Name,VCS Root ID,VCS Root Name
ProjectA_Build1,Project A Build 1,VcsRoot_1,VCS-Repo-1
ProjectA_Build2,Project A Build 2,VcsRoot_1,VCS-Repo-1
ProjectB_Build1,Project B Build 1,VcsRoot_2,VCS-Repo-2
```

### Output Format: Projects Report (--projects)
The script generates a CSV file with the following columns:
- **Project ID**: TeamCity project ID
- **Project Name**: Human-readable project name
- **VCS Root ID**: ID of the associated VCS repository
- **VCS Root Name**: Name of the associated VCS repository
- **Fetch URL**: URL of the VCS repository
- **Default Branch**: Default branch of the VCS repository

#### Sample Output (Projects)
```csv
Project ID,Project Name,VCS Root ID,VCS Root Name,Fetch URL,Default Branch
ProjectA,Project A,VcsRoot_1,VCS-Repo-1,https://github.com/example/repo-a.git,main
ProjectB,Project B,VcsRoot_2,VCS-Repo-2,https://github.com/example/repo-b.git,master
```

### Input Format: Update Projects (--update-projects)
The CSV file should have the following columns:
- **Project ID**: TeamCity project ID
- **VCS Root ID**: ID of the VCS repository to update
- **Fetch URL** (optional): New fetch URL for the VCS repository
- **Default Branch** (optional): New default branch for the VCS repository

#### Sample Input (Update Projects)
```csv
Project ID,VCS Root ID,Fetch URL,Default Branch
ProjectA,VcsRoot_1,https://github.com/example/new-repo-a.git,develop
ProjectB,VcsRoot_2,,main
```

### Input Format: Update Builds (--update-builds)
The CSV file should have the following columns:
- **Build ID**: TeamCity build configuration ID
- **VCS Root ID**: ID of the VCS repository
- **Action** (optional): Action to perform (A: Attach, D: Detach, default is A)

#### Sample Input (Update Builds)
```csv
Build ID,VCS Root ID,Action
ProjectA_Build1,VcsRoot_1,A
ProjectA_Build2,VcsRoot_2,A
ProjectB_Build1,VcsRoot_1,D
```

## Dependencies
- Python 3.6+
- `requests` >= 2.25.0
- `urllib3` >= 1.26.0, < 2.0.0

Install dependencies:
```bash
pip install -r requirements.txt
```

## Error Handling
The script includes comprehensive error handling:
- Network connectivity issues
- Authentication failures
- Missing or invalid build configurations
- API rate limiting
- Invalid CSV formats

Errors are logged to stderr while the CSV output continues to stdout.

## Security Notes
- Never hardcode access tokens in the script
- Use environment variables for sensitive configuration
- Ensure the access token has appropriate permissions
- Consider using a dedicated service account for API access