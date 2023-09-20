import subprocess
import re
from collections import Counter
import yaml

with open('resources/clusters.yaml', 'r') as file:
    clusters = yaml.safe_load(file)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error:
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')

def get_service_names(namespace):
    # Fetch deployments from Kubernetes namespace
    cmd_output = run_command(f"kubectl get deployment -n {namespace}")

    # Split the output by lines and skip the header
    lines = cmd_output.split('\n')[1:]

    # Use regex to extract the service name
    service_names = [re.split('-\d+', line.split()[0])[0] for line in lines if line]

    # Count occurrences of each service name
    counter = Counter(service_names)

    # Sort by count
    sorted_services = sorted(counter.items(), key=lambda x: x[1], reverse=True)

    return sorted_services

def main():

    for cluster in clusters:
        # Update kubeconfig for the cluster
        run_command(cluster["config"])

        # Fetch and process service names for each namespace in the cluster
        for namespace in cluster["namespaces"]:
            results = get_service_names(namespace)
            # Determine the maximum length of the service names
            max_length = max(len(service) for service, _ in results)
            print(f"\n\n Results for namespace {namespace}:")
            for service, count in results:
                # Use the string format method to align the output
                print(f"{service},{' '*(max_length-len(service))}{count}")

if __name__ == "__main__":
    main()
