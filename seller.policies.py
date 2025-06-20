import sys
import os
import requests
from ebay_config import ENV, get_oauth_token_from_refresh_token

OAUTH_TOKEN = get_oauth_token_from_refresh_token(['https://api.ebay.com/oauth/api_scope/sell.account'])

BASE_URL = 'https://api.sandbox.ebay.com' if ENV == 'sandbox' else 'https://api.ebay.com'
HEADERS = {
    'Authorization': f"Bearer {OAUTH_TOKEN}",
    'Content-Type': 'application/json'
}

POLICY_NAMES = {
    'fulfillment_policy': 'standard shipping',
    'payment_policy': 'standard payment',
    'return_policy': 'standard return'
}

def handle_response(r, success_msg=None, error_prefix=None):
    try:
        data = r.json()
    except ValueError:
        data = {}

    if r.status_code in {200, 201, 204}:
        if success_msg:
            print(f"✅ {success_msg}")
        return data
    else:
        errors = data.get('errors', [])
        error = errors[0] if errors else {}
        message = error.get('longMessage', error.get('message', 'Unknown error'))
        print(f"❌ {error_prefix or 'Request'} ({r.status_code}): {message}")
        return None

def enable_business_policies():
    payload = {'programType': 'SELLING_POLICY_MANAGEMENT'}
    r = requests.post(f"{BASE_URL}/sell/account/v1/program/opt_in", headers=HEADERS, json=payload)
    if r.status_code == 200:
        print('✅ Successfully opted in.')
    elif r.status_code == 409:
        print('⚠️  Already opted into SELLING_POLICY_MANAGEMENT.')
        check_opted_in_programs()
    else:
        handle_response(r, error_prefix='Enable Business Policies')

def disable_business_policies():
    payload = {'programType': 'SELLING_POLICY_MANAGEMENT'}
    r = requests.post(f"{BASE_URL}/sell/account/v1/program/opt_out", headers=HEADERS, json=payload)
    if r.status_code == 200:
        print('✅ Successfully opted out.')
    else:
        handle_response(r, error_prefix='Disable Business Policies')

def check_opted_in_programs():
    r = requests.get(f"{BASE_URL}/sell/account/v1/program/get_opted_in_programs", headers=HEADERS)
    data = handle_response(r, success_msg='Opted-In Programs:')
    if data:
        print(data)

def delete_policies():
    id_field_map = {
        'fulfillment_policy': 'fulfillmentPolicyId',
        'payment_policy': 'paymentPolicyId',
        'return_policy': 'returnPolicyId',
    }

    response_key_map = {
        'fulfillment_policy': 'fulfillmentPolicies',
        'payment_policy': 'paymentPolicies',
        'return_policy': 'returnPolicies',
    }

    for policy_type in id_field_map:
        r = requests.get(f"{BASE_URL}/sell/account/v1/{policy_type}?marketplace_id=EBAY_US", headers=HEADERS)
        policies = r.json().get(response_key_map[policy_type], [])
        for policy in policies:
            if policy['name'].lower() != POLICY_NAMES[policy_type].lower(): continue
            policy_id = policy.get(id_field_map[policy_type])
            if policy_id:
                del_url = f"{BASE_URL}/sell/account/v1/{policy_type}/{policy_id}"
                del_resp = requests.delete(del_url, headers=HEADERS)
                handle_response(del_resp, success_msg=f"Deleted {policy_type} {policy_id}", error_prefix=f"Delete {policy_type}")

def create_policy(policy_type, payload):
    url = f"{BASE_URL}/sell/account/v1/{policy_type}"
    r = requests.post(url, headers=HEADERS, json=payload)
    if r.status_code in {200, 201}:
        id_key_map = {
            'fulfillment_policy': 'fulfillmentPolicyId',
            'payment_policy': 'paymentPolicyId',
            'return_policy': 'returnPolicyId'
        }
        policy_id = r.json().get(id_key_map[policy_type], 'N/A')
        print(f"✅ Created {policy_type}: {policy_id}")
    else:
        handle_response(r, error_prefix=f"Create {policy_type}")

