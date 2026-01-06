"""Extract text from Aras Kargo PDF."""
try:
    import pdfplumber
    pdf = pdfplumber.open('Aras Kargo-Müşteri Bilgi Sorgulama Servisleri.pdf')
    print(f'Total pages: {len(pdf.pages)}')
    print('\n=== PAGE 1 ===')
    print(pdf.pages[0].extract_text()[:3000])
    print('\n=== PAGE 2 ===')
    if len(pdf.pages) > 1:
        print(pdf.pages[1].extract_text()[:3000])
    pdf.close()
except ImportError:
    print("pdfplumber not installed. Trying alternative...")
    try:
        import PyPDF2
        with open('Aras Kargo-Müşteri Bilgi Sorgulama Servisleri.pdf', 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f'Total pages: {len(reader.pages)}')
            print('\n=== PAGE 1 ===')
            print(reader.pages[0].extract_text()[:3000])
            if len(reader.pages) > 1:
                print('\n=== PAGE 2 ===')
                print(reader.pages[1].extract_text()[:3000])
    except ImportError:
        print("PyPDF2 not installed either. Please install: pip install pdfplumber or pip install PyPDF2")
    except Exception as e:
        print(f'Error with PyPDF2: {e}')
except Exception as e:
    print(f'Error: {e}')













