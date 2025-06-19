import sys
import os
import requests
from ebay_config import ENV, get_oauth_token_from_refresh_token

OAUTH_TOKEN = get_oauth_token_from_refresh_token(['https://api.ebay.com/oauth/api_scope/sell.account'])

BASE_URL = "https://api.sandbox.ebay.com" if ENV == "sandbox" else "https://api.ebay.com"
HEADERS = {
    "Authorization": f"Bearer {OAUTH_TOKEN}",
    "Content-Type": "application/json"
}

def enable_business_policies():
    payload = {
        "programType": "SELLING_POLICY_MANAGEMENT"
    }
    r = requests.post(f"{BASE_URL}/sell/account/v1/program/opt_in", headers=HEADERS, json=payload)
    print("Enable Business Policies:", r.status_code)

    if r.status_code == 204:
        print("Successfully opted in.")
        check_opted_in_programs()
    elif r.status_code == 409:
        print("Already opted into SELLING_POLICY_MANAGEMENT.")
        check_opted_in_programs()
    else:
        try:
            print(r.json())
        except ValueError:
            print("No JSON response body.")

def check_opted_in_programs():
    status_resp = requests.get(f"{BASE_URL}/sell/account/v1/program/get_opted_in_programs", headers=HEADERS)
    print("Opted-In Programs:", status_resp.status_code)
    try:
        print(status_resp.json())
    except ValueError:
        print("No JSON response body from status check.")

def delete_existing_policies():
    id_field_map = {
        "fulfillment_policy": "fulfillmentPolicyId",
        "payment_policy": "paymentPolicyId",
        "return_policy": "returnPolicyId"
    }

    response_key_map = {
        "fulfillment_policy": "fulfillmentPolicies",
        "payment_policy": "paymentPolicies",
        "return_policy": "returnPolicies"
    }

    for policy_type in id_field_map:
        r = requests.get(f"{BASE_URL}/sell/account/v1/{policy_type}?marketplace_id=EBAY_US", headers=HEADERS)
        response_json = r.json()
        policies = response_json.get(response_key_map[policy_type], [])
        for policy in policies:
            policy_id = policy.get(id_field_map[policy_type])
            if policy_id:
                del_url = f"{BASE_URL}/sell/account/v1/{policy_type}/{policy_id}"
                del_resp = requests.delete(del_url, headers=HEADERS)
                print(f"Deleted {policy_type} {policy_id}: {del_resp.status_code}")

def create_policy(policy_type, payload):
    url = f"{BASE_URL}/sell/account/v1/{policy_type}"
    r = requests.post(url, headers=HEADERS, json=payload)
    try:
        if r.status_code in {200, 201}:
            id_key_map = {
                "fulfillment_policy": "fulfillmentPolicyId",
                "payment_policy": "paymentPolicyId",
                "return_policy": "returnPolicyId"
            }
            policy_id = r.json().get(id_key_map.get(policy_type), "N/A")
            print(f"{policy_type} {policy_id}: {r.status_code}")
        else:
            error = r.json().get("errors", [{}])[0]
            message = error.get("longMessage", error.get("message", "Unknown error"))
            print(f"{policy_type}: {r.status_code} - {message}")
    except ValueError:
        print(f"{policy_type}: {r.status_code} - No JSON response")

def write_policies():
    delete_existing_policies()

    # Fulfillment Policy
    fulfillment_payload = {
        "name": "standard shipping",
        "description": "USPS Ground Advantage, 2-day handling, calculated shipping",
        "marketplaceId": "EBAY_US",
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "handlingTime": {"unit": "DAY", "value": 2},
        "shippingOptions": [{
            "costType": "CALCULATED",
            "optionType": "DOMESTIC",
            "shippingServices": [{
                "shippingCarrierCode": "USPS",
                "shippingServiceCode": "USPSParcel",
                "freeShipping": False
            }]
        }]
    }

    # Payment Policy
    payment_payload = {
        "name": "standard payment",
        "description": "Immediate payment required",
        "marketplaceId": "EBAY_US",
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "immediatePay": True
    }

    # Return Policy
    return_payload = {
        "name": "standard return",
        "description": "14-day return, buyer pays return shipping",
        "marketplaceId": "EBAY_US",
        "refundMethod": "MONEY_BACK",
        "returnsAccepted": True,
        "returnPeriod": {"value": 14, "unit": "DAY"},
        "returnShippingCostPayer": "BUYER",
        "internationalOverride" : { 
            "returnsAccepted" : False
        }
    }

    create_policy("fulfillment_policy", fulfillment_payload)
    create_policy("payment_policy", payment_payload)
    create_policy("return_policy", return_payload)

def read_policies():
    endpoints = [
        "fulfillment_policy",
        "payment_policy",
        "return_policy"
    ]
    for endpoint in endpoints:
        url = f"{BASE_URL}/sell/account/v1/{endpoint}?marketplace_id=EBAY_US"
        r = requests.get(url, headers=HEADERS)
        print(f"Read {endpoint.replace('_', ' ').title()}s:", r.status_code)
        try:
            print(r.json())
        except ValueError:
            print("No JSON response body.")
        print()

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"write", "read", "enable"}:
        script = os.path.basename(__file__)
        print(f"Usage: python {script} <write|read|enable>")
        sys.exit(1)

    action = sys.argv[1]
    if action == "write":
        write_policies()
    elif action == "read":
        read_policies()
    elif action == "enable":
        enable_business_policies()

if __name__ == "__main__":
    main()