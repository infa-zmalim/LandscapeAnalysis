from prettytable import PrettyTable
from Kubernetes.utils.utils import run_command, clusters, get_service_names


def main():
    for cluster in clusters:
        run_command(cluster["config"])
        for namespace in cluster["namespaces"]:
            results = get_service_names(namespace)

            # print(f"\n\nResults for Cluster: {cluster['config'].split('--name')[-1].strip()}:")

            table = PrettyTable()
            table.field_names = ["Cluster","Namespace", "Service", "Count"]

            for service, count in results:
                table.add_row([cluster['config'].split('--name')[-1].strip(),namespace, service, count])

            print(table)

if __name__ == "__main__":
    main()
