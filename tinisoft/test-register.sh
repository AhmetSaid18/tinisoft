#!/bin/bash
# Register test script

curl -X POST https://api.tinisoft.com.tr/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmetsaidates18@gmail.com",
    "password": "Asamsa2003",
    "first_name": "said",
    "last_name": "ateş",
    "phone": "+905335183770",
    "store_name": "Ates",
    "store_slug": "ates",
    "custom_domain": "influencermarket.com.tr",
    "template": "default"
}' | jq .

