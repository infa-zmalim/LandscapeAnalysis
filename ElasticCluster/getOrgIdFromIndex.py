import pandas as pd
import requests
from utility_functions import convert_size_to_mb, modify_volume, extract_tenant_id, extract_org_id
import os

from config import BASE_URL

# Set display options for a clearer output

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows',None)

# Fetching data from the API for deleted docs stats
indices_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/indices/?format=json&v&s=store.size:desc').json())

# Apply the function to extract TenantId
extracted_df = indices_df['index'].apply(extract_org_id)
print(extracted_df)