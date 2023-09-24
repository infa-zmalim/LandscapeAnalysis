import json
from collections import defaultdict

from Kubernetes.utils import parse_memory, parse_cpu, run_command


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

    # Calculate the maximum length for proper alignment
    max_length = max(len(pod['namespace'] + ', ' + pod['pod_name']) for node, pods in pods_per_node.items() for pod in pods)

    # Print the result
    header_format = "{:<" + str(max_length) + "} {:<30} {:<20} {:<20}"
    row_format = "  {:<" + str(max_length) + "} {:<30} {:<20.2f} {:<20}"

    print(f"{'Node':<{max_length}} PodCount, CPURequests (cores), MemoryRequests (Mi)")
    print('-' * (max_length + 60))
    for node, pods in pods_per_node.items():
        print(header_format.format(node, len(pods), '', ''))
        for pod in pods:
            print(row_format.format(pod['namespace'] + ', ' + pod['pod_name'], '', pod['cpu_requests'], pod['memory_requests']))
        print()

if __name__ == "__main__":
    get_pods_per_node()
