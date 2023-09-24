import subprocess
import json
import yaml

from Kubernetes.utils import parse_cpu, parse_memory


def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error and "No resources found" not in error.decode('utf-8'):
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')


def get_pod_count_and_resources_per_deployment_for_all_clusters():
    # Assuming you have a YAML file containing your clusters' information
    with open('resources/clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

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
                desired_replicas = deployment['spec'].get('replicas', 0)

                if deployment_name not in all_deployments:
                    all_deployments[deployment_name] = {"count": 0, "cpu": 0, "memory": 0}

                all_deployments[deployment_name]['count'] += desired_replicas

                containers = deployment['spec']['template']['spec']['containers']
                for container in containers:
                    resources = container.get('resources', {})
                    requests = resources.get('requests', {})
                    cpu_request = parse_cpu(requests.get('cpu', '0'))
                    memory_request = parse_memory(requests.get('memory', '0'))

                    all_deployments[deployment_name]['cpu'] += cpu_request
                    all_deployments[deployment_name]['memory'] += memory_request

        # Find the longest service name for alignment
        max_length = max(len(deployment) for deployment in all_deployments.keys())

        # Printing the results
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")
        print(f"{'Service':<{max_length}} PodCount, CPURequests (cores), MemoryRequests (Mi)")
        print('-' * (max_length + 50))

        for deployment, info in all_deployments.items():
            print(f"{deployment:<{max_length}} {info['count']}, {info['cpu']:.2f}, {info['memory']:.2f}")


if __name__ == "__main__":
    get_pod_count_and_resources_per_deployment_for_all_clusters()
