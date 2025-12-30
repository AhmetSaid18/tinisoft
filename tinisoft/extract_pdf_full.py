"""Extract full text from Aras Kargo PDF and search for relevant sections."""
import pdfplumber
import re

pdf = pdfplumber.open('Aras Kargo-Müşteri Bilgi Sorgulama Servisleri.pdf')
print(f'Total pages: {len(pdf.pages)}\n')

# Keywords to search for
keywords = [
    'gönderi', 'shipment', 'create', 'oluştur', 'takip', 'track', 'query',
    'etiket', 'label', 'iptal', 'cancel', 'soap', 'xml', 'endpoint', 'url',
    'QueryType', 'method', 'servis', 'service'
]

all_text = ""
for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text:
        all_text += f"\n=== PAGE {i+1} ===\n{text}\n"

# Search for relevant sections
print("=== SEARCHING FOR RELEVANT SECTIONS ===\n")
for keyword in keywords:
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches = pattern.findall(all_text)
    if matches:
        print(f"Found '{keyword}': {len(matches)} times")

# Extract sections with QueryType
print("\n=== QUERYTYPE SECTIONS ===\n")
querytype_pattern = re.compile(r'QueryType\s*=\s*(\d+)', re.IGNORECASE)
for match in querytype_pattern.finditer(all_text):
    start = max(0, match.start() - 200)
    end = min(len(all_text), match.end() + 1000)
    print(f"\n--- {match.group(0)} ---")
    print(all_text[start:end][:500])
    print("...")

# Save full text to file
with open('aras_kargo_full_text.txt', 'w', encoding='utf-8') as f:
    f.write(all_text)

print(f"\n\nFull text saved to aras_kargo_full_text.txt")
pdf.close()

