import configparser
import json
from urllib.parse import urljoin
import pandas as pd
import requests

from Kibana.AnalyseLogWithTraceID import get_log_details


def get_all_trace_ids(config):
    url = config.get('QA', 'url')
    cert_file_path = config.get('QA', 'cert_file_path')
    key_file_path = config.get('QA', 'key_file_path')
    api_key = config.get('QA', 'apikey')
    start_time = config.get('TimeRange', 'start_time')
    end_time = config.get('TimeRange', 'end_time')
    serviceName = config.get('QueryParams', 'serviceName')

    with open('QA/Resources/DSLLogAllTraceIds.json', 'r') as file:
        payload = file.read()
        payload = payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time).replace("{{serviceName}}", serviceName)
        payload = json.loads(payload)

    request_payload = json.dumps(payload)
    path = "fluentbit-*-ccgf-*/_search"
    full_url = urljoin(url, path)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    try:
        kibana_response = requests.post(full_url, headers=headers, data=request_payload, cert=(cert_file_path, key_file_path))
        kibana_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        return []

    response_json = kibana_response.json()
    # print(json.dumps(response_json, indent=4))
    trace_ids = [bucket['key'] for bucket in response_json['aggregations']['traceId_agg']['buckets']]
    print(f"Trace id count : {len(trace_ids)}")
    return trace_ids

def get_All_log_details():
    config = configparser.ConfigParser()
    config.read('config/config.ini')

    trace_ids = get_all_trace_ids(config)

    main_df = pd.DataFrame()

    for trace_id in trace_ids:
        trace_df = get_log_details(trace_id)
        main_df = pd.concat([main_df, trace_df], ignore_index=True)
    return(main_df)

if __name__ == "__main__":
    get_All_log_details_df = get_All_log_details()
    filtered_df = get_All_log_details_df[get_All_log_details_df['time_difference'] < -2]
    print(filtered_df)
