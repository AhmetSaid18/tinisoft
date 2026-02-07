
import base64
import hashlib
import hmac

# Logdan alınan değerler
merchant_id = '662616'
merchant_key = b'QxsoDMk8j1hnrngJ'  # Bytes literal
merchant_salt = b'Xf2aWdsrwrPS9Emz' # Bytes literal

user_ip = '85.105.100.100'
merchant_oid = 'ORD-CE-EE-MAGAZASI-1770469350-6AA19040'
email = 'ahmetsaidates18@gmail.com'
payment_amount = '1490.00'
payment_type = 'card'
installment_count = '0'
currency = 'TL'
test_mode = '1'
non_3d = '0'

# Hash String
hash_str = (
    f"{merchant_id}"
    f"{user_ip}"
    f"{merchant_oid}"
    f"{email}"
    f"{payment_amount}"
    f"{payment_type}"
    f"{installment_count}"
    f"{currency}"
    f"{test_mode}"
    f"{non_3d}"
)

print(f"Hash String: {hash_str}")

# Hash Calculation
message_bytes = hash_str.encode() + merchant_salt
print(f"Message Bytes (first 50): {message_bytes[:50]}")

paytr_token = base64.b64encode(
    hmac.new(
        merchant_key,
        message_bytes,
        hashlib.sha256
    ).digest()
).decode()

print(f"Calculated Token: {paytr_token}")

# Logdaki token ile karşılaştırma
log_token = "5jwt9ld2hfWhywN42ZvBJxhVLz4n3ZCsdBeQSf3ykPw="
if paytr_token == log_token:
    print("SUCCESS: Tokens MATCH!")
else:
    print(f"FAILURE: Tokens do NOT match! Log: {log_token}, Calculated: {paytr_token}")
