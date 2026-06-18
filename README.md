# 🇮🇷 Persian PDF to EPUB Converter

**تبدیل PDF فارسی به EPUB برای Kindle**

---

## 👩‍💻 Developer

**Maryam Mobayen**

---

## ✨ Features

✅ تبدیل PDF فارسی به EPUB
✅ حروف فارسی صحیح (متصل + راست‌چین)
✅ OCR برای PDF اسکن‌شده
✅ EPUB معتبر برای Calibre و Kindle
✅ حذف متن تکراری
✅ رابط ساده

---

## 📋 Requirements

```bash
pip3 install PyMuPDF arabic-reshaper PyQt5
```

**برای PDF اسکن‌شده:**
```bash
pip3 install pytesseract Pillow
brew install tesseract tesseract-lang
```

---

## 🚀 Usage

### PDF معمولی:
```bash
python3 final.py
```

### PDF اسکن‌شده:
```bash
python3 convert.py
```

### TXT به EPUB:
```bash
python3 txt_to_epub.py
```

### حذف متن تکراری:
```bash
python3 clean_txt.py
```

---

## 📖 مثال

```
📄 PDF path: /path/to/book.pdf
📚 Title [Book]: کتاب نام
✍️ Author [Unknown]: نویسنده

📖 Reading book.pdf...
✅ 100 pages
⚙️ Building EPUB...
✅ book.epub (250KB)
✨ Success!
```

---

## 🎯 Process

1. **PDF → Text** (extract)
2. **Persian Fix** (reshape & RTL)
3. **XHTML** (chapters)
4. **EPUB** (standard format)
5. **Kindle** (ready!)

---

## 🛠️ Tools Used

- **PyMuPDF** - PDF reading
- **arabic-reshaper** - Persian text
- **pytesseract** - OCR
- **PyQt5** - GUI (optional)

---

## 📝 License

MIT License - Free for everyone

---

## 💬 Support

نیاز کمک؟ Issue بسازید!

---

**Made with ❤️ by Maryam Mobayen**
