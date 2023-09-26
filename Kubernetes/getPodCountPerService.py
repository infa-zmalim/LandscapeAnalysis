import json
import re
from prettytable import PrettyTable
from Kubernetes.utils.utils import run_command, clusters


def get_pod_count_per_service_for_all_clusters():
    for cluster in clusters:
        # Update kubeconfig for the current cluster
        run_command(cluster["config"])

        # Fetch all namespaces
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        # Initialize a list to store service pod count along with namespace and service name
        service_pod_counts = []

        # Iterate over each namespace
        for namespace_item in namespaces_json['items']:
            namespace_name = namespace_item['metadata']['name']

            # Get deployments in the namespace
            deployments_output = run_command(f"kubectl get deployments -n {namespace_name} -o json")
            deployments_json = json.loads(deployments_output)

            # Extract the deployment name, namespace name and desired replicas
            for deployment in deployments_json['items']:
                deployment_name = deployment['metadata']['name']
                # Extracting service name from deployment name
                service_name = re.sub(r'-\d+-\d+-\d+-\d+$', '', deployment_name)
                desired_replicas = deployment['spec'].get('replicas', 0)

                # Append the details to the service_pod_counts list
                service_pod_counts.append({
                    "Namespace": namespace_name,
                    "ServiceName": service_name,
                    "PodCount": desired_replicas
                })

        # Sort the list by PodCount
        sorted_services = sorted(service_pod_counts, key=lambda x: x["PodCount"], reverse=True)

        # Create and print PrettyTable for the current cluster
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")

        table = PrettyTable()
        table.field_names = ["Namespace", "ServiceName", "PodCount"]
        for service in sorted_services:
            table.add_row([service["Namespace"], service["ServiceName"], service["PodCount"]])

        print(table)
        print("\n")

if __name__ == "__main__":
    get_pod_count_per_service_for_all_clusters()
