import subprocess
import json
import yaml
import re
from collections import Counter

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error and "No resources found" not in error.decode('utf-8'):
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')

def get_service_names_from_pods_for_all_clusters():
    # Load clusters from clusters.yaml
    with open('resources/clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

    for cluster in clusters:
        # Update kubeconfig for the current cluster
        run_command(cluster["config"])

        # Fetch all namespaces
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        all_service_names = []

        # Iterate over each namespace
        for namespace_item in namespaces_json['items']:
            namespace_name = namespace_item['metadata']['name']

            # Get pods in the namespace
            pods_output = run_command(f"kubectl get pods -n {namespace_name}")
            lines = pods_output.strip().split('\n')[1:]  # Skip header

            # Extract the service name
            for line in lines:
                pod_name = line.split()[0]
                service_name = re.sub(r'-\w{7}-\w{5}$', '', pod_name)
                service_name = '-'.join(service_name.split('-')[:3])
                all_service_names.append(service_name)

        # Count occurrences of each service name
        counter = Counter(all_service_names)
        sorted_services = sorted(counter.items(), key=lambda x: x[1], reverse=True)

        # Print results for the current cluster
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")
        for service, count in sorted_services:
            print(f"  ServiceName: {service}, Count: {count}")
        print("\n")

if __name__ == "__main__":
    get_service_names_from_pods_for_all_clusters()
