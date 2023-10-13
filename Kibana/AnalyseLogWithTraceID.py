import configparser
import json
from urllib.parse import urljoin

import pandas as pd
import requests

from Kibana.utils.utils import load_config


def get_log_details(traceId):
    configurations = load_config()  # Using the new load_config function

    # Set display options for clearer output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)

    # Load configurations
    url = configurations['url']
    cert_file_path = configurations['cert_file_path']
    key_file_path = configurations['key_file_path']
    api_key = configurations['apikey']
    start_time = configurations.get('start_time', '')
    end_time = configurations.get('end_time', '')
    serviceName = configurations.get('servicename', '')
    objectName = configurations.get('objectname', '')
    path = configurations.get('path', '')

    # Read the payload from the JSON file for the second request
    with open('Resources/DSLLogWithTraceID.json', 'r') as file:
        payload = file.read()
        payload = payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time).replace(
            "{{serviceName}}", serviceName).replace("{{traceId}}", traceId)\
            # .replace("{{objectName}}", objectName)
        payload = json.loads(payload)

    request_payload = json.dumps(payload)
    # Join the base URL with the path
    full_url = urljoin(url, path)

    # Headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    # Send the request
    try:
        kibana_response = requests.post(full_url, headers=headers, data=request_payload,
                                        cert=(cert_file_path, key_file_path))
        kibana_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        kibana_response = None

    # Process the Kibana response
    if kibana_response and kibana_response.status_code == 200:
        response_json = kibana_response.json()

        # Extract the hits
        hits = response_json['hits']['hits']

        # Initialize an empty list to hold the extracted data
        extracted_data = []

        for hit in hits:
            # Each record will be a dictionary
            record = {}

            # Extract the datetime from message part
            message_content = json.loads(hit.get('fields', {}).get('message', [None])[0])

            record['datetime'] = message_content.get('datetime')

            # Extract the parsed.message
            fields = hit.get('fields', {})
            record['parsed.message'] = fields.get('parsed.message', [None])[0]

            # Append the record to the extracted_data list
            extracted_data.append(record)

        # Convert the list of dictionaries into a DataFrame for better visualization and further analysis
        df = pd.DataFrame(extracted_data)

        # Convert the datetime column to datetime type
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Calculate the time difference between each datetime
        df['time_difference'] = df['datetime'].diff().dt.total_seconds().fillna(0)

        return df

    else:
        print("No response or response has an error.")


if __name__ == "__main__":
    # Load the configuration file
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    traceId = config.get('QueryParams', 'traceId')
    get_log_details_df = get_log_details(traceId)
    print(get_log_details_df)
