import os
import sys
import csv
from urllib.parse import urlparse
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
from ebay_config import ENV, DEV_ID, APP_ID, CERT_ID, USER_TOKEN, EBAY_SITE_ID, EBAY_API_DOMAIN

def upload_image_with_ebaysdk(image_url, api):
    try:
        response = api.execute('UploadSiteHostedPictures', {
            'ExternalPictureURL': image_url,
            'PictureSet': 'Supersize',
            'PhotoDisplay': 'SuperSize'
        })
        if response.reply.Ack == "Success":
            return response.reply.SiteHostedPictureDetails.FullURL, "Success"
        else:
            if hasattr(response.reply, 'Errors'):
                errors = response.reply.Errors
                if not isinstance(errors, list):
                    errors = [errors]
                error_message = "; ".join(
                    [f"{getattr(e, 'ShortMessage', 'NoShortMsg')}: {getattr(e, 'LongMessage', 'NoLongMsg')}" for e in errors]
                )
            else:
                error_message = "Unknown error with no Errors field"
            return None, f"API Error: {error_message}"
    except ConnectionError as e:
        return None, f"Connection error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def main():
    if len(sys.argv) != 4:
        script_name = os.path.basename(__file__)
        print(f"Usage: python {script_name} <s3-urls-file.txt> <category> <product-id>")
        sys.exit(1)

    file_path = sys.argv[1]
    category = sys.argv[2]
    product_id = sys.argv[3]
    output_file = f"eps.{category}.{product_id}{f'.{ENV}' if ENV != 'production' else ''}.urls.csv"

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print(f"❌ No URLs found in input file.")
        sys.exit(0)

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

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["S3_URL", "eBay_URL", "Status"])

        for url in urls:
            ebay_url, status = upload_image_with_ebaysdk(url, api)
            writer.writerow([url, ebay_url if ebay_url else "", status])
            if ebay_url:
                print(f"✅ Uploaded: {url} → {ebay_url}")
            else:
                print(f"❌ Failed: {url} → {status}")

if __name__ == "__main__":
    main()