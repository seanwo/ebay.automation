import sys
import os
import csv
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from ebay_config import ENV, SHIPPING_ADDRESS, get_oauth_token_from_refresh_token

OAUTH_TOKEN = get_oauth_token_from_refresh_token(['https://api.ebay.com/oauth/api_scope/sell.inventory', 'https://api.ebay.com/oauth/api_scope/sell.account'])

BASE_URL = 'https://api.sandbox.ebay.com' if ENV == 'sandbox' else 'https://api.ebay.com'
HEADERS = {
    'Authorization': f"Bearer {OAUTH_TOKEN}",
    'Content-Type': 'application/json',
    'Content-Language': 'en-US' 
}

def read_image_urls(csv_path):
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row['eBay_URL'] for row in reader if row.get('eBay_URL')]

def read_description(html_path):
    with open(html_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        body = soup.body
        return ''.join(str(child) for child in body.children if child.name) if body else ''
    
def read_title_from_html(html_path, max_length=80):
    with open(html_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        title_tag = soup.title
        if title_tag and title_tag.string:
            return title_tag.string.strip()[:max_length]
        return ''
    
def read_product_data(xlsx_path, product_id):
    df = pd.read_excel(xlsx_path, dtype={'id': str})
    row = df[df['id'] == product_id]
    if row.empty:
        raise ValueError(f"No entry for product_id {product_id} in pricing file.")
    record = row.iloc[0]
    return record

def create_inventory_location(location_key):
    payload = {
        'name': 'Warehouse',
        'location': {
            'address': SHIPPING_ADDRESS,
        },
        'merchantLocationStatus': 'ENABLED'
    }

    r = requests.post(f"{BASE_URL}/sell/inventory/v1/location/{location_key}", headers=HEADERS, json=payload)

    try:
        response_json = r.json()
    except ValueError:
        response_json = '(no JSON body)'

    print(f"Inventory location '{location_key}' created/updated successfully.")

def create_inventory_item(sku, title, image_urls, product_info):
    weight = product_info['lbs'] * 16 + product_info['oz']
    payload = {
        'availability': {
            'pickupAtLocationAvailability': [],
            'shipToLocationAvailability': {
                'quantity': 1
            }
        },
        'condition': 'USED_EXCELLENT',
        'conditionDescription': 'In good condition. Displayed only in a glass case in a smoke-free home.',
        'product': {
            'title': title,
            'aspects': {
                k: [str(v)] for k, v in {
                    'Organization': 'NASCAR',
                    'Material': 'Diecast',
                    'Scale': product_info.get('scale'),
                    'Driver': product_info.get('driver'),
                    'Vehicle Model': product_info.get('model'),
                    'Vehicle Year': product_info.get('year'),
                    'Edition': product_info.get('edition'),
                    'Type': product_info.get('type'),
                    'Autographed': 'Yes' if product_info.get('autographed') else 'No'
                }.items() if pd.notna(v)
            },
            'imageUrls': image_urls
        },
        
        'packageWeightAndSize': {
            'dimensions': {
                'length': str(int(product_info['l'])),
                'width': str(int(product_info['w'])),
                'height': str(int(product_info['h'])),
                'unit': 'INCH'
            },
            'weight': {
                'value': str(int(weight)),
                'unit': 'OUNCE'
            }
        }
    }

    r = requests.put(f"{BASE_URL}/sell/inventory/v1/inventory_item/{sku}", headers=HEADERS, json=payload)

    try:
        response_json = r.json()
    except ValueError:
        response_json = '(no JSON body)'

    print('Create Inventory Item:', r.status_code, response_json)

def get_policy_id_by_name(policy_type, name):
    url = f"{BASE_URL}/sell/account/v1/{policy_type}_policy?marketplace_id=EBAY_US"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch {policy_type} policies: {r.status_code} - {r.text}")
    
    policies = r.json().get(f"{policy_type}Policies", [])
    for policy in policies:
        if policy['name'].lower() == name.lower():
            return policy[f"{policy_type}PolicyId"]
    raise ValueError(f"{policy_type.capitalize()} policy named '{name}' not found.")

def create_or_update_offer(sku, description_html, product_info, inventory_location):
    # First, check if an offer exists for this SKU
    get_url = f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}"
    get_resp = requests.get(get_url, headers=HEADERS)

    try:
        get_json = get_resp.json()
    except ValueError:
        get_json = {}

    offers = get_json.get('offers', [])
    offer_exists = len(offers) > 0

    FULFILLMENT_POLICY_ID = get_policy_id_by_name('fulfillment', 'standard shipping')
    PAYMENT_POLICY_ID = get_policy_id_by_name('payment', 'standard payment')
    RETURN_POLICY_ID = get_policy_id_by_name('return', 'standard return')

    payload = {
        'sku': sku,
        'marketplaceId': 'EBAY_US',
        'format': 'FIXED_PRICE',
        'availableQuantity': 1,
        'categoryId': '180272',
        'listingDuration': 'GTC',
        'listingPolicies': {
            'fulfillmentPolicyId': FULFILLMENT_POLICY_ID,
            'paymentPolicyId': PAYMENT_POLICY_ID,
            'returnPolicyId': RETURN_POLICY_ID
        },
        'listingDescription': description_html,
        'pricingSummary': {
            'price': {
                'value': float(product_info['price']),
                'currency': 'USD'
            }
        },
        'merchantLocationKey': inventory_location
    }

    if offer_exists:
        offer_id = offers[0]['offerId']
        update_url = f"{BASE_URL}/sell/inventory/v1/offer/{offer_id}"
        r = requests.put(update_url, headers=HEADERS, json=payload)
        action = 'Update'
    else:
        create_url = f"{BASE_URL}/sell/inventory/v1/offer"
        r = requests.post(create_url, headers=HEADERS, json=payload)
        action = 'Create'

    try:
        response_json = r.json()
    except ValueError:
        response_json = '(no JSON body)'

    print(f"{action} Offer:", r.status_code, response_json)


def main():
    if len(sys.argv) != 5:
        script = os.path.basename(__file__)
        print(f"Usage: python {script} <product.xlsx> <eps.csv> <description.html> <product_id>")
        sys.exit(1)

    xlsx_path = sys.argv[1]
    csv_path = sys.argv[2]
    html_path = sys.argv[3]
    product_id = sys.argv[4]

    sku = f"DIECAST-{product_id}"
    product_info = read_product_data(xlsx_path, product_id)
    description_html = read_description(html_path)
    title = read_title_from_html(html_path)
    image_urls = read_image_urls(csv_path)

    inventory_location = 'WAREHOUSE'

    create_inventory_location(inventory_location)
    create_inventory_item(sku, title, image_urls, product_info)
    create_or_update_offer(sku, description_html, product_info, inventory_location)

if __name__ == '__main__':
    main()