"""Extract tracking web page PDF"""
import pdfplumber
import os

pdf_path = 'kargotakipwebsayfasıuyeligihakkinda.pdf'

if not os.path.exists(pdf_path):
    pdf_path = os.path.join('tinisoft', pdf_path)

pdf = pdfplumber.open(pdf_path)
print(f'Total pages: {len(pdf.pages)}\n')

all_text = ""
for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text:
        all_text += f"\n=== PAGE {i+1} ===\n{text}\n"

# Save to file
with open('tracking_web_extracted.txt', 'w', encoding='utf-8') as f:
    f.write(all_text)

print(f"Saved {len(all_text)} characters to tracking_web_extracted.txt")

# Search for key terms
keywords = ['accountid', 'alici_kod', 'mainpage', 'iframe', 'link', 'url', 'kod', 'şifre', 'password', 'kargotakip']
print("\n=== KEY TERMS ===")
for keyword in keywords:
    count = all_text.lower().count(keyword.lower())
    if count > 0:
        print(f"{keyword}: {count} times")

pdf.close()

