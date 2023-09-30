import json

import requests
from datetime import datetime, timedelta


with open('config/config.json', 'r') as f:
    config = json.load(f)

# Extract the API URL from the config
prometheus_api_url = config['prometheus_api_url']

# Define the time range (last hour)
end = datetime.now()
start = end - timedelta(hours=1)

# Construct the parameters for the request
params = {
    'start': start.timestamp(),
    'end': end.timestamp(),
}

# Make the HTTP GET request to Prometheus API
response = requests.get(prometheus_api_url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Extract and print the series
    series = data['data']
    for s in series:
        print(s)
else:
    # Print an error message if the request was unsuccessful
    print(f"Failed to query Prometheus: {response.status_code} - {response.text}")
