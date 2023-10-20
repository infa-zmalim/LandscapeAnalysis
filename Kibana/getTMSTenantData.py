import pandas as pd
import requests

from ElasticCluster.config import tenant_api_base_url


def get_TMS_Tenant_data():
    # Fetch all tenants
    TMS_response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})
    if TMS_response.status_code != 200:
        print("Error fetching tenants:", TMS_response.status_code)
        print(TMS_response.text)

    all_tenants_data_TMS = TMS_response.json().get('value', [])
    all_tenants_TMS_df = pd.DataFrame(all_tenants_data_TMS)
    all_tenants_TMS_df['tenantId'] = all_tenants_TMS_df['tenantId'].str.lower()
    return all_tenants_TMS_df

if __name__ == "__main__":
    df = get_TMS_Tenant_data()
    print(df)
