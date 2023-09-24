import subprocess
import json
from collections import defaultdict

from Kubernetes.utils import parse_memory


def parse_cpu(cpu):
    if cpu.endswith('m'):
        return float(cpu.rstrip('m')) / 1000
    return float(cpu)


def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error and "No resources found" not in error.decode('utf-8'):
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')

def get_pods_per_node():
    # Fetch all pods in all namespaces
    pods_output = run_command("kubectl get pods --all-namespaces -o json")
    pods_json = json.loads(pods_output)

    # Initialize a dictionary to hold the pod information per node
    pods_per_node = defaultdict(list)

    # Iterate over each pod and append it to the corresponding node list
    for pod in pods_json['items']:
        node_name = pod['spec'].get('nodeName')
        pod_name = pod['metadata']['name']
        namespace = pod['metadata']['namespace']

        if node_name:  # Only append pods that are assigned to a node
            cpu_requests = 0
            memory_requests = 0
            containers = pod['spec']['containers']
            for container in containers:
                resources = container.get('resources', {})
                requests = resources.get('requests', {})
                cpu_requests += parse_cpu(requests.get('cpu', '0'))
                memory_requests += parse_memory(requests.get('memory', '0'))

            pods_per_node[node_name].append({
                "pod_name": pod_name,
                "namespace": namespace,
                "cpu_requests": cpu_requests,
                "memory_requests": memory_requests,
            })

    # Print the result
    for node, pods in pods_per_node.items():
        print(f"Node: {node}")
        print(f"Pod Count: {len(pods)}")
        for pod in pods:
            print(f"  Namespace: {pod['namespace']}, PodName: {pod['pod_name']}, CPU Request: {pod['cpu_requests']:.2f} cores, Memory Request: {pod['memory_requests']} Mi")
        print()

if __name__ == "__main__":
    get_pods_per_node()
