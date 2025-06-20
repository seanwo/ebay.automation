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

def safe_json(r):
    try:
        return r.json()
    except ValueError:
        return {}

def publish_offer(sku):
    try:
        url = f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"❌ Failed to fetch offer for SKU {sku}: {r.status_code}")
            return
        data = safe_json(r)
        offers = data.get('offers', [])
        if not offers:
            print(f"⚠️  No offer found for SKU {sku}")
            return
        offer_id = offers[0]['offerId']
        pub_url = f"{BASE_URL}/sell/inventory/v1/offer/{offer_id}/publish"
        r = requests.post(pub_url, headers=HEADERS)
        print(f"✅ Publish Offer [{sku}]:", r.status_code)
        print(safe_json(r) if r.content else "(no JSON body)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while publishing offer: {e}")

def end_listing(sku):
    try:
        r = requests.get(f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}", headers=HEADERS)
        if r.status_code != 200:
            print(f"❌ Failed to fetch offer for SKU {sku}: {r.status_code}")
            return
        data = safe_json(r)
        offers = data.get('offers', [])
        if not offers:
            print(f"⚠️  No offer found to end for SKU {sku}")
            return

        item_id = offers[0].get('listing', {}).get('listingId')
        if not item_id:
            print(f"⚠️  No listingId found in offer for SKU {sku}")
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
            return

        try:
            response = api.execute('EndFixedPriceItem', {'ItemID': item_id, 'EndingReason': 'NotAvailable'})
            print(f"✅ End Listing [{sku}]:", response.dict())
        except ConnectionError as e:
            if 'Code: 1047' in str(e):
                print(f"✅ Listing [{sku}] is already ended.")
            else:
                raise
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while ending listing: {e}")

def check_listing_status(sku):
    try:
        r = requests.get(f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}", headers=HEADERS)
        if r.status_code != 200:
            print(f"❌ Failed to fetch offer for SKU {sku}: {r.status_code}")
            return
        data = safe_json(r)
        offers = data.get('offers', [])
        if not offers:
            print(f"⚠️  No offer found for SKU {sku}")
            return

        listing_id = offers[0].get('listing', {}).get('listingId')
        if not listing_id:
            print(f"⚠️  No listingId found in offer for SKU {sku}")
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
            return

        response = api.execute('GetItem', {'ItemID': listing_id})
        status = response.dict().get('Item', {}).get('SellingStatus', {}).get('ListingStatus', 'UNKNOWN')
        print(f"ℹ️  Listing status for [{sku}] (ItemID {listing_id}): {status}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while checking listing status: {e}")
    except ConnectionError as e:
        print(f"❌ Trading API error while checking listing status: {e}")

def delete_offer_and_inventory(sku):
    try:
        r = requests.get(f"{BASE_URL}/sell/inventory/v1/offer?sku={sku}", headers=HEADERS)
        if r.status_code != 200:
            print(f"❌ Failed to fetch offers for SKU {sku}: {r.status_code}")
            return
        offers = safe_json(r).get('offers', [])
        for offer in offers:
            listing = offer.get('listing', {})
            if listing:
                #listing_id = listing.get('listingId')
                #if listing_id:
                #    print(f"⚠️ Cannot delete SKU {sku} — Active listing exists with ID {listing_id}")
                #    return
                listing_status = listing.get('listingStatus')
                if listing_status:
                    if listing_status.lower()=="active":
                        print(f"⚠️ Cannot delete SKU {sku} — Active listing exists with listing status {listing_status}")
                        return
            status = offer.get('status', {})
            if status:
                if status.lower()=="published":
                    print(f"⚠️ Cannot delete SKU {sku} — Active listing exists with status {status}")
                    return
            offer_id = offer['offerId']
            del_r = requests.delete(f"{BASE_URL}/sell/inventory/v1/offer/{offer_id}", headers=HEADERS)
            print(f"✅ Deleted Offer [{sku}] ID {offer_id}: {del_r.status_code}")

        del_item_r = requests.delete(f"{BASE_URL}/sell/inventory/v1/inventory_item/{sku}", headers=HEADERS)
        print(f"✅ Deleted Inventory Item [{sku}]:", del_item_r.status_code)
        if del_item_r.status_code != 204:
            print(safe_json(del_item_r))
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during deletion: {e}")

def main():
    valid_actions = {'publish', 'end', 'delete', 'status'}
    if len(sys.argv) != 3 or sys.argv[1] not in valid_actions:
        script = os.path.basename(__file__)
        print(f"Usage: python {script} <{'|'.join(sorted(valid_actions))}> <product_id>")
        sys.exit(1)

    action = sys.argv[1]
    product_id = sys.argv[2]
    sku = f"DIECAST-{product_id}"

    if action == 'publish':
        publish_offer(sku)
    elif action == 'end':
        end_listing(sku)
    elif action == 'status':
        check_listing_status(sku)
    elif action == 'delete':
        delete_offer_and_inventory(sku)

if __name__ == '__main__':
    main()