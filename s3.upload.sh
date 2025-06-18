#!/bin/bash

# Set your S3 bucket name
BUCKET_NAME="ebay.photos"

# Check if category is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <category>"
  exit 1
fi

CATEGORY="$1"

aws s3 sync "./photos/${CATEGORY}" "s3://${BUCKET_NAME}/${CATEGORY}/" \
  --exact-timestamps \
  --exclude ".DS_Store" \
  --exclude "*/.DS_Store" #--dryrun