import configparser
import os
import pandas as pd
import requests

def get_TMS_Tenant_data(tenant_api_base_url):
    # Fetch all tenants
    TMS_response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})

    if TMS_response.status_code != 200:
        print(f"Error fetching tenants from {tenant_api_base_url}:", TMS_response.status_code)
        print(TMS_response.text)
        return pd.DataFrame()

    all_tenants_data_TMS = TMS_response.json().get('value', [])
    all_tenants_TMS_df = pd.DataFrame(all_tenants_data_TMS)
    all_tenants_TMS_df['tenantId'] = all_tenants_TMS_df['tenantId'].str.lower()
    return all_tenants_TMS_df

if __name__ == "__main__":
    # Read configuration
    config = configparser.ConfigParser()
    config.read('../ElasticCluster/config/config.ini')

    # Choose the sections you want to iterate over. You can modify this list.
    desired_sections = ['AWS-PROD', 'Azure-PROD']

    # DataFrame to hold data from all URLs
    all_data = pd.DataFrame()

    for section in desired_sections:
        if section in config:
            for key, base_url in config[section].items():
                tenant_api_base_url = f"{base_url}/ccgf-tms/odata/v1/Tenants"
                df = get_TMS_Tenant_data(tenant_api_base_url)

                # Append the data to the combined DataFrame
                all_data = all_data._append(df, ignore_index=True)

    # Print combined data
    print(all_data)
