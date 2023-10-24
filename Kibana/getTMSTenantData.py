import configparser
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

def get_TMS_Tenant_data(tenant_api_base_url):
    TMS_response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})
    if TMS_response.status_code != 200:
        print(f"Error fetching tenants from {tenant_api_base_url}:", TMS_response.status_code)
        print(TMS_response.text)
        return pd.DataFrame()

    all_tenants_data_TMS = TMS_response.json().get('value', [])
    all_tenants_TMS_df = pd.DataFrame(all_tenants_data_TMS)
    all_tenants_TMS_df['tenantId'] = all_tenants_TMS_df['tenantId'].str.lower()
    return all_tenants_TMS_df

def worker(base_url):
    tenant_api_base_url = f"{base_url}/ccgf-tms/odata/v1/Tenants"
    return get_TMS_Tenant_data(tenant_api_base_url)

def get_all_tenants_data(config_path, sections):
    config = configparser.ConfigParser()
    config.read(config_path)

    urls_to_fetch = []
    for section in sections:
        if section in config:
            for key, base_url in config[section].items():
                urls_to_fetch.append(base_url)

    all_data = pd.DataFrame()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(worker, urls_to_fetch))

    for df in results:
        all_data = all_data._append(df, ignore_index=True)

    return all_data

def main():
    desired_sections = ['AWS-PROD', 'Azure-PROD']
    data = get_all_tenants_data('../ElasticCluster/config/config.ini', desired_sections)
    print(data)

if __name__ == "__main__":
    main()
