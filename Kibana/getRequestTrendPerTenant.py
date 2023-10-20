import json
import os
from urllib.parse import urljoin
import pandas as pd
import requests
import matplotlib.pyplot as plt
from ElasticCluster.config import tenant_api_base_url
from Kibana.utils.utils import load_config

def get_timeseries_per_tenant_request_data():
    configurations = load_config()

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)

    url = configurations['url']
    cert_file_path = configurations['cert_file_path']
    key_file_path = configurations['key_file_path']
    api_key = configurations['apikey']
    start_time = configurations.get('start_time', '')
    end_time = configurations.get('end_time', '')
    serviceName = configurations.get('servicename', '')
    objectName = configurations.get('objectname', '')
    path = configurations.get('path', '')

    script_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_directory, 'Resources', 'DSLAllTenantRequestsPerTimePeriod.json')
    with open(json_file_path, 'r') as file:
        payload = file.read()
        payload = payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time).replace("{{serviceName}}", serviceName).replace("{{objectName}}", objectName)
        payload = json.loads(payload)

    request_payload = json.dumps(payload)
    full_url = urljoin(url, path)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    try:
        kibana_response = requests.post(full_url, headers=headers, data=request_payload, cert=(cert_file_path, key_file_path))
        kibana_response.raise_for_status()

        print("Kibana Response Status Code:", kibana_response.status_code)
        # print("Kibana conent:", kibana_response.content)

        if kibana_response.status_code == 200:
            response_payload = kibana_response.json()
            bucket_data = response_payload.get('aggregations', {}).get('0', {}).get('buckets', [])

            data_dict = {}  # Store data by org ID

            # Corrected data extraction from Elasticsearch response
            for item in bucket_data:
                org_id = item.get('key', 'N/A')  # Extract org_id

                for nested_bucket in item.get('1', {}).get('buckets', []):
                    doc_count = nested_bucket.get('doc_count', 0)
                    metric_value = nested_bucket.get('2-bucket', {}).get('2-metric', {}).get('value', 0)

                    # Extract time
                    time = nested_bucket.get('key_as_string', 'N/A')

                    if org_id not in data_dict:
                        data_dict[org_id] = {'time': [], 'doc_count': [], 'metric_value': []}

                    data_dict[org_id]['time'].append(time)
                    data_dict[org_id]['doc_count'].append(doc_count)
                    data_dict[org_id]['metric_value'].append(metric_value)


        # Plot a line graph for each org ID with data
            for org_id, data in data_dict.items():
                if data['time']:
                    plt.plot(data['time'], data['doc_count'], label=f'Org ID {org_id}')

            plt.xlabel('Time')
            plt.ylabel('Requests')
            plt.title('Requests Over Time')
            plt.xticks(rotation=45)
            plt.legend()

            plt.show()
    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        kibana_response = None

if __name__ == "__main__":
    get_timeseries_per_tenant_request_data()
