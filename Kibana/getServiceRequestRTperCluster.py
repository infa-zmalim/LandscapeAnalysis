import json
import os
from urllib.parse import urljoin
import pandas as pd
import requests
from Kibana.utils.utils import load_config

def get_response_times():
    configurations = load_config()  # Using the new load_config function

    # Set display options for clearer output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', 50)

    # Load configurations
    url = configurations['url']
    cert_file_path = configurations['cert_file_path']
    key_file_path = configurations['key_file_path']
    start_time = configurations.get('start_time', '')
    end_time = configurations.get('end_time', '')
    api_key = configurations['apikey']
    APMPath = configurations['apmpath']

    # Fetch the JSON payload
    script_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_directory, 'Resources', 'DSLServiceRequestTimesPerCluster.json')
    with open(json_file_path, 'r') as file:
        payload = file.read().replace("{{start_time}}", start_time).replace("{{end_time}}", end_time)
        payload = json.loads(payload)

    request_payload = json.dumps(payload, indent=4)
    # Print the formatted payload
    # print("Formatted Payload:")
    # print(request_payload)
    full_url = urljoin(url, APMPath)

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
        return None

    if kibana_response and kibana_response.status_code == 200:
        response_payload = kibana_response.json()
        # print(json.dumps(response_payload, indent=4))

        # Extract the main product buckets
        buckets = response_payload.get("aggregations", {}).get("0", {}).get("buckets", [])

        # Create a dictionary to hold the results
        result = {}

        for bucket in buckets:
            product_key = bucket.get("key")
            sub_buckets = bucket.get("1", {}).get("buckets", [])

            sub_products = {}
            for sub_bucket in sub_buckets:
                sub_product_key = sub_bucket.get("key")
                value_95 = sub_bucket.get("2", {}).get("values", {}).get("95.0")
                sub_products[sub_product_key] = value_95

            result[product_key] = sub_products

        return result
    else:
        print(f"Failed to fetch data from Kibana. Status Code: {kibana_response.status_code if kibana_response else 'No Response'}")
        return None

if __name__ == "__main__":
    response_data = get_response_times()

    # List to hold all the data
    data = []

    for product, sub_products in response_data.items():
        for sub_product, value in sub_products.items():
            # Check if value is not None, then round it off to two decimal places
            if value is not None:
                value = round(value, 2)
            # Append the data as a dictionary to the list
            data.append({
                "Product": product,
                "Sub-Product": sub_product,
                "95.0 Value": value
            })

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Now you can save this DataFrame to a CSV file or use it further as needed
    print(df)
