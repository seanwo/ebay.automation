import sys
import requests
import base64
from urllib.parse import unquote, urlencode
from ebay_config import ENV, APP_ID, CERT_ID, RUNAME

SCOPES = [
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.account",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
]

def generate_url():
    base = "https://auth.sandbox.ebay.com/oauth2/authorize" if ENV == "sandbox" else "https://auth.ebay.com/oauth2/authorize"
    query = {
        "client_id": APP_ID,
        "redirect_uri": RUNAME,
        "response_type": "code",
        "scope": " ".join(SCOPES)
    }
    print("\n🔗 Paste this URL into a browser to get the authorization code:\n")
    print(f"{base}?{urlencode(query)}")

def process_code(auth_code):
    decoded_code = unquote(auth_code)
    url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if ENV == "sandbox" else "https://api.ebay.com/identity/v1/oauth2/token"

    credentials = f"{APP_ID}:{CERT_ID}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }

    data = {
        "grant_type": "authorization_code",
        "code": decoded_code,
        "redirect_uri": RUNAME
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        token_data = response.json()
        print("\n✅ Token Received:")
        print(f"Access Token:  {token_data['access_token']}")
        print(f"Refresh Token: {token_data.get('refresh_token', 'N/A')}")
        print(f"Expires In:    {token_data['expires_in']} seconds")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"generate", "process"}:
        print(f"Usage: python {sys.argv[0]} generate | process <authorization_code>")
        sys.exit(1)

    if sys.argv[1] == "generate":
        generate_url()
    elif sys.argv[1] == "process":
        if len(sys.argv) != 3:
            print(f"Usage: python {sys.argv[0]} process <authorization_code>")
            sys.exit(1)
        process_code(sys.argv[2])

if __name__ == "__main__":
    main()