import os
import argparse
import json
import requests
import subprocess
import sys
from collections import defaultdict

def fetch_json_from_postman(api_key, uid, resource_type):
    headers = {'x-api-key': api_key}
    if resource_type == "collection":
        url = f"https://api.postman.com/collections/{uid}"
    elif resource_type == "workspace":
        url = f"https://api.postman.com/workspaces/{uid}"
    else:
        raise ValueError("Invalid resource type specified.")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def lint_json(file_path, ruleset_path):
    
    spectral_path = "/Users/bryancross/.nvm/versions/node/v18.18.0/bin/spectral" # Adjust this path
    try:
        result = subprocess.run(
            [spectral_path, "lint", file_path, "--ruleset", ruleset_path, "-f", "json"],
            capture_output=True, text=True
        )
        print(result.stdout);
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Spectral linting failed with error: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as j:
        print("Failed to decode JSON from Spectral output. Please check the output manually.")
        sys.exit(1)

def process_results(source_json, results):
    # Group errors by their message
    grouped_errors = defaultdict(list)
    for error in results:
        if error.get("severity", 0) >= 0:
            grouped_errors[error["message"]].append(error)

    # Format and print the results
    for message, errors in grouped_errors.items():
        print(f"\n{len(errors)} occurrences of: {message}\n")
        for error in errors:
            path = error["path"]
            try:
                # Traverse the JSON structure to find the parent object
                parent = source_json
                for key in path[:-1]:
                    if isinstance(parent, list):
                        key = int(key)
                    parent = parent[key]

                # Check if the final parent is a list or a dictionary
                if isinstance(parent, dict):
                    name = parent.get("name", None)
                else:
                    name = None

                if name:
                    print(f"Name: {name}")
                else:
                    print(f"Path: {'.'.join(path)}")
            except (KeyError, IndexError, TypeError) as e:
                print(f"Path: {'.'.join(path)}")
                print(f"Error accessing path: {e}")

def main():
    parser = argparse.ArgumentParser(description="Lint a Postman collection or workspace using Spectral rules.")
    parser.add_argument("-c", "--collection", help="Collection ID")
    parser.add_argument("-w", "--workspace", help="Workspace ID")
    parser.add_argument("-r", "--ruleset", help="Path to the ruleset")
    parser.add_argument("-p", "--path", help="Input file path (Collection only)")
    parser.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()

    if bool(args.collection) and bool(args.workspace):
        parser.error("You must specify either a collection ID (-c) or a workspace ID (-w), but not both.")
    if bool(args.collection) and (bool(args.path) or bool(args.workspace)):
        parser.error("You must specify a path to the input file or a postman UID, not both")
    

    api_key = os.getenv('POSTMAN_API_KEY')
    if not api_key:
        print("POSTMAN_API_KEY environment variable is not set.")
        sys.exit(1)

    resource_type = "collection" if (args.collection or args.path) else "workspace"
    uid = args.collection if args.collection else args.workspace
    source_json_file = f"_{resource_type}.json"
    #ruleset_path = "rules.yaml" if resource_type == "collection" else "workspacerules.yaml"
    if(args.ruleset):
        ruleset_path = args.ruleset
    else:
        ruleset_path = "./rulesets/collection-rules.yaml" if resource_type == "collection" else "./rulesets/rules.yaml"

    # Fetch JSON data from Postman API
    print("Fetching JSON data from Postman API...")
    if (args.collection or args.workspace):
        source_json = fetch_json_from_postman(api_key, uid, resource_type)
    elif(args.path):
        with open(args.path, "r") as f:
            source_json = json.load(f)

    # Save the source JSON to a file
    with open(source_json_file, "w") as f:
        json.dump(source_json, f, indent=4)

    # Lint the JSON file using Spectral
    print("Linting JSON data...")
    results = lint_json(source_json_file, ruleset_path)

    # If -o flag is set, save the raw results to a file
    if(args.output):
        with open(args.output, "w") as f:
            json.dump(results, f, indent=4)
    # Process the results and print the output
    print("Processing linting results...")
    process_results(source_json, results)
    

if __name__ == "__main__":
    main()
