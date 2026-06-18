#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persian PDF to EPUB - Auto OCR for Scanned Books
Developer: Maryam Mobayen
GitHub: https://github.com/maryam-mobayen/persian-pdf-to-epub
License: MIT

تبدیل PDF فارسی (متن و اسکن) به EPUB برای Kindle
"""

import os, sys, subprocess, zipfile, uuid, re, unicodedata, io
from datetime import datetime

print("📦 Installing...")
for pkg in ['PyMuPDF', 'arabic-reshaper', 'pytesseract', 'Pillow']:
    subprocess.call([sys.executable, '-m', 'pip', 'install', '-q', pkg], timeout=180)

import fitz, arabic_reshaper
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except:
    HAS_OCR = False
    print("⚠️ OCR libraries installed but may need Tesseract")

def check_tesseract():
    try:
        subprocess.run(['which', 'tesseract'], capture_output=True, check=True)
        return True
    except:
        return False

def install_tesseract():
    print("\n❌ Tesseract not found!")
    print("\n📥 Install Tesseract:")
    print("   brew install tesseract")
    print("\n📥 Install Persian language:")
    print("   brew install tesseract-lang")
    print("\nThen run this script again.\n")
    sys.exit(1)

def clean(text):
    if not text: return text
    text = unicodedata.normalize('NFC', text)
    for a, p in [('ك', 'ک'), ('ي', 'ی'), ('ة', 'ه')]:
        text = text.replace(a, p)
    return re.sub(r' +', ' ', text).strip()

def reshape(text):
    try: return arabic_reshaper.reshape(text)
    except: return text

def is_scanned(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text_count = 0
        for page in doc[:min(3, len(doc))]:
            text = page.get_text('text').strip()
            text_count += len(text)
        doc.close()
        return text_count < 100
    except:
        return False

def ocr_page(page, lang='fas'):
    if not HAS_OCR:
        return ""
    try:
        mat = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(mat.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=lang)
        return text
    except:
        return ""

def extract(pdf):
    print(f"📖 Reading {os.path.basename(pdf)}...")
    
    scanned = is_scanned(pdf)
    if scanned:
        print("🔍 Scanned PDF detected - Using OCR")
        if not check_tesseract():
            install_tesseract()
    
    doc = fitz.open(pdf)
    pages = []
    
    for i, page in enumerate(doc):
        text = page.get_text('text').strip()
        
        if not text and scanned:
            print(f"  OCR {i+1}/{len(doc)}...", end='\r')
            sys.stdout.flush()
            text = ocr_page(page)
        
        if text:
            pages.append(clean(text))
    
    doc.close()
    
    if pages:
        print(f"✅ {len(pages)} pages{' (from OCR)' if scanned else ''}")
    return pages

def epub(title, author, pages, out):
    print("⚙️ Building EPUB...")
    bid = str(uuid.uuid4())
    
    chapters = []
    cur, length = [], 0
    for text in pages:
        if length + len(text) > 10000 and cur:
            chapters.append('\n\n'.join(cur))
            cur, length = [], 0
        cur.append(text)
        length += len(text)
    if cur: chapters.append('\n\n'.join(cur))
    
    files, manifest, spine = {}, [], []
    
    for i, content in enumerate(chapters):
        ch_id, fname = f'c{i+1:04d}', f'c{i+1:04d}.html'
        shaped = reshape(content)
        paras = ''.join(f'<p>{p.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</p>' 
                       for p in shaped.split('\n\n') if p.strip())
        
        html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fa" dir="rtl">
<head><meta charset="UTF-8"/><title>Ch {i+1}</title>
<style>body{{direction:rtl;text-align:right;font-family:Georgia,serif;margin:1em;}}
p{{direction:rtl;text-align:right;margin:0.5em 0;}}</style></head>
<body><h2>بخش {i+1}</h2>{paras}</body></html>'''
        
        files[fname] = html
        manifest.append(f'<item id="{ch_id}" href="{fname}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{ch_id}"/>')
    
    nav = f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="fa" dir="rtl">
<head><meta charset="UTF-8"/></head>
<body dir="rtl"><nav epub:type="toc"><ol dir="rtl">
{''.join(f'<li><a href="c{i+1:04d}.html">بخش {i+1}</a></li>' for i in range(len(chapters)))}
</ol></nav></body></html>'''
    
    opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>{title}</dc:title>
<dc:creator>{author}</dc:creator>
<dc:identifier id="id">urn:uuid:{bid}</dc:identifier>
<dc:language>fa</dc:language>
</metadata>
<manifest>
<item id="nav" href="nav.html" media-type="application/xhtml+xml" properties="nav"/>
{''.join(manifest)}
</manifest>
<spine page-progression-direction="rtl">
{''.join(spine)}
</spine>
</package>'''
    
    ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="urn:uuid:{bid}"/></head>
<docTitle><text>{title}</text></docTitle>
<navMap>
{''.join(f'<navPoint id="c{i+1:04d}" playOrder="{i+1}"><navLabel><text>بخش {i+1}</text></navLabel><content src="c{i+1:04d}.html"/></navPoint>' for i in range(len(chapters)))}
</navMap>
</ncx>'''
    
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>''')
        z.writestr('OEBPS/content.opf', opf)
        z.writestr('OEBPS/toc.ncx', ncx)
        z.writestr('OEBPS/nav.html', nav)
        for fname, html in files.items():
            z.writestr(f'OEBPS/{fname}', html)
    
    if os.path.exists(out):
        size = os.path.getsize(out)
        print(f"✅ {os.path.basename(out)}")
        print(f"   {size:,} bytes")
        return True
    return False

if __name__ == '__main__':
    print("\n🇮🇷 Persian PDF → EPUB Converter")
    print("by Maryam Mobayen\n")
    
    pdf = input("📄 PDF path: ").strip().strip('"\'')
    if not os.path.exists(pdf):
        print("❌ File not found")
        sys.exit(1)
    
    out = pdf.replace('.pdf', '.epub')
    title = input("📚 Title [Book]: ").strip() or "Book"
    author = input("✍️  Author [Unknown]: ").strip() or "Unknown"
    
    print()
    pages = extract(pdf)
    
    if not pages:
        print("❌ No content extracted")
        print("\n💡 If scanned PDF, install Tesseract:")
        print("   brew install tesseract tesseract-lang")
        sys.exit(1)
    
    ok = epub(title, author, pages, out)
    print()
    
    if ok:
        print(f"✨ Success!")
        print(f"📖 Open: {out}")
    else:
        print("❌ Failed")
        sys.exit(1)
