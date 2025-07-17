# TaxAgent Pro 🤖

**Professional AI-Powered Tax Document Processing**

A sophisticated web application that leverages Google Gemini AI to automatically extract tax data from documents and generate completed IRS Form 1040 returns with professional dark mode interface.

![TaxAgent Pro](https://img.shields.io/badge/TaxAgent-Pro-blue?style=for-the-badge&logo=python)
![AI Powered](https://img.shields.io/badge/AI-Powered-green?style=for-the-badge&logo=google)
![Dark Mode](https://img.shields.io/badge/UI-Dark%20Mode-black?style=for-the-badge)

## ✨ Features

### 🎯 **Core Capabilities**
- **AI Document Analysis**: Advanced Google Gemini AI extracts tax data from W-2, 1099-INT, and 1099-NEC documents
- **Automatic Tax Calculations**: 2024 IRS-compliant progressive tax calculations with standard deductions
- **Multiple Form Outputs**: Three professional form generation options
- **Real IRS Form Filling**: Populates actual IRS Form 1040 PDF templates with extracted data

### 🎨 **Professional Interface**
- **Modern Dark Mode**: Sophisticated dark theme with smooth animations
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Drag & Drop Upload**: Intuitive file upload with progress indicators
- **Professional Branding**: Corporate-grade UI/UX design

### 🔒 **Enterprise Security**
- **Secure File Handling**: Encrypted file uploads with automatic cleanup
- **Input Validation**: Comprehensive file type and size validation
- **Error Handling**: Professional error management and user feedback
- **Production Logging**: Structured logging for monitoring and debugging

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/taxagent-pro.git
   cd taxagent-pro
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key_here"
   export SECRET_KEY="your_secure_secret_key_here"
   ```

5. **Launch the application**
   ```bash
   python app.py
   ```

6. **Access the interface**
   Open your browser to `http://localhost:8080`

## 📋 Supported Documents

| Document Type | Description | Extracted Data |
|---------------|-------------|----------------|
| **W-2** | Employee wage statement | Wages, federal withholding, employer info |
| **1099-INT** | Interest income | Interest amounts, tax withholding |
| **1099-NEC** | Non-employee compensation | Contract income, backup withholding |

## 📊 Form Generation Options

### 1. **Simple Summary** 📄
- Clean, readable tax summary
- Educational format
- Perfect for review and verification

### 2. **Professional Form** 🏢
- Corporate-style tax document
- Professional layout and formatting
- Suitable for business use

### 3. **Official IRS Form 1040** 🏛️
- Actual IRS PDF template with data filled in
- Government-compliant formatting
- Ready for official submission review

## 🔧 Technical Architecture

### **Backend Components**
```
TaxAgent Pro/
├── app.py                          # Main Flask application
├── tax_calculator.py               # 2024 tax calculation engine
├── form_generator.py               # Simple form generation
├── official_form_generator.py      # Professional form creation
├── irs_form_filler_corrected.py    # Official IRS form filling
└── f1040.pdf                       # Official IRS template
```

### **AI Processing Pipeline**
1. **Document Upload** → Secure file validation and storage
2. **Text Extraction** → PyMuPDF for PDF text extraction
3. **AI Analysis** → Google Gemini processes document content
4. **Tax Calculation** → 2024 IRS tax brackets and deductions
5. **Form Generation** → Multiple professional output formats

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secure_secret_key_here

# Optional
PORT=8080
FLASK_ENV=production
```

### File Limits
- **Maximum file size**: 16MB
- **Supported formats**: PDF, PNG, JPG, JPEG
- **Processing timeout**: 30 seconds

## 🛡️ Security Features

- **Secure file uploads** with content type validation
- **Automatic file cleanup** after processing
- **Session security** with HTTP-only cookies
- **Input sanitization** for all user data
- **Error handling** without sensitive data exposure

## 📈 Production Deployment

### **Docker Deployment**
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
# Production environment variables
export FLASK_ENV=production
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')
export GEMINI_API_KEY=your_production_api_key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License



## 🆘 Support

- **Documentation**: Check this README for detailed setup instructions
- **Issues**: Report bugs via GitHub Issues
- **Email**: support@taxagentpro.com

## 🙏 Acknowledgments

- **Google Gemini AI** for advanced document processing
- **IRS** for official Form 1040 templates
- **PyMuPDF** for reliable PDF text extraction
- **Flask** for the robust web framework

---

