# 🚀 AI Tax Agent Setup Guide

## 📋 **Prerequisites**

- **Python 3.9+** installed
- **Git** installed
- **Google Gemini API Key** (free tier available)

---

## 🔧 **Quick Setup**

### **1. Clone the Repository**
```bash
git clone https://github.com/RACERNOX/AI-TAX.git
cd AI-TAX
```

### **2. Create Virtual Environment**
```bash
python -m venv venv

# Activate virtual environment:
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure Environment Variables**
Create a `.env` file in the project root:
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
PORT=8080
SECRET_KEY=your_secure_secret_key_here
```

**🔑 Get Gemini API Key:**
1. Visit: https://makersuite.google.com/app/apikey
2. Create a new API key (free tier available)
3. Copy and paste into `.env` file

### **5. Run the Application**
```bash
python app.py
```

### **6. Access the Application**
Open your browser to: **http://localhost:8080**

---

## 📁 **Project Structure**

```
AI-TAX/
├── app.py                          # Main Flask application
├── tax_calculator.py               # 2024 tax calculation engine  
├── form_generator.py               # Simple form generation
├── irs_form_filler_corrected.py    # Official IRS form filling
├── f1040.pdf                       # Official IRS Form 1040 template
├── templates/
│   └── index.html                  # Web interface
├── sample_*.txt                    # Sample tax documents for testing
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── SECURITY_COMPLIANCE.md          # Security measures documentation
└── .gitignore                      # Git ignore file
```

---

## 🔒 **Security Features**

- **✅ SSN Masking**: All SSNs displayed as `XXX**XXXX`
- **✅ Memory-Only Processing**: No files stored on disk
- **✅ Secure Sessions**: HTTP-only cookies with CSRF protection
- **✅ Input Validation**: Comprehensive file and data validation
- **✅ Error Handling**: No sensitive data exposed in errors

---

## 📄 **Supported Documents**

| Document Type | Description | Extracted Data |
|---------------|-------------|----------------|
| **W-2** | Employee wage statement | Wages, federal withholding, employer info |
| **1099-INT** | Interest income | Interest amounts, tax withholding |
| **1099-NEC** | Non-employee compensation | Contract income, backup withholding |
| **1099-DIV** | Dividend income | Dividend amounts |
| **1099-MISC** | Miscellaneous income | Other income types |

---

## 🔧 **Configuration Options**

### **Environment Variables**
```bash
# Required
GEMINI_API_KEY=your_api_key           # Google Gemini API key

# Optional  
PORT=8080                             # Server port (default: 8080)
SECRET_KEY=your_secret_key            # Flask secret key (auto-generated if not set)
FLASK_ENV=production                  # Environment mode
```

### **File Limits**
- **Maximum file size**: 16MB per file
- **Maximum files**: 10 files per upload
- **Supported formats**: PDF, PNG, JPG, JPEG
- **Processing timeout**: 30 seconds per file

---

## 🧪 **Testing the Application**

### **1. Use Sample Documents**
The project includes sample tax documents:
- `sample_w2_higher_income.txt`
- `sample_1099_int.txt` 
- `sample_1099_nec.txt`

### **2. Test Multiple File Upload**
- Upload 2-5 sample documents at once
- Verify combined calculations
- Download generated IRS Form 1040

### **3. Verify Security**
- Check that SSNs show as `XXX**XXXX` in outputs
- Confirm no sensitive data in browser console
- Verify files are not saved to disk

---

## 🚀 **Production Deployment**

### **Docker Deployment** (Recommended)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "app.py"]
```

### **Environment Setup**
```bash
# Production environment
export FLASK_ENV=production
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')
export GEMINI_API_KEY=your_production_api_key
export PORT=8080
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. Missing API Key**
```
Error: GEMINI_API_KEY environment variable not set
Solution: Add GEMINI_API_KEY to .env file
```

**2. Port Already in Use**
```
Error: Address already in use
Solution: Change PORT in .env file or kill existing process
```

**3. SSL Warning (macOS)**
```
Warning: urllib3 v2 only supports OpenSSL 1.1.1+
Solution: This is a warning only, application works normally
```

**4. Virtual Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## 📞 **Support**

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check README.md for detailed information
- **Security**: Review SECURITY_COMPLIANCE.md for security measures

---

## 🎉 **You're Ready!**

Your AI Tax Agent is now set up and ready to process tax documents with enterprise-grade security and accuracy!

**Next Steps:**
1. Upload some sample tax documents
2. Review the generated calculations
3. Download your completed IRS Form 1040
4. Explore the multiple file upload feature

---

*Built with ❤️ for GreenGrowth CPAs | Powered by Google Gemini AI* 