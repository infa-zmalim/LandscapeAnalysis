import configparser
import json
from urllib.parse import urljoin
import pandas as pd
import requests

def get_log_details(traceId):
    # Set display options for clearer output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)

    # Load the configuration file
    config = configparser.ConfigParser()
    config.read('config/config.ini')

    # Read the configuration parameters
    url = config.get('QA', 'url')
    cert_file_path = config.get('QA', 'cert_file_path')
    key_file_path = config.get('QA', 'key_file_path')
    api_key = config.get('QA', 'apikey')
    start_time = config.get('TimeRange', 'start_time')
    end_time = config.get('TimeRange', 'end_time')
    serviceName = config.get('QueryParams', 'serviceName')
    # traceId = config.get('QueryParams', 'traceId')

    # Read the payload from the JSON file for the second request
    with open('QA/Resources/DSLLogWithTraceID.json', 'r') as file:
        payload = file.read()
        payload = payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time).replace("{{serviceName}}", serviceName).replace("{{traceId}}", traceId)
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

            # Extract the timestamp
            record['@timestamp'] = hit.get('fields', {}).get('@timestamp', [None])[0]


            # Extract the parsed.message
            fields = hit.get('fields', {})
            record['parsed.message'] = fields.get('parsed.message', [None])[0]


            # Append the record to the extracted_data list
            extracted_data.append(record)

        # Convert the list of dictionaries into a DataFrame for better visualization and further analysis
        df = pd.DataFrame(extracted_data)

        # Convert the @timestamp column to datetime type
        df['@timestamp'] = pd.to_datetime(df['@timestamp'])

        # Calculate the time difference between each timestamp
        df['time_difference'] = df['@timestamp'].diff().dt.total_seconds().fillna(0)

        return (df)

    else:
        print("No response or response has an error.")

if __name__ == "__main__":
    get_log_details_df = get_log_details()
    print(get_log_details_df)