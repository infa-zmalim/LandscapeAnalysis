import re
import yaml
import json

from Kubernetes.utils import run_command


def get_resources_for_all_clusters():
    # Load clusters from clusters.yaml
    with open('resources/NON-PROD_clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

    for cluster in clusters:
        # Update kubeconfig for the current cluster
        run_command(cluster["config"])

        service_resources = {}

        # Fetch all namespaces
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

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

                # Get pods of the deployment
                pods_output = run_command(f"kubectl get pods -l app={deployment_name} -n {namespace_name} -o json")
                pods_json = json.loads(pods_output)

                for pod in pods_json['items']:
                    for container in pod['spec']['containers']:
                        requests = container['resources'].get('requests', {})
                        cpu_request = requests.get('cpu', '0')
                        memory_request = requests.get('memory', '0')

                        if service_name not in service_resources:
                            service_resources[service_name] = {"cpu": 0, "memory": 0}

                        service_resources[service_name]["cpu"] += float(cpu_request.rstrip('m')) if 'm' in cpu_request else float(cpu_request) * 1000
                        service_resources[service_name]["memory"] += float(memory_request.rstrip('Mi')) if 'Mi' in memory_request else float(memory_request.rstrip('Gi')) * 1024

        # Print results for the current cluster
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")
        for service, resources in service_resources.items():
            print(f"  ServiceName: {service}, Total CPU Requests (in millicores): {resources['cpu']}, Total Memory Requests (in MiB): {resources['memory']}")
        print("\n")

if __name__ == "__main__":
    get_resources_for_all_clusters()
