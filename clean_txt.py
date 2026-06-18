#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove Repeated Text from TXT
Developer: Maryam Mobayen
GitHub: https://github.com/maryam-mobayen/persian-pdf-to-epub
License: MIT

حذف متن‌های تکراری (مثل واترمارک) از فایل متنی
"""

import os, sys, re

def clean_repeated(txt_path, remove_texts=None):
    """Remove repeated text from file"""
    
    if not os.path.exists(txt_path):
        print(f"❌ {txt_path} not found")
        return
    
    print(f"📖 Reading {os.path.basename(txt_path)}...")
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content)
    
    # Default repeated texts to remove
    if not remove_texts:
        remove_texts = [
            'PDF.tarikhema.org',
            'tarikhema.org',
            'PDF.tarikhema.org\nPDF.tarikhema.org\ntarikhema.org',
        ]
    
    print(f"🧹 Removing repeated text...")
    
    # Remove each text
    for text in remove_texts:
        if text in content:
            count = content.count(text)
            content = content.replace(text, '')
            print(f"   ✓ Removed '{text}' ({count} times)")
    
    # Clean extra whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    
    new_size = len(content)
    removed = original_size - new_size
    
    # Save
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Done!")
    print(f"   Original: {original_size:,} characters")
    print(f"   Cleaned: {new_size:,} characters")
    print(f"   Removed: {removed:,} characters")

if __name__ == '__main__':
    print("\n🧹 Remove Repeated Text from TXT")
    print("by Maryam Mobayen\n")
    
    txt = input("📄 TXT path: ").strip().strip('"\'')
    
    if not os.path.exists(txt):
        print("❌ Not found")
        sys.exit(1)
    
    print("\n📝 Removing:")
    print("   - PDF.tarikhema.org")
    print("   - tarikhema.org")
    print()
    
    clean_repeated(txt)
    
    print(f"\n💡 Now run: python3 txt_to_epub.py")
