import configparser
import requests
import json
from urllib.parse import urljoin
import matplotlib.pyplot as plt
import numpy as np

# Load the configuration file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Fetch the color palettes and convert them to lists
graph_palette = config.get('ColorPalettes', 'ColourPalette').split(',')


# Read the configuration parameters
url = config.get('QA', 'url')
cert_file_path = config.get('QA', 'cert_file_path')
key_file_path = config.get('QA', 'key_file_path')
api_key = config.get('QA', 'apikey')

# Load the configuration file
config = configparser.ConfigParser()
config.read('config/config.ini')
# Fetch the time range from config.ini
start_time = config.get('TimeRange', 'start_time')
end_time = config.get('TimeRange', 'end_time')

# Read the payload from the JSON file
with open('QA/Resources/DSLClusterCount.json', 'r') as file:
    cluster_payload = file.read()
    # Replace the placeholders with actual values
    cluster_payload = cluster_payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time)
    cluster_payload = json.loads(cluster_payload)

cluster_payload_json = json.dumps(cluster_payload)
print("cluster_payload_jsonc",cluster_payload_json)
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
print("Payload:", cluster_payload_json)

# Initialize response as None
response = None

try:
    response = requests.post(full_url, headers=headers, data=cluster_payload_json, cert=(cert_file_path, key_file_path))
except requests.exceptions.RequestException as e:
    print("Error making the request:", e)

if response is not None and response.status_code == 200:
    print("Success!")
    cluster_payload_json = json.loads(response.text)

    if 'aggregations' not in cluster_payload_json:
        print("No aggregations in the response. Please check the Elasticsearch query and index.")
        print("Response:", json.dumps(cluster_payload_json, indent=4))
    else:
        cluster_buckets = cluster_payload_json["aggregations"]["0"]["buckets"]
        cluster_names = [bucket['key'] for bucket in cluster_buckets]
        cluster_counts = [bucket['doc_count'] for bucket in cluster_buckets]

        # Setting up the figure and subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={'width_ratios': [4, 6]})

        ax1.pie(cluster_counts, labels=cluster_names, startangle=90, colors=graph_palette[:len(cluster_names)])
        ax1.set_title('Distribution of Records for each Cluster')
        ax1.axis('equal')

        unique_object_names = set()
        for bucket in cluster_buckets:
            for obj in bucket["1"]["buckets"]:
                unique_object_names.add(obj["key"])

        color_map = dict(zip(unique_object_names, graph_palette[:len(unique_object_names)]))

        bottoms = np.zeros(len(cluster_names))
        for object_name in unique_object_names:
            counts = []
            for bucket in cluster_buckets:
                count = next((obj['doc_count'] for obj in bucket["1"]["buckets"] if obj['key'] == object_name), 0)
                counts.append(count)
            ax2.bar(cluster_names, counts, bottom=bottoms, label=object_name, color=color_map[object_name])
            bottoms = [i+j for i, j in zip(bottoms, counts)]

        ax2.set_title('Breakdown of Object Names for each Cluster')
        ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax2.set_xticks(range(len(cluster_names)))
        ax2.set_xticklabels(cluster_names, rotation=90)

        plt.tight_layout()
        plt.show()


else:
    print("Failed to retrieve data.")
    if response is not None:
        print("Status Code:", response.status_code)
        print(response.text)
