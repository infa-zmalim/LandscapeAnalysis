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

def get_pod_count_per_deployment_for_all_clusters():
    # Load clusters from clusters.yaml
    with open('resources/clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

    for cluster in clusters:
        # Update kubeconfig for the current cluster
        run_command(cluster["config"])

        # Fetch all namespaces
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        all_deployments = {}

        # Iterate over each namespace
        for namespace_item in namespaces_json['items']:
            namespace_name = namespace_item['metadata']['name']

            # Get deployments in the namespace
            deployments_output = run_command(f"kubectl get deployments -n {namespace_name} -o json")
            deployments_json = json.loads(deployments_output)

            # Extract the deployment name and desired replicas
            for deployment in deployments_json['items']:
                deployment_name = deployment['metadata']['name']
                desired_replicas = deployment['spec'].get('replicas', 0)
                all_deployments[deployment_name] = all_deployments.get(deployment_name, 0) + desired_replicas

        # Sort by replica count
        sorted_deployments = sorted(all_deployments.items(), key=lambda x: x[1], reverse=True)

        # Print results for the current cluster
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")
        for deployment, count in sorted_deployments:
            print(f"  DeploymentName: {deployment}, PodCount: {count}")
        print("\n")

if __name__ == "__main__":
    get_pod_count_per_deployment_for_all_clusters()
