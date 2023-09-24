import json
import yaml
import re

from Kubernetes.utils import run_command


def get_pod_count_per_service_for_all_clusters():
    # Load clusters from clusters.yaml
    with open('resources/clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

    for cluster in clusters:
        # Update kubeconfig for the current cluster
        run_command(cluster["config"])

        # Fetch all namespaces
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        service_pod_counts = {}

        # Iterate over each namespace
        for namespace_item in namespaces_json['items']:
            namespace_name = namespace_item['metadata']['name']

            # Get deployments in the namespace
            deployments_output = run_command(f"kubectl get deployments -n {namespace_name} -o json")
            deployments_json = json.loads(deployments_output)

            # Extract the deployment name and desired replicas
            for deployment in deployments_json['items']:
                deployment_name = deployment['metadata']['name']
                # Extracting service name from deployment name
                service_name = re.sub(r'-\d+-\d+-\d+-\d+$', '', deployment_name)
                desired_replicas = deployment['spec'].get('replicas', 0)
                service_pod_counts[service_name] = service_pod_counts.get(service_name, 0) + desired_replicas

        # Sort by replica count
        sorted_services = sorted(service_pod_counts.items(), key=lambda x: x[1], reverse=True)

        # Print results for the current cluster
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")
        for service, count in sorted_services:
            print(f"  ServiceName: {service}, PodCount: {count}")
        print("\n")

if __name__ == "__main__":
    get_pod_count_per_service_for_all_clusters()

