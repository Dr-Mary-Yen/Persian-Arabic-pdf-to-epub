#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persian PDF to EPUB Converter
Developer: Maryam Mobayen
GitHub: https://github.com/maryam-mobayen/persian-pdf-to-epub
License: MIT

تبدیل PDF فارسی به EPUB برای Kindle
"""

import os, sys, subprocess, zipfile, uuid, re, unicodedata, traceback
from datetime import datetime

# Install
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'PyMuPDF', 'arabic-reshaper'], timeout=180)

import fitz
import arabic_reshaper

def clean(text):
    if not text:
        return text
    text = unicodedata.normalize('NFC', text)
    for a, p in [('ك', 'ک'), ('ي', 'ی'), ('ة', 'ه')]:
        text = text.replace(a, p)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def reshape(text):
    try:
        return arabic_reshaper.reshape(text)
    except:
        return text

def extract_pdf(pdf_path):
    print(f"📖 Reading: {pdf_path}")
    pages = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        text = page.get_text('text', flags=fitz.TEXT_PRESERVE_WHITESPACE)
        if text.strip():
            pages.append(clean(text))
    doc.close()
    print(f"✅ {len(pages)} pages")
    return pages

def make_epub(title, author, pages, out_path):
    print(f"⚙️ Building EPUB to: {out_path}")
    
    bid = str(uuid.uuid4())
    now = datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(datetime, 'UTC') else datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Chapters
    chapters = []
    cur = []
    length = 0
    num = 1
    
    for text in pages:
        if length + len(text) > 5000 and cur:
            chapters.append(('\n\n'.join(cur)))
            cur = []
            length = 0
            num += 1
        cur.append(text)
        length += len(text)
    
    if cur:
        chapters.append(('\n\n'.join(cur)))
    
    print(f"📚 {len(chapters)} chapters")
    
    # Files
    manifest = []
    spine = []
    files = {}
    
    for i, content in enumerate(chapters):
        cid = f'c{i+1:04d}'
        fname = f'{cid}.xhtml'
        
        shaped = reshape(content)
        
        paras = []
        for para in shaped.split('\n\n'):
            if para.strip():
                p = para.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                paras.append(f'<p dir="rtl">{p}</p>')
        
        html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fa" dir="rtl">
<head><meta charset="UTF-8"/><title>Ch {i+1}</title>
<style>body{{direction:rtl;text-align:right;margin:1em;font-family:Georgia,serif;}}
p{{direction:rtl;text-align:right;margin:0.5em 0;}}</style>
</head>
<body dir="rtl">
<h2>بخش {i+1}</h2>
{''.join(paras)}
</body>
</html>'''
        
        files[fname] = html
        manifest.append(f'<item id="{cid}" href="{fname}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{cid}"/>')
    
    # Nav
    nav_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="fa" dir="rtl">
<head><meta charset="UTF-8"/><title>فهرست</title></head>
<body dir="rtl"><nav epub:type="toc" dir="rtl"><h1>فهرست</h1><ol dir="rtl">
{chr(10).join(f'<li><a href="c{i+1:04d}.xhtml">بخش {i+1}</a></li>' for i in range(len(chapters)))}
</ol></nav></body>
</html>'''
    
    # OPF
    opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID" xml:lang="fa">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="BookID">urn:uuid:{bid}</dc:identifier>
<dc:title>{title}</dc:title>
<dc:creator>{author}</dc:creator>
<dc:language>fa</dc:language>
<dc:date>{now}</dc:date>
</metadata>
<manifest>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
{chr(10).join(manifest)}
</manifest>
<spine toc="ncx" page-progression-direction="rtl">
{chr(10).join(spine)}
</spine>
</package>'''
    
    # NCX
    ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="fa">
<head><meta name="dtb:uid" content="urn:uuid:{bid}"/></head>
<docTitle><text>{title}</text></docTitle>
<navMap>
{chr(10).join(f'<navPoint id="c{i+1:04d}" playOrder="{i+1}"><navLabel><text>بخش {i+1}</text></navLabel><content src="c{i+1:04d}.xhtml"/></navPoint>' for i in range(len(chapters)))}
</navMap>
</ncx>'''
    
    # Container
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    
    # Create
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', container)
        z.writestr('OEBPS/content.opf', opf)
        z.writestr('OEBPS/toc.ncx', ncx)
        z.writestr('OEBPS/nav.xhtml', nav_html)
        for fname, html in files.items():
            z.writestr(f'OEBPS/{fname}', html)
    
    if os.path.exists(out_path):
        size = os.path.getsize(out_path)
        print(f"✅ Done: {out_path} ({size} bytes)")
        return True
    return False

# Main
if __name__ == '__main__':
    try:
        from PyQt5.Qt import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QFileDialog, QMessageBox, QTextEdit, 
                              QGroupBox, Qt, QFont)
    except:
        print("نصب: pip3 install PyQt5")
        sys.exit(1)
    
    class App(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('Persian Kindle Fix - by Maryam Mobayen')
            self.setMinimumWidth(650)
            
            lay = QVBoxLayout(self)
            
            title = QLabel('🇮🇷 Persian Kindle Fix')
            title.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(16)
            font.setBold(True)
            title.setFont(font)
            title.setStyleSheet('color:#2c7a7b; margin:10px;')
            lay.addWidget(title)
            
            developer = QLabel('by Maryam Mobayen')
            developer.setAlignment(Qt.AlignCenter)
            developer.setStyleSheet('color:#666; margin-bottom:15px; font-size:10px;')
            lay.addWidget(developer)
            
            g1 = QGroupBox('PDF')
            l1 = QHBoxLayout(g1)
            self.pdf = QLineEdit()
            l1.addWidget(self.pdf)
            b1 = QPushButton('انتخاب')
            b1.clicked.connect(self._browse_pdf)
            l1.addWidget(b1)
            lay.addWidget(g1)
            
            g2 = QGroupBox('عنوان/نویسنده')
            l2 = QVBoxLayout(g2)
            l2a = QHBoxLayout()
            l2a.addWidget(QLabel('عنوان:'))
            self.title = QLineEdit()
            l2a.addWidget(self.title)
            l2.addLayout(l2a)
            l2b = QHBoxLayout()
            l2b.addWidget(QLabel('نویسنده:'))
            self.author = QLineEdit()
            l2b.addWidget(self.author)
            l2.addLayout(l2b)
            lay.addWidget(g2)
            
            g3 = QGroupBox('خروجی')
            l3 = QHBoxLayout(g3)
            self.out = QLineEdit()
            l3.addWidget(self.out)
            b3 = QPushButton('انتخاب')
            b3.clicked.connect(self._browse_out)
            l3.addWidget(b3)
            lay.addWidget(g3)
            
            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(100)
            lay.addWidget(QLabel('گزارش:'))
            lay.addWidget(self.log)
            
            self.btn = QPushButton('🔄 تبدیل')
            self.btn.setStyleSheet('background:#2c7a7b; color:white; padding:8px; font-weight:bold;')
            self.btn.clicked.connect(self._convert)
            lay.addWidget(self.btn)
        
        def _browse_pdf(self):
            p, _ = QFileDialog.getOpenFileName(self, 'PDF', '', 'PDF (*.pdf)')
            if p:
                self.pdf.setText(p)
                base = os.path.splitext(os.path.basename(p))[0]
                self.out.setText(os.path.join(os.path.dirname(p), base + '.epub'))
        
        def _browse_out(self):
            p, _ = QFileDialog.getSaveFileName(self, 'EPUB', '', 'EPUB (*.epub)')
            if p:
                self.out.setText(p)
        
        def _convert(self):
            pdf = self.pdf.text()
            out = self.out.text()
            title = self.title.text() or 'کتاب'
            author = self.author.text() or 'نامشخص'
            
            if not pdf or not os.path.exists(pdf):
                QMessageBox.critical(self, 'خطا', 'PDF معتبر انتخاب کنید')
                return
            
            self.log.clear()
            self.log.append(f'شروع: {os.path.basename(pdf)}')
            
            try:
                pages = extract_pdf(pdf)
                self.log.append(f'✅ استخراج')
                
                ok = make_epub(title, author, pages, out)
                if ok:
                    self.log.append(f'✅ {out}')
                    QMessageBox.information(self, 'موفق', f'EPUB ساخته شد!\n\n{out}')
                else:
                    self.log.append('❌ خطا')
                    QMessageBox.critical(self, 'خطا', 'فایل ساخته نشد')
            except Exception as e:
                self.log.append(f'❌ {e}')
                QMessageBox.critical(self, 'خطا', str(e))
    
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
