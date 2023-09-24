# config.py
#DEVPROD
BASE_URL = 'https://vpc-ccgf-qa-devprod-cdgc-v2-es-v4za6cpj3x2r4gtmgtsv2a2o3u.us-west-2.es.amazonaws.com'
# Uncomment the below line if you need the AUDIT cluster
#BASE_URL = 'https://vpc-ccgf-qa-devprod-cdgc-audit-e-5hq67rm25gap6h53bmqnuejkaa.us-west-2.es.amazonaws.com'

NA_API_BASE_URL = "https://cdgc-api.dm-us.informaticacloud.com"
DEVPROD_API_BASE_URL = "https://devprod-api.hawk.mrel.infaqa.com"

# tenant_api_base_url definition moved here
tenant_api_base_url = f"{DEVPROD_API_BASE_URL}/ccgf-tms/odata/v1/Tenants"

