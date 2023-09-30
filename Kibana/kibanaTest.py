import configparser
import requests
import json
from urllib.parse import urljoin
import matplotlib.pyplot as plt
import numpy as np

# Load the configuration file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Read the configuration parameters
url = config.get('QA', 'url')
cert_file_path = config.get('QA', 'cert_file_path')
key_file_path = config.get('QA', 'key_file_path')
api_key = config.get('QA', 'apikey')

# Read the payload from the JSON file
with open('QA/Resources/DSLClusterCount.json', 'r') as file:
    payload = json.load(file)

data = json.dumps(payload)

# Define the path
path = "fluentbit-*-ccgf-*/_search"

# Join the base URL with the path
full_url = urljoin(url, path)
print("Full URL:", full_url)

# Headers
headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key
}
print("Headers:", headers)
print("Payload:", data)

# Initialize response as None
response = None

try:
    response = requests.post(full_url, headers=headers, data=data, cert=(cert_file_path, key_file_path))
except requests.exceptions.RequestException as e:
    print("Error making the request:", e)

if response is not None and response.status_code == 200:
    print("Success!")
    data = json.loads(response.text)

    if 'aggregations' not in data:
        print("No aggregations in the response. Please check the Elasticsearch query and index.")
        print("Response:", json.dumps(data, indent=4))
    else:
        cluster_buckets = data["aggregations"]["0"]["buckets"]
        cluster_names = [bucket['key'] for bucket in cluster_buckets]
        cluster_counts = [bucket['doc_count'] for bucket in cluster_buckets]

        # Pie Chart (Cluster Distribution) - 60%
        pie_palette = ["#e27c7c", "#a86464", "#6d4b4b", "#503f3f", "#333333", "#3c4e4b", "#466964", "#599e94", "#6cd4c5"]

        # Stacked Bar Chart (Object Names Breakdown by Cluster) - 30%
        bar_palette = ["#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", "#ffee65", "#beb9db", "#fdcce5",
                       "#8bd3c7", "#e27c7c", "#a86464", "#6d4b4b", "#503f3f", "#333333", "#3c4e4b", "#466964",
                       "#599e94", "#6cd4c5"]

        # Setting up the figure and subplots
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 7), gridspec_kw={'width_ratios': [6, 3, 1]})

        ax1.pie(cluster_counts, labels=cluster_names, startangle=90, colors=pie_palette[:len(cluster_names)])
        ax1.set_title('Distribution of Records for each Cluster (Last Hour)')
        ax1.axis('equal')

        unique_object_names = set()
        for bucket in cluster_buckets:
            for obj in bucket["1"]["buckets"]:
                unique_object_names.add(obj["key"])

        color_map = dict(zip(unique_object_names, bar_palette[:len(unique_object_names)]))

        bottoms = np.zeros(len(cluster_names))
        for object_name in unique_object_names:
            counts = []
            for bucket in cluster_buckets:
                count = next((obj['doc_count'] for obj in bucket["1"]["buckets"] if obj['key'] == object_name), 0)
                counts.append(count)
            ax2.bar(cluster_names, counts, bottom=bottoms, label=object_name, color=color_map[object_name])
            bottoms = [i+j for i, j in zip(bottoms, counts)]

        ax2.set_title('Breakdown of Object Names for each Cluster (Last Hour)')
        ax2.legend(loc='upper right')
        ax2.set_xticks(range(len(cluster_names)))
        ax2.set_xticklabels(cluster_names, rotation=90)

        # Accent Space (10%) - Placeholder
        ax3.axis("off")
        ax3.text(0.5, 0.5, 'Accent Space', ha='center', va='center', transform=ax3.transAxes, color='darkred')

        plt.tight_layout()
        plt.show()

else:
    print("Failed to retrieve data.")
    if response is not None:
        print("Status Code:", response.status_code)
        print(response.text)
