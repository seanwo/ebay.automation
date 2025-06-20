# 🏁 eBay Diecast Automation

Automates the end-to-end process of creating and managing eBay listings for diecast collectibles:

- Dynamic pricing based on inventory attributes
- EPS photo URL generation and HTML description templating
- Inventory creation, offer publishing, and listing management via eBay APIs
- Uses refresh tokens and configurable business policies

---

## 🔁 Every 18 Months

1. **Generate Authorization URL**
   ```bash
   python3 refresh.token.py generate
   ```

2. **Exchange Authorization Code for Refresh Token**
   ```bash
   python3 refresh.token.py process <authorization_code>
   ```
   - Insert result into `ebay_config.py`

---

## 🧾 One-Time Setup

### Enable and Create Business Policies
```bash
python3 seller.policies.py enable
python3 seller.policies.py create
```

### Read/Verify Existing Policies
```bash
python3 seller.policies.py read
```

---

## 📸 When Adding Products

### 1. Upload Photos to S3
```bash
./s3.upload.sh
```

### 2. Generate S3 URLs (EPS-Compatible)
```bash
./s3.get.urls.sh <category> <product_id>
```

### 3. Generate Pricing File
```bash
python3 diecast.pricing.py <input.xlsx> <output.xlsx>
```

---

## 🧱 Creating a New Listing

### 1. Generate Description HTML
```bash
python3 diecast.listings.py <spreadsheet.xlsx> <template.html> <product_id>
```

### 2. Transfer Images to eBay EPS
```bash
python3 eps.upload.py <s3-urls-file.txt> <category> <product_id>
```

### 3. Create Inventory and Offer (Unpublished)
```bash
python3 stock.py <product.xlsx> <eps.csv> <description.html> <product_id>
```

### 4. Publish Offer
```bash
python3 manage.py publish <product_id>
```

---

## 🧹 Listing Maintenance

### End an Active Listing
```bash
python3 manage.py end <product_id>
```

### Delete Offer and Inventory Item (Only if Not Active)
```bash
python3 manage.py delete <product_id>
```

### Check Listing Status
```bash
python3 manage.py status <product_id>
```

---

## 🔧 Notes

- All `sku` values are prefixed as `DIECAST-<product_id>`
- Listings ended via Trading API will retain their listing ID but show as `status: UNPUBLISHED` in the Sell API
- Deletion is blocked if the listing is still active; always end it first
- All commands support both sandbox and production environments via `ebay_config.py`