def update_policy(policy_type, payload):
    policy_id = get_policy_id_by_name(policy_type, POLICY_NAMES[policy_type])

    url = f"{BASE_URL}/sell/account/v1/{policy_type}/{policy_id}"
    r = requests.put(url, headers=HEADERS, json=payload)
    if r.status_code in {200, 201}:
        print(f"✅ Updated {policy_type}: {policy_id}")
    elif r.status_code == 400:
        print(f"⚠️  Updated {policy_type}: Business Profile information in the request is the same as in the system.")
    else:
        handle_response(r, error_prefix=f"Update {policy_type}")

def write_policies(upsert):
    policies = [
        ('fulfillment_policy', {
            'name': POLICY_NAMES['fulfillment_policy'],
            'description': 'USPS Ground Advantage, 2-day handling, calculated shipping',
            'marketplaceId': 'EBAY_US',
            'categoryTypes': [{'name': 'ALL_EXCLUDING_MOTORS_VEHICLES'}],
            'handlingTime': {'unit': 'DAY', 'value': 2},
            'shippingOptions': [{
                'costType': 'CALCULATED',
                'optionType': 'DOMESTIC',
                'shippingServices': [{
                    'shippingCarrierCode': 'USPS',
                    'shippingServiceCode': 'USPSParcel',
                    'freeShipping': False
                }]
            }]
        }),
        ('payment_policy', {
            'name': POLICY_NAMES['payment_policy'],
            'description': 'Immediate payment required',
            'marketplaceId': 'EBAY_US',
            'categoryTypes': [{'name': 'ALL_EXCLUDING_MOTORS_VEHICLES'}],
            'immediatePay': True
        }),
        ('return_policy', {
            'name': POLICY_NAMES['return_policy'],
            'description': '30-day return, buyer pays return shipping',
            'marketplaceId': 'EBAY_US',
            'refundMethod': 'MONEY_BACK',
            'returnsAccepted': True,
            'returnPeriod': {'value': 30, 'unit': 'DAY'},
            'returnShippingCostPayer': 'BUYER',
            'internationalOverride': {'returnsAccepted': False}
        })
    ]
    for policy_type, payload in policies:
        if (upsert):
            update_policy(policy_type, payload)
        else:
            create_policy(policy_type, payload)

def read_policies():
    for policy_type in ['fulfillment_policy', 'payment_policy', 'return_policy']:
        url = f"{BASE_URL}/sell/account/v1/{policy_type}?marketplace_id=EBAY_US"
        r = requests.get(url, headers=HEADERS)
        print(f"\n📘 {policy_type.replace('_', ' ').title()}(s):")
        data = handle_response(r, error_prefix=f"Read {policy_type}")
        if data:
            print(data)

def get_policy_id_by_name(policy_type, target_name):
    endpoint = f"{BASE_URL}/sell/account/v1/{policy_type}?marketplace_id=EBAY_US"
    r = requests.get(endpoint, headers=HEADERS)
    if r.status_code != 200:
        print(f"Failed to retrieve {policy_type}s: {r.status_code}")
        return None

    try:
        data = r.json()
    except ValueError:
        print('No JSON response body.')
        return None

    key_map = {
        'fulfillment_policy': 'fulfillmentPolicies',
        'payment_policy': 'paymentPolicies',
        'return_policy': 'returnPolicies'
    }

    id_field_map = {
        'fulfillment_policy': 'fulfillmentPolicyId',
        'payment_policy': 'paymentPolicyId',
        'return_policy': 'returnPolicyId'
    }

    policies = data.get(key_map.get(policy_type), [])
    for policy in policies:
        if policy.get('name') == target_name:
            return policy.get(id_field_map.get(policy_type))

    print(f"⚠️  No {policy_type} found with name '{target_name}'")
    return None

def main():
    valid_actions = {'create', 'read', 'delete', 'update', 'enable', 'disable'}
    if len(sys.argv) != 2 or sys.argv[1] not in valid_actions:
        script = os.path.basename(__file__)
        print(f"Usage: python {script} <{'|'.join(sorted(valid_actions))}>")
        sys.exit(1)

    action = sys.argv[1]
    if action == 'create':
        write_policies(False)
    elif action == 'read':
        read_policies()
    elif action == 'update':
        write_policies(True)
    elif action == 'delete':
        delete_policies()
    elif action == 'enable':
        enable_business_policies()
    elif action == 'disable':
        disable_business_policies()

if __name__ == '__main__':
    main()