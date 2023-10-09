from Kubernetes.utils.utils import clusters, run_command, get_deployments, get_hpas


def getDeploymentsWithNoHpa(NameSpace):
    # Get all deployments in the namespace
    deployments = get_deployments(NameSpace)

    # Get all HPAs in the namespace
    hpas = get_hpas(NameSpace)
    hpa_names = {hpa["metadata"]["name"] for hpa in hpas["items"]}

    print(f"\nDeployments with no HPA in namespace {NameSpace}:\n")
    for deployment in deployments["items"]:
        deploymentName = deployment["metadata"]["name"]
        if NameSpace not in deploymentName and f"{deploymentName}-hpa" not in hpa_names:
            print(deploymentName)

if __name__ == "__main__":
    for cluster in clusters:
        # Set kubeconfig for the cluster
        run_command(cluster["config"])
        print(f"\n\nDetails for cluster {cluster['name']}:\n")  # Assuming cluster has a 'name' key

        # Loop through each namespace in the cluster
        for NameSpace in cluster["namespaces"]:
            # Print deployments with no HPA for the current namespace in the cluster
            getDeploymentsWithNoHpa(NameSpace)
