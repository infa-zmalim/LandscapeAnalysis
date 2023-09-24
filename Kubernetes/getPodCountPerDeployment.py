import subprocess
import json
import yaml

def parse_cpu(cpu):
    if cpu.endswith('m'):
        return float(cpu.rstrip('m')) / 1000
    return float(cpu)

def parse_memory(memory):
    if memory.endswith('Gi'):
        return float(memory.rstrip('Gi')) * 1024
    elif memory.endswith('Mi'):
        return float(memory.rstrip('Mi'))
    return float(memory)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error and "No resources found" not in error.decode('utf-8'):
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')

def get_pod_count_and_resources_per_deployment_for_all_clusters():
    with open('resources/clusters.yaml', 'r') as file:
        clusters = yaml.safe_load(file)

    for cluster in clusters:
        run_command(cluster["config"])
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        all_deployments = {}
        total_service_resources = {}

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

                # Update the total resources for the service (assuming deployment name is the same as service name)
                service_name = deployment_name
                if service_name not in total_service_resources:
                    total_service_resources[service_name] = {"cpu": 0, "memory": 0}
                total_service_resources[service_name]['cpu'] += all_deployments[deployment_name]['cpu']
                total_service_resources[service_name]['memory'] += all_deployments[deployment_name]['memory']

        sorted_deployments = sorted(all_deployments.items(), key=lambda x: x[1]['count'], reverse=True)
        print(f"\n\nCluster: {cluster['config'].split('--name')[-1].strip()}")
        for deployment, info in sorted_deployments:
            print(f"  DeploymentName: {deployment}, PodCount: {info['count']}, CPURequests: {info['cpu']} cores, MemoryRequests: {info['memory']} Mi")
        print("\nTotal Service Resources:")
        for service, resources in total_service_resources.items():
            print(f"  ServiceName: {service}, TotalCPURequests: {resources['cpu']} cores, TotalMemoryRequests: {resources['memory']} Mi")
        print("\n")

if __name__ == "__main__":
    get_pod_count_and_resources_per_deployment_for_all_clusters()
