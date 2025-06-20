import sys
import os
import requests
from ebay_config import ENV, DEV_ID, APP_ID, CERT_ID, USER_TOKEN, EBAY_SITE_ID, EBAY_API_DOMAIN, get_oauth_token_from_refresh_token
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError

# Get access token for REST API
OAUTH_TOKEN = get_oauth_token_from_refresh_token([
    'https://api.ebay.com/oauth/api_scope/sell.inventory'
])
BASE_URL = 'https://api.sandbox.ebay.com' if ENV == 'sandbox' else 'https://api.ebay.com'
HEADERS = {
    'Authorization': f"Bearer {OAUTH_TOKEN}",
    'Content-Type': 'application/json'
}

def publish_offer(sku):
    url = f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    offers = data.get('offers', [])
    if not offers:
        print(f"No offer found for SKU {sku}")
        return
    offer_id = offers[0]['offerId']
    pub_url = f"{BASE_URL}/sell/inventory/v1/offer/{offer_id}/publish"
    r = requests.post(pub_url, headers=HEADERS)
    print(f"Publish Offer [{sku}]:", r.status_code, r.json() if r.content else "(no JSON body)")


def end_listing(sku):
    r = requests.get(f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}", headers=HEADERS)
    data = r.json()
    offers = data.get('offers', [])
    if not offers:
        print(f"No offer found to end for SKU {sku}")
        return

    item_id = offers[0].get('listing', {}).get('listingId')

    if not item_id:
        print(f"No listingId found in offer for SKU {sku}")
        return

    try:
        api = Trading(
            domain=EBAY_API_DOMAIN,
            config_file=None,
            appid=APP_ID,
            certid=CERT_ID,
            devid=DEV_ID,
            token=USER_TOKEN,
            siteid=EBAY_SITE_ID,
            warnings=True
        )
    except Exception as e:
        print(f"❌ Failed to initialize eBay SDK: {str(e)}")
        sys.exit(1)

    try:
        response = api.execute('EndFixedPriceItem', {'ItemID': item_id, 'EndingReason': 'NotAvailable'})
        print(f"End Listing [{sku}]:", response.dict())
    except ConnectionError as e:
        if 'Code: 1047' in str(e):
            print(f"Listing [{sku}] is already ended.")
            return
        else:
            raise

def delete_offer_and_inventory(sku):
    r = requests.get(f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}", headers=HEADERS)
    offers = r.json().get('offers', [])
    for offer in offers:
        offer_id = offer['offerId']
        del_r = requests.delete(f"{BASE_URL}/sell/inventory/v1/offer/{offer_id}", headers=HEADERS)
        print(f"Deleted Offer [{sku}] ID {offer_id}: {del_r.status_code}")
    del_item_r = requests.delete(f"{BASE_URL}/sell/inventory/v1/inventory_item/{sku}", headers=HEADERS)
    print(f"Deleted Inventory Item [{sku}]:", del_item_r.status_code)

def main():
    script = os.path.basename(__file__)
    if len(sys.argv) != 3:
        print(f"Usage: python {script} <publish|end|delete> <product_id>")
        sys.exit(1)

    action = sys.argv[1]
    product_id = sys.argv[2]
    sku = f"DIECAST-{product_id}"

    if action == 'publish':
        publish_offer(sku)
    elif action == 'end':
        end_listing(sku)
    elif action == 'delete':
        delete_offer_and_inventory(sku)
    else:
        print(f"Invalid action. Use: python {script} <publish|end|delete>")
        sys.exit(1)

if __name__ == '__main__':
    main()