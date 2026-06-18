#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT to EPUB Converter
Developer: Maryam Mobayen
GitHub: https://github.com/maryam-mobayen/persian-pdf-to-epub
License: MIT

تبدیل فایل متنی (از Google Docs یا OCR) به EPUB برای Kindle
"""

import os, sys, zipfile, uuid, unicodedata, re
from datetime import datetime

def clean(text):
    if not text: return text
    text = unicodedata.normalize('NFC', text)
    for a, p in [('ك', 'ک'), ('ي', 'ی'), ('ة', 'ه')]:
        text = text.replace(a, p)
    return re.sub(r' +', ' ', text).strip()

def epub(title, author, content, out):
    print("⚙️ Building EPUB...")
    bid = str(uuid.uuid4())
    
    # Split into chapters
    chapters = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    if not chapters:
        print("❌ No content")
        return False
    
    # Group chapters
    final_chapters = []
    cur = []
    length = 0
    
    for ch in chapters:
        if length + len(ch) > 8000 and cur:
            final_chapters.append('\n\n'.join(cur))
            cur = []
            length = 0
        cur.append(ch)
        length += len(ch)
    
    if cur:
        final_chapters.append('\n\n'.join(cur))
    
    print(f"📚 {len(final_chapters)} chapters")
    
    files, manifest, spine = {}, [], []
    
    for i, text in enumerate(final_chapters):
        ch_id, fname = f'c{i+1:04d}', f'c{i+1:04d}.html'
        
        paras = ''.join(f'<p>{p.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</p>' 
                       for p in text.split('\n') if p.strip())
        
        html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fa" dir="rtl">
<head><meta charset="UTF-8"/><title>Ch {i+1}</title>
<style>body{{direction:rtl;text-align:right;font-family:Georgia,serif;margin:1em;}}
p{{direction:rtl;text-align:right;margin:0.5em 0;text-indent:1.5em;}}</style></head>
<body><h2>بخش {i+1}</h2>{paras}</body></html>'''
        
        files[fname] = html
        manifest.append(f'<item id="{ch_id}" href="{fname}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{ch_id}"/>')
    
    nav = f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="fa" dir="rtl">
<head><meta charset="UTF-8"/></head>
<body dir="rtl"><nav epub:type="toc"><ol dir="rtl">
{''.join(f'<li><a href="c{i+1:04d}.html">بخش {i+1}</a></li>' for i in range(len(final_chapters)))}
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
{''.join(f'<navPoint id="c{i+1:04d}" playOrder="{i+1}"><navLabel><text>بخش {i+1}</text></navLabel><content src="c{i+1:04d}.html"/></navPoint>' for i in range(len(final_chapters)))}
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
        print(f"✅ {os.path.basename(out)} ({os.path.getsize(out):,} bytes)")
        return True
    return False

if __name__ == '__main__':
    print("\n🇮🇷 TXT → EPUB Converter")
    print("by Maryam Mobayen\n")
    
    txt = input("📄 TXT path: ").strip().strip('"\'')
    if not os.path.exists(txt):
        print("❌ Not found")
        sys.exit(1)
    
    out = txt.replace('.txt', '.epub')
    title = input("📚 Title [Book]: ").strip() or "Book"
    author = input("✍️  Author [Unknown]: ").strip() or "Unknown"
    
    with open(txt, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = clean(content)
    
    if not content:
        print("❌ Empty file")
        sys.exit(1)
    
    print(f"\n📖 {len(content):,} characters")
    
    ok = epub(title, author, content, out)
    print()
    
    if ok:
        print(f"✨ Success!\n📖 {out}")
    else:
        print("❌ Failed")
        sys.exit(1)
