import re
from collections import Counter
import yaml
from prettytable import PrettyTable  # Importing PrettyTable
from Kubernetes.utils import run_command

with open('resources/AZURE_NON-PROD_clusters.yaml', 'r') as file:
    clusters = yaml.safe_load(file)
    print(clusters)

def get_service_names(namespace):
    cmd_output = run_command(f"kubectl get deployment -n {namespace}")
    lines = cmd_output.split('\n')[1:]
    service_names = [re.split('-\d+', line.split()[0])[0] for line in lines if line]
    counter = Counter(service_names)
    sorted_services = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    return sorted_services

def main():
    for cluster in clusters:
        run_command(cluster["config"])
        for namespace in cluster["namespaces"]:
            results = get_service_names(namespace)

            print(f"\n\nResults for Cluster: {cluster['config'].split('--name')[-1].strip()}:")

            # Creating a PrettyTable object and setting field names
            table = PrettyTable()
            table.field_names = ["Namespace", "Service", "Count"]  # Added Namespace as a field name

            for service, count in results:
                # Adding rows to the PrettyTable object
                table.add_row([namespace, service, count])  # Added namespace as a column value

            # Printing the PrettyTable
            print(table)

if __name__ == "__main__":
    main()
