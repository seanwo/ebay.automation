#!/bin/bash

# Set your S3 bucket name and region here
REGION="us-east-1"
BUCKET_NAME="ebay.photos"

# Check if both category and product ID are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <category> <product_id>"
  exit 1
fi

CATEGORY="$1"
PRODUCT_ID="$2"
OUTPUT_FILE="s3.${CATEGORY}.${PRODUCT_ID}.urls.txt"

aws s3 ls "s3://${BUCKET_NAME}/${CATEGORY}/${PRODUCT_ID}/" --recursive | awk '{print $4}' | while read key; do
  echo "https://s3.${REGION}.amazonaws.com/${BUCKET_NAME}/${key}"
done > "$OUTPUT_FILE"