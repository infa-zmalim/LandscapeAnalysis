import json
from collections import defaultdict
from prettytable import PrettyTable  # Import PrettyTable
from Kubernetes.utils import parse_memory, parse_cpu, run_command


def get_pods_per_node():
    pods_output = run_command("kubectl get pods --all-namespaces -o json")
    pods_json = json.loads(pods_output)

    pods_per_node = defaultdict(list)

    for pod in pods_json['items']:
        node_name = pod['spec'].get('nodeName')
        pod_name = pod['metadata']['name']
        namespace = pod['metadata']['namespace']

        if node_name:
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

    for node, pods in pods_per_node.items():
        table = PrettyTable()
        table.field_names = ["Node", "Namespace", "Pod", "CPURequests (cores)", "MemoryRequests (Mi)"]
        table.align = "l"

        # Add a row for each pod in the node
        for pod in pods:
            row = [
                node if pod is pods[0] else '',  # Only display node name in the first row
                pod['namespace'],
                pod['pod_name'],
                f"{pod['cpu_requests']:.2f}",
                f"{int(pod['memory_requests'])}"  # Changed to display without decimal values
            ]
            table.add_row(row)

        # Add an additional row for the totals
        total_cpu = sum(pod['cpu_requests'] for pod in pods)
        total_memory = sum(pod['memory_requests'] for pod in pods)
        table.add_row(["", "Total", len(pods), f"{total_cpu:.2f}", f"{int(total_memory)}"])

        print(table)
        print()


if __name__ == "__main__":
    get_pods_per_node()
