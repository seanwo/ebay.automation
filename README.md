# 🏁 eBay Diecast Automation

This repository automates the end-to-end process of creating eBay listings for diecast collectibles, including:

- Pricing based on rarity and driver relevance
- Generating formatted HTML descriptions from a template
- Uploading and retrieving product images via AWS S3
- Producing EPS-compatible bulk upload files
- Using account-specific configuration for policy management

---

# 🛠️ eBay Listing Automation: How-To Guide

This guide walks through the complete workflow for managing eBay listings using Python scripts and shell tools.

---

## 🔁 Every 18 Months

1. **Generate Authorization URL**
   ```bash
   python3 refresh.token.py generate
   ```
   - Open the printed URL
   - Sign in to eBay
   - Copy the **authorization code**

2. **Exchange the Code for a Refresh Token**
   ```bash
   python3 refresh.token.py process <authorization_code>
   ```
   - The resulting refresh token will be inserted into `ebay_config.py`

---

## 🧾 One-Time Setup

### 1. **Enable Business Policies**
```bash
python3 seller.policies.py enable
```

### 2. **Create Standard Policies**
```bash
python3 seller.policies.py write
```

### 3. **Verify the Created Policies**
```bash
python3 seller.policies.py read
```

---

## 📸 As You Add Products

### 1. **Upload Product Photos to S3**
```bash
s3.upload.sh
```
- Place photos in `./photos/000/` where `000` is the SKU

### 2. **Generate EPS-Compatible S3 URLs**
```bash
s3.get.urls.sh <category> <product_id>
```

### 3. **Generate or Update Pricing File**
```bash
python3 diecast.pricing.py <input.xlsx> <output.xlsx>
```
- Converts your full inventory into a pricing sheet for eBay

---

## 📦 For Each eBay Listing

### 1. **Create Product Description HTML**
```bash
python3 diecast.listings.py <spreadsheet.xlsx> <template.html> <product_id>
```

### 2. **Transfer S3 Product Photos to eBay EPS**
```bash
python3 eps.upload.py <s3-urls-file.txt> <category> <product_id>
```

### 3. **Create Inventory Item and Offer (Unpublished)**
```bash
python3 sell.py <product.xlsx> <eps.csv> <description.html> <product_id>
```

### 4. **Publish the Offer**
```bash
# You’ll need to call the publish function manually or from within the script
```

---

## 🧹 Maintenance Commands

### End a Listing
```bash
# Use the offerId to end it via API or dashboard
```

### Delete Offer and Inventory Item
```bash
# Use DELETE endpoints in the Inventory API or add script support
```
