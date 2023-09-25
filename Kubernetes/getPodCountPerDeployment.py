import json
import yaml
from prettytable import PrettyTable
from Kubernetes.utils import parse_cpu, parse_memory, run_command

def get_pod_count_and_resources_per_deployment_for_all_clusters():
    with open('resources/NON-PROD_clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

    services_with_different_limits_and_requests = []

    for cluster in clusters:
        run_command(cluster["config"])
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        all_deployments = {}

        for namespace_item in namespaces_json['items']:
            namespace_name = namespace_item['metadata']['name']
            deployments_output = run_command(f"kubectl get deployments -n {namespace_name} -o json")
            deployments_json = json.loads(deployments_output)

            for deployment in deployments_json['items']:
                deployment_name = deployment['metadata']['name']
                full_name = f"{namespace_name}/{deployment_name}"

                if full_name not in all_deployments:
                    all_deployments[full_name] = {
                        "count": 0, "cpu": 0, "memory": 0, "cpu_limit": 0, "memory_limit": 0}

                all_deployments[full_name]['count'] += deployment['spec'].get('replicas', 0)

                containers = deployment['spec']['template']['spec']['containers']
                for container in containers:
                    resources = container.get('resources', {})
                    requests = resources.get('requests', {})
                    limits = resources.get('limits', {})
                    cpu_request = parse_cpu(requests.get('cpu', '0'))
                    memory_request = parse_memory(requests.get('memory', '0'))
                    cpu_limit = parse_cpu(limits.get('cpu', '0'))
                    memory_limit = parse_memory(limits.get('memory', '0'))

                    all_deployments[full_name]['cpu'] += cpu_request
                    all_deployments[full_name]['memory'] += memory_request
                    all_deployments[full_name]['cpu_limit'] += cpu_limit
                    all_deployments[full_name]['memory_limit'] += memory_limit

                    if cpu_request != cpu_limit or memory_request != memory_limit:
                        cluster_name = cluster['config'].split('--name')[-1].strip()
                        full_name_with_cluster = f"{cluster_name}/{namespace_name}/{deployment_name}"
                        services_with_different_limits_and_requests.append({
                            "name": full_name_with_cluster,
                            "cpu_request": cpu_request,
                            "memory_request": memory_request,
                            "cpu_limit": cpu_limit,
                            "memory_limit": memory_limit,
                        })

        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")

        table = PrettyTable()
        table.field_names = ["Namespace/Service", "PodCount", "CPURequests (cores)", "MemoryRequests (Mi)", "CPULimits (cores)", "MemoryLimits (Mi)"]
        for deployment, info in all_deployments.items():
            table.add_row([deployment, info['count'], f"{info['cpu']:.2f}", f"{info['memory']:.2f}", f"{info['cpu_limit']:.2f}", f"{info['memory_limit']:.2f}"])

        print(table)

    print("\n\nServices with different request limits:")
    for service in services_with_different_limits_and_requests:
        print(f"{service['name']} - CPURequest: {service['cpu_request']:.2f}, MemoryRequest: {service['memory_request']:.2f}, CPULimit: {service['cpu_limit']:.2f}, MemoryLimit: {service['memory_limit']:.2f}")


if __name__ == "__main__":
    get_pod_count_and_resources_per_deployment_for_all_clusters()
