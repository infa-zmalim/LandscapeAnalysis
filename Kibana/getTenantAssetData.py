import configparser
import json
import os
from urllib.parse import urljoin
import pandas as pd
import requests
from ElasticCluster.utility_functions import modify_volume


def get_tenant_asset_data():
    # Set display options for clearer output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)
    # Load the configuration file
    config = configparser.ConfigParser()
    # Absolute path to config.ini
    script_directory = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_directory, 'config', 'config.ini')
    config.read(config_path)

    # Read the configuration parameters
    url = config.get('QA', 'url')
    cert_file_path = config.get('QA', 'cert_file_path')
    key_file_path = config.get('QA', 'key_file_path')
    api_key = config.get('QA', 'apikey')
    start_time = config.get('TimeRange', 'start_time')
    end_time = config.get('TimeRange', 'end_time')
    serviceName  = config.get('QueryParams','serviceName')

    cert_file_relative_path = config.get('QA', 'cert_file_path')
    key_file_relative_path = config.get('QA', 'key_file_path')

    # Construct full paths for cert_file_path and key_file_path
    cert_file_path = os.path.join(script_directory, cert_file_relative_path)
    key_file_path = os.path.join(script_directory, key_file_relative_path)

    # Absolute path to DSLTenantAssetVolumeData.json
    json_file_path = os.path.join(script_directory, 'QA', 'Resources', 'DSLTenantAssetVolumeData.json')

    # Read the payload from the JSON file for the second request
    with open(json_file_path, 'r') as file:
        payload = file.read()
        payload = payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time)
        payload = json.loads(payload)

    request_payload = json.dumps(payload)

    # Define the path
    path = "fluentbit-*-ccgf-*/_search"

    # Join the base URL with the path
    full_url = urljoin(url, path)

    # Headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    # Send the request
    try:
        kibana_response = requests.post(full_url, headers=headers, data=request_payload, cert=(cert_file_path, key_file_path))
        kibana_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        kibana_response = None

    df = None
    if kibana_response and kibana_response.status_code == 200:
        request_payload = kibana_response.json()
        bucket_data = request_payload['aggregations']['0']['buckets']
        df_data = []
        for item in bucket_data:
            org = item['key']
            inner_buckets = item['1']['buckets']
            for inner_item in inner_buckets:
                tenant = inner_item['key']
                business_assets_sum = round(inner_item['2-bucket']['2-metric']['top'][0]['metrics']['parsed.key2.key7n'])
                technical_assets_sum = round(inner_item['3-bucket']['3-metric']['top'][0]['metrics']['parsed.key2.key8n'])
                marketplace_sum = round(inner_item['4-bucket']['4-metric']['top'][0]['metrics']['parsed.key2.key9n'])
                total_sum = round(inner_item['5-bucket']['5-metric']['top'][0]['metrics']['parsed.key2.key4n'])
                df_data.append([org, tenant, business_assets_sum, technical_assets_sum, marketplace_sum, total_sum])

        # Convert the list to a dataframe
        df = pd.DataFrame(df_data, columns=['Org', 'Tenant', 'Business Assets', 'Technical Assets', 'Marketplace', 'Total'])
        df = df.sort_values(by='Total', ascending = False)
        df['Org'] = df['Org'].str.lower()
        # Apply the modify_volume function to the specified columns
        cols_to_modify = ['Business Assets', 'Technical Assets', 'Marketplace', 'Total']
        for col in cols_to_modify:
            df[col] = df[col].apply(modify_volume)


    return df

# For debugging purposes
if __name__ == "__main__":
    df = get_tenant_asset_data()
    print(df)
