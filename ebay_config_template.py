# Change to 'production' when ready
ENV = 'sandbox'
#ENV = 'production'

CONFIG = {
    'sandbox': {
        'DEV_ID': 'YOUR_DEV_ID',
        'APP_ID': 'YOUR_APP_ID',
        'CERT_ID': 'YOUR__CERT_ID',
        'USER_TOKEN': 'YOUR_USER_TOKEN',
        'EBAY_API_DOMAIN': 'api.sandbox.ebay.com',
    },
    'production': {
        'DEV_ID': 'YOUR_DEV_ID',
        'APP_ID': 'YOUR_APP_ID',
        'CERT_ID': 'YOUR__CERT_ID',
        'USER_TOKEN': 'YOUR_USER_TOKEN',
        'EBAY_API_DOMAIN': 'api.ebay.com',
    }
}

EBAY_SITE_ID = '0'

# Export selected config
DEV_ID = CONFIG[ENV]['DEV_ID']
APP_ID = CONFIG[ENV]['APP_ID']
CERT_ID = CONFIG[ENV]['CERT_ID']
USER_TOKEN = CONFIG[ENV]['USER_TOKEN']
EBAY_API_DOMAIN = CONFIG[ENV]['EBAY_API_DOMAIN']