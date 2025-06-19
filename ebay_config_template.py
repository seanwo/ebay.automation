# Change to 'production' when ready
ENV = 'sandbox'
#ENV = 'production'

CONFIG = {
    'sandbox': {
        'DEV_ID': 'YOUR_DEV_ID',
        'APP_ID': 'YOUR_APP_ID',
        'CERT_ID': 'YOUR__CERT_ID',
        'EBAY_API_DOMAIN': 'api.sandbox.ebay.com',
        'USER_TOKEN': 'YOUR_USER_TOKEN',
        'REFRESH_TOKEN': 'YOUR_REFRESH_TOKEN',
        'RUNAME': 'YOUR_RUNAME',
    },
    'production': {
        'DEV_ID': 'YOUR_DEV_ID',
        'APP_ID': 'YOUR_APP_ID',
        'CERT_ID': 'YOUR__CERT_ID',
        'EBAY_API_DOMAIN': 'api.ebay.com',
        'USER_TOKEN': 'YOUR_USER_TOKEN',
        'REFRESH_TOKEN': 'YOUR_REFRESH_TOKEN',
        'RUNAME': 'YOUR_RUNAME',
    }
}

CONFIDENTIAL = {
    'address': {
        'addressLine1': '123 Warehouse Road',
        'city': 'Dallas',
        'stateOrProvince': 'TX',
        'postalCode': '75001',
        'country': 'US'
    }
}

EBAY_SITE_ID = '0'

# Export selected config
DEV_ID = CONFIG[ENV]['DEV_ID']
APP_ID = CONFIG[ENV]['APP_ID']
CERT_ID = CONFIG[ENV]['CERT_ID']
USER_TOKEN = CONFIG[ENV]['USER_TOKEN']
EBAY_API_DOMAIN = CONFIG[ENV]['EBAY_API_DOMAIN']
RUNAME = CONFIG[ENV]['RUNAME']

# Export selected confidential
SHIPPING_ADDRESS = CONFIDENTIAL['address']

import requests
import base64

def get_oauth_token_from_refresh_token(scopes):
    url = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token' if ENV == 'sandbox' else 'https://api.ebay.com/identity/v1/oauth2/token'
    
    credentials = f"{APP_ID}:{CERT_ID}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f"Basic {encoded_credentials}"
    }

    scope_string = ' '.join(scopes)

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': CONFIG[ENV]['REFRESH_TOKEN'],
        'scope': scope_string,
    }

    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Token refresh failed: {response.status_code}\n{response.text}")