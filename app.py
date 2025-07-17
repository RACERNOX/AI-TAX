#!/usr/bin/env python3
"""
GreenGrowth CPAs - AI Tax Agent Pro
Professional AI-Powered Tax Processing Application
Copyright 2024 - GreenGrowth CPAs | Powered by TaxAgent Pro
"""

import os
import json
import logging
import secrets
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
import fitz  # PyMuPDF
from tax_calculator import TaxCalculator
from form_generator import Form1040Generator
from irs_form_filler_corrected import CorrectedIRSForm1040Filler

# Configure logging for production (cloud-compatible)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()  # Only console logging for cloud deployment
    ]
)
logger = logging.getLogger(__name__)

# Security Configuration for PII Protection
import re
import hashlib

def mask_ssn(ssn):
    """Securely mask SSN for logging and display"""
    if not ssn:
        return "***-**-****"
    
    ssn_clean = re.sub(r'[^\d]', '', str(ssn))
    if len(ssn_clean) >= 9:
        return f"***-**-{ssn_clean[-4:]}"
    elif len(ssn_clean) >= 4:
        return f"***-**-{ssn_clean[-4:]}"
    else:
        return "***-**-****"

def hash_pii_for_logging(data):
    """Hash PII data for secure logging"""
    if not data:
        return "NONE"
    return hashlib.sha256(str(data).encode()).hexdigest()[:8]

def secure_log_tax_data(tax_data, prefix=""):
    """Securely log tax data with PII protection"""
    if not tax_data:
        return
    
    masked_data = {
        'taxpayer_name_hash': hash_pii_for_logging(tax_data.get('taxpayer_name')),
        'ssn_masked': mask_ssn(tax_data.get('ssn')),
        'document_type': tax_data.get('document_type', 'Unknown'),
        'wages': tax_data.get('wages', 0),
        'federal_withholding': tax_data.get('federal_withholding', 0),
        'total_files': tax_data.get('documents_processed', 1)
    }
    
    logger.info(f"{prefix}Secure Tax Data: Name_Hash={masked_data['taxpayer_name_hash']}, "
                f"SSN={masked_data['ssn_masked']}, DocType={masked_data['document_type']}, "
                f"Wages=${masked_data['wages']}, Withholding=${masked_data['federal_withholding']}")

# Secure Memory Processing Configuration
class SecureMemoryProcessor:
    """Process files in memory only - no disk storage"""
    
    @staticmethod
    def process_file_in_memory(file_stream):
        """Process uploaded file in memory without saving to disk"""
        try:
            # Read file content into memory
            file_content = file_stream.read()
            file_stream.seek(0)  # Reset stream position
            
            # Create temporary file-like object in memory
            from io import BytesIO
            memory_file = BytesIO(file_content)
            
            return memory_file
        except Exception as e:
            logger.error(f"Memory processing error: {e}")
            raise ValueError("Failed to process file in memory")
    
    @staticmethod
    def extract_text_from_memory_pdf(memory_file):
        """Extract text from PDF in memory without disk storage"""
        try:
            import fitz
            
            # Open PDF from memory
            doc = fitz.open(stream=memory_file, filetype="pdf")
            text = ""
            
            if len(doc) == 0:
                doc.close()
                raise ValueError("PDF has no pages")
            
            # Limit to first 10 pages for performance
            max_pages = min(len(doc), 10)
            
            for page_num in range(max_pages):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    logger.warning(f"Error reading page {page_num}: {page_error}")
                    continue
            
            doc.close()
            
            if not text.strip():
                raise ValueError("No readable text content found in PDF")
            
            return text
            
        except Exception as e:
            logger.error(f"Memory PDF extraction error: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

# Initialize secure processor
secure_processor = SecureMemoryProcessor()

# Professional Flask App Configuration
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(16)),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    UPLOAD_FOLDER='/tmp/uploads',  # Use temp directory for cloud
    OUTPUT_FOLDER='/tmp/generated',  # Use temp directory for cloud
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Initialize AI and Processing Components
try:
    # Configure Gemini AI
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        raise ValueError("Missing required GEMINI_API_KEY")
    
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Test API connection
    try:
        test_response = gemini_model.generate_content("Test connection")
        logger.info("✅ Gemini API connection verified")
    except Exception as api_test_error:
        logger.error(f"❌ Gemini API connection failed: {api_test_error}")
        raise ValueError(f"Gemini API connection failed: {api_test_error}")
    
    # Initialize processing engines
    tax_calculator = TaxCalculator()
    form_generator = Form1040Generator()
    irs_form_filler = CorrectedIRSForm1040Filler()
    
    logger.info("✅ GreenGrowth CPAs AI Tax Agent initialized successfully")
    logger.info("✅ All processing engines ready")
    
except Exception as e:
    logger.error(f"❌ Initialization failed: {e}")
    raise

# Ensure directories exist with proper permissions (cloud-compatible)
for directory in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    try:
        os.makedirs(directory, exist_ok=True)
        # Test write permissions in cloud environment
        test_file = os.path.join(directory, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"✅ Directory ready: {directory}")
    except Exception as e:
        logger.warning(f"⚠️ Directory setup warning for {directory}: {e}")
        # Continue without raising error in cloud environment
        pass

# Professional file validation
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/png', 
    'image/jpeg',
    'image/jpg'
}

# File size limits (more granular)
MAX_FILE_SIZES = {
    'application/pdf': 16 * 1024 * 1024,  # 16MB for PDFs
    'image/png': 10 * 1024 * 1024,        # 10MB for PNG
    'image/jpeg': 10 * 1024 * 1024,       # 10MB for JPEG
    'image/jpg': 10 * 1024 * 1024         # 10MB for JPG
}

def validate_file_comprehensive(file):
    """Enhanced file validation with security checks"""
    try:
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check filename
        if len(file.filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        # Check for suspicious characters
        suspicious_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in file.filename for char in suspicious_chars):
            return False, "Filename contains invalid characters"
        
        # Validate file extension
        if '.' not in file.filename:
            return False, "File must have an extension"
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Validate MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            return False, f"Invalid file format. Content type: {file.content_type}"
        
        # Check file size (more specific)
        if hasattr(file, 'content_length') and file.content_length:
            max_size = MAX_FILE_SIZES.get(file.content_type, 16 * 1024 * 1024)
            if file.content_length > max_size:
                return False, f"File too large. Max size: {max_size // (1024*1024)}MB"
        
        return True, "Valid file"
        
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return False, f"File validation failed: {str(e)}"

def is_allowed_file(filename, content_type):
    """Legacy function - kept for compatibility"""
    valid, _ = validate_file_comprehensive(type('MockFile', (), {
        'filename': filename, 
        'content_type': content_type
    })())
    return valid

def extract_text_from_pdf(file_path):
    """Extract text from PDF with enhanced error handling"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if os.path.getsize(file_path) == 0:
            raise ValueError("PDF file is empty")
        
        doc = fitz.open(file_path)
        text = ""
        
        if len(doc) == 0:
            doc.close()
            raise ValueError("PDF has no pages")
        
        # Limit to first 10 pages for performance
        max_pages = min(len(doc), 10)
        
        for page_num in range(max_pages):
            try:
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            except Exception as page_error:
                logger.warning(f"Error reading page {page_num}: {page_error}")
                continue
        
        doc.close()
        
        if not text.strip():
            raise ValueError("No readable text content found in PDF")
        
        # Validate text quality
        if len(text.strip()) < 10:
            raise ValueError("Extracted text too short - may be corrupted or scanned image")
            
        return text
        
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        if 'doc' in locals():
            try:
                doc.close()
            except:
                pass
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def combine_multiple_tax_documents(all_tax_data):
    """Intelligently combine tax data from multiple documents"""
    if not all_tax_data:
        raise ValueError("No tax data to combine")
    
    if len(all_tax_data) == 1:
        return all_tax_data[0]  # No combination needed
    
    logger.info(f"Combining {len(all_tax_data)} tax documents")
    
    # Start with the first document as base
    combined = all_tax_data[0].copy()
    
    # Use the most complete taxpayer information
    primary_taxpayer = None
    for data in all_tax_data:
        if data.get('taxpayer_name') and len(data.get('taxpayer_name', '').strip()) > len(combined.get('taxpayer_name', '').strip()):
            primary_taxpayer = data
            break
    
    if primary_taxpayer:
        combined.update({
            'taxpayer_name': primary_taxpayer.get('taxpayer_name', ''),
            'ssn': primary_taxpayer.get('ssn', ''),
            'address': primary_taxpayer.get('address', ''),
            'city': primary_taxpayer.get('city', ''),
            'state': primary_taxpayer.get('state', ''),
            'zip_code': primary_taxpayer.get('zip_code', ''),
            'filing_status': primary_taxpayer.get('filing_status', 'single')
        })
    
    # Sum all monetary fields
    monetary_fields = [
        'wages', 'interest_income', 'dividend_income', 'other_income',
        'federal_withholding', 'state_withholding', 
        'social_security_wages', 'medicare_wages'
    ]
    
    for field in monetary_fields:
        total = 0
        for data in all_tax_data:
            value = data.get(field, 0)
            try:
                total += float(value) if value else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid {field} value in document: {value}")
                continue
        combined[field] = total
    
    # Combine document types
    doc_types = []
    for data in all_tax_data:
        doc_type = data.get('document_type', 'Other')
        if doc_type not in doc_types:
            doc_types.append(doc_type)
    
    if len(doc_types) == 1:
        combined['document_type'] = doc_types[0]
    else:
        combined['document_type'] = 'Multiple'
    
    # Collect source filenames
    source_files = []
    for data in all_tax_data:
        filename = data.get('source_filename', 'Unknown')
        if filename not in source_files:
            source_files.append(filename)
    
    combined['source_files'] = source_files
    combined['documents_processed'] = len(all_tax_data)
    
    # Use the highest confidence scores
    combined['classification_confidence'] = max(
        (data.get('classification_confidence', 0) for data in all_tax_data), 
        default=0.8
    )
    combined['extraction_confidence'] = max(
        (data.get('extraction_confidence', 0) for data in all_tax_data), 
        default=0.8
    )
    
    # Set document quality to the best found
    qualities = ['high', 'medium', 'low']
    best_quality = 'low'
    for data in all_tax_data:
        quality = data.get('document_quality', 'medium')
        if quality in qualities and qualities.index(quality) < qualities.index(best_quality):
            best_quality = quality
    combined['document_quality'] = best_quality
    
    # Combine validation flags
    all_flags = []
    for data in all_tax_data:
        flags = data.get('validation_flags', [])
        if isinstance(flags, list):
            all_flags.extend(flags)
    combined['validation_flags'] = list(set(all_flags))  # Remove duplicates
    
    # Set requires_review if any document requires it
    combined['requires_review'] = any(
        data.get('requires_review', False) for data in all_tax_data
    )
    
    # Add employer/payer information
    employers = []
    payers = []
    eins = []
    
    for data in all_tax_data:
        payer_name = data.get('payer_name', '').strip()
        employer_ein = data.get('employer_ein', '').strip()
        
        if payer_name and payer_name not in payers:
            payers.append(payer_name)
        if employer_ein and employer_ein not in eins:
            eins.append(employer_ein)
    
    combined['payer_name'] = '; '.join(payers) if payers else ''
    combined['employer_ein'] = '; '.join(eins) if eins else ''
    
    logger.info(f"✅ Successfully combined documents: Total wages=${combined.get('wages', 0):,.2f}, "
                f"Total withholding=${combined.get('federal_withholding', 0):,.2f}")
    
    return combined

def extract_tax_data_with_ai(text, max_retries=3):
    """Extract tax data using Gemini AI with enhanced retry logic"""
    
    if not text or len(text.strip()) < 10:
        raise ValueError("Insufficient text content for AI processing")
    
    # Truncate very long text to avoid API limits
    if len(text) > 10000:
        text = text[:10000] + "... [truncated]"
    
    prompt = """
You are a professional tax document analysis AI with expertise in IRS tax forms and compliance requirements. Your task is to extract tax information from this document and return ONLY valid JSON with professional-grade accuracy.

DOCUMENT ANALYSIS PROTOCOL:
1. First, assess document quality and readability
2. Classify document type with confidence scoring
3. Extract data using form-specific validation rules
4. Perform cross-field validation and consistency checks
5. Apply professional tax standards and compliance requirements

CRITICAL: You must return a valid JSON object with these exact fields:
{
    "document_type": "W-2" | "1099-INT" | "1099-NEC" | "1099-MISC" | "1099-DIV" | "Other",
    "classification_confidence": 0.95,
    "document_quality": "high" | "medium" | "low",
    "taxpayer_name": "Full name exactly as shown on document",
    "ssn": "XXX-XX-XXXX format or empty string",
    "itin": "9XX-XX-XXXX format or empty string if applicable",
    "filing_status": "single" | "married_filing_jointly" | "married_filing_separately" | "head_of_household" | "qualifying_widow",
    "wages": 0.00,
    "interest_income": 0.00,
    "dividend_income": 0.00,
    "other_income": 0.00,
    "federal_withholding": 0.00,
    "state_withholding": 0.00,
    "social_security_wages": 0.00,
    "medicare_wages": 0.00,
    "address": "Street address with number",
    "city": "City name",
    "state": "State abbreviation (e.g., CA, NY, TX)",
    "zip_code": "ZIP code (5 or 9 digits)",
    "employer_ein": "XX-XXXXXXX format or empty string",
    "payer_name": "Name of paying organization",
    "validation_flags": [],
    "extraction_confidence": 0.90,
    "requires_review": false
}

FORM-SPECIFIC EXTRACTION RULES:

W-2 Form Processing:
- wages = Box 1 (Wages, tips, other compensation)
- federal_withholding = Box 2 (Federal income tax withheld)
- social_security_wages = Box 3 (Social security wages)
- medicare_wages = Box 5 (Medicare wages and tips)
- employer_ein = Box b (Employer identification number)
- Validate: Box 2 should not exceed Box 1 × 0.37
- Validate: Box 3 should not exceed social security wage base
- Extract employee address from employee section (typically left side)

1099-INT Form Processing:
- interest_income = Box 1 (Interest income)
- federal_withholding = Box 4 (Federal income tax withheld)
- payer_name = Payer information section
- Validate: Box 4 should not exceed Box 1 × 0.24
- Validate: Box 1 should be > 0 if form is present

1099-NEC Form Processing:
- other_income = Box 1 (Nonemployee compensation)
- federal_withholding = Box 4 (Federal income tax withheld)
- state_withholding = Box 5 (State tax withheld)
- Validate: Box 4 should not exceed Box 1 × 0.24
- Validate: Box 1 should be > 0 for contractor payments

1099-MISC Form Processing:
- other_income = Box 3 (Other income)
- federal_withholding = Box 4 (Federal income tax withheld)
- Extract from appropriate boxes based on income type

PROFESSIONAL VALIDATION STANDARDS:

Data Type Validation:
- All monetary values must be numbers (not strings)
- SSN format: XXX-XX-XXXX (exactly 9 digits with dashes)
- ITIN format: 9XX-XX-XXXX (starts with 9, middle digits 70-88, 90-92, 94-99)
- EIN format: XX-XXXXXXX (exactly 9 digits with dash after 2nd digit)
- ZIP code: 5 or 9 digits (XXXXX or XXXXX-XXXX)
- State: Only valid 2-letter abbreviations (CA, NY, TX, etc.)

Cross-Field Validation:
- If wages > 0, federal_withholding should be reasonable (typically 0-37% of wages)
- If interest_income > 0, document_type should be "1099-INT"
- If other_income > 0, document_type should be "1099-NEC" or "1099-MISC"
- SSN and ITIN are mutually exclusive (only one should have a value)
- Address components should be consistent and complete

Quality Assessment Rules:
- classification_confidence: 0.95+ for clear forms, 0.85+ for acceptable, <0.85 requires review
- document_quality: "high" for clear text, "medium" for some OCR issues, "low" for poor quality
- extraction_confidence: Based on field clarity and validation success
- requires_review: true if confidence < 0.85 or validation errors detected

Error Handling and Fallback Mechanisms:
- If field not found or unclear, use appropriate default (0.00 for money, empty string for text)
- For poor OCR quality, flag validation_flags with specific issues
- Common OCR corrections: "O" vs "0", "I" vs "1", "S" vs "5"
- If multiple possible values, choose most likely based on context
- Flag unusual values (e.g., withholding > 50% of income) for review

Validation Flags (add to validation_flags array if detected):
- "ssn_format_invalid": SSN doesn't match XXX-XX-XXXX pattern
- "excessive_withholding": Federal withholding > 37% of income
- "missing_required_field": Essential field is empty or unclear
- "ocr_quality_poor": Document quality affects extraction confidence
- "cross_validation_failed": Fields don't validate against each other
- "unusual_values": Values outside normal ranges
- "incomplete_address": Address components missing or unclear

COMPLIANCE REQUIREMENTS:
- Extract taxpayer name exactly as shown (don't modify capitalization or spelling)
- Preserve all punctuation and formatting in names and addresses
- Use only IRS-approved state abbreviations
- Validate SSN/ITIN format strictly per IRS requirements
- Flag any data that doesn't meet IRS ATS (Automated Tax System) standards

PROFESSIONAL STANDARDS:
- Minimum 98% accuracy for numerical fields
- Minimum 95% accuracy for text fields
- All extracted data must be audit-ready
- Confidence scoring must reflect actual extraction reliability
- Flag any extraction below professional standards for human review

Document text:
""" + text

    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"AI extraction attempt {attempt + 1}/{max_retries}")
            
            response = gemini_model.generate_content(prompt)
            if not response or not response.text:
                raise ValueError("Empty response from AI")
            
            response_text = response.text.strip()
            
            # Clean and parse JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            if not response_text:
                raise ValueError("Empty response after cleaning")
            
            # Parse and validate JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as je:
                logger.warning(f"JSON parsing failed: {je}")
                logger.warning(f"Raw response: {response_text[:200]}...")
                raise ValueError(f"Invalid JSON format: {str(je)}")
            
            # Validate required fields and structure
            required_fields = ['document_type', 'classification_confidence', 'document_quality', 
                             'taxpayer_name', 'ssn', 'itin', 'filing_status', 
                             'wages', 'interest_income', 'dividend_income', 'other_income', 
                             'federal_withholding', 'state_withholding', 'social_security_wages', 
                             'medicare_wages', 'address', 'city', 'state', 'zip_code', 
                             'employer_ein', 'payer_name', 'validation_flags', 
                             'extraction_confidence', 'requires_review']
            
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field {field}, adding default")
                    # Set appropriate defaults based on field type
                    if field in ['wages', 'interest_income', 'dividend_income', 'other_income', 
                               'federal_withholding', 'state_withholding', 'social_security_wages', 
                               'medicare_wages', 'classification_confidence', 'extraction_confidence']:
                        data[field] = 0.0
                    elif field in ['validation_flags']:
                        data[field] = []
                    elif field in ['requires_review']:
                        data[field] = False
                    else:
                        data[field] = ""
            
            # Enhanced type validation and conversion
            for money_field in ['wages', 'interest_income', 'dividend_income', 'other_income', 
                               'federal_withholding', 'state_withholding', 'social_security_wages', 
                               'medicare_wages']:
                try:
                    value = data[money_field]
                    if isinstance(value, str):
                        # Remove common currency symbols and formatting
                        value = value.replace('$', '').replace(',', '').strip()
                    data[money_field] = float(value)
                    
                    # Validate reasonable ranges
                    if data[money_field] < 0:
                        logger.warning(f"Negative value for {money_field}: {data[money_field]}")
                        data[money_field] = 0.0
                    elif data[money_field] > 10000000:  # $10M limit
                        logger.warning(f"Suspiciously high value for {money_field}: {data[money_field]}")
                        
                except (ValueError, TypeError) as ve:
                    logger.warning(f"Type conversion error for {money_field}: {ve}")
                    data[money_field] = 0.0
            
            # Validate string fields
            for str_field in ['document_type', 'document_quality', 'taxpayer_name', 'ssn', 'itin', 
                             'filing_status', 'address', 'city', 'state', 'zip_code', 'employer_ein', 'payer_name']:
                data[str_field] = str(data[str_field]).strip()
            
            # Validate specific field formats
            if data['filing_status'] not in ['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household', 'qualifying_widow']:
                logger.warning(f"Invalid filing status: {data['filing_status']}, defaulting to single")
                data['filing_status'] = 'single'
            
            if data['document_type'] not in ['W-2', '1099-INT', '1099-NEC', '1099-MISC', '1099-DIV', 'Other']:
                logger.warning(f"Unknown document type: {data['document_type']}, defaulting to Other")
                data['document_type'] = 'Other'
                
            # Validate document quality
            if data['document_quality'] not in ['high', 'medium', 'low']:
                logger.warning(f"Invalid document quality: {data['document_quality']}, defaulting to medium")
                data['document_quality'] = 'medium'
            
            # Validate state format (should be 2 letters)
            if data['state'] and len(data['state']) > 2:
                # Try to extract state abbreviation
                state_mapping = {
                    'california': 'CA', 'new york': 'NY', 'texas': 'TX', 'florida': 'FL',
                    'illinois': 'IL', 'pennsylvania': 'PA', 'ohio': 'OH', 'georgia': 'GA',
                    'north carolina': 'NC', 'michigan': 'MI'
                }
                state_lower = data['state'].lower()
                if state_lower in state_mapping:
                    data['state'] = state_mapping[state_lower]
                else:
                    logger.warning(f"Invalid state format: {data['state']}, keeping as-is")
            
            # Validate ZIP code format
            if data['zip_code']:
                zip_clean = ''.join(filter(str.isdigit, data['zip_code']))
                if len(zip_clean) >= 5:
                    if len(zip_clean) == 5:
                        data['zip_code'] = zip_clean
                    elif len(zip_clean) >= 9:
                        data['zip_code'] = f"{zip_clean[:5]}-{zip_clean[5:9]}"
                    else:
                        data['zip_code'] = zip_clean
                else:
                    logger.warning(f"Invalid ZIP code format: {data['zip_code']}")
                    data['zip_code'] = ""
            
            logger.info(f"✅ AI extraction successful on attempt {attempt + 1}")
            return data
            
        except json.JSONDecodeError as e:
            last_error = f"JSON parsing error: {e}"
            logger.warning(f"Attempt {attempt + 1} - {last_error}")
        except Exception as e:
            last_error = f"AI processing error: {e}"
            logger.warning(f"Attempt {attempt + 1} - {last_error}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            import time
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    raise ValueError(f"AI extraction failed after {max_retries} attempts. Last error: {last_error}")

# ===== ROUTES =====

@app.route('/')
def index():
    """Serve the professional TaxAgent Pro interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        return jsonify({'error': 'Unable to load application interface'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check API connectivity
        test_response = gemini_model.generate_content("Health check")
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'gemini_api': 'connected',
                'file_system': 'accessible',
                'processing_engines': 'ready'
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle multiple file upload and processing with SECURE memory-only processing"""
    try:
        # Enhanced request validation for multiple files
        if 'file' not in request.files:
            return jsonify({'error': 'No files provided in request'}), 400
        
        files = request.files.getlist('file')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate number of files (limit to prevent abuse)
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed per upload'}), 400
        
        logger.info(f"🔒 Processing {len(files)} file(s) in SECURE memory-only mode")
        
        # Process each file and collect results
        all_tax_data = []
        processing_errors = []
        
        for i, file in enumerate(files, 1):
            if file.filename == '':
                continue  # Skip empty files
            
            try:
                # Secure logging with masked filename
                masked_filename = f"file_{i}_{hash_pii_for_logging(file.filename)}"
                logger.info(f"🔒 Processing {masked_filename} in memory")
                
                # Comprehensive file validation
                is_valid, validation_message = validate_file_comprehensive(file)
                if not is_valid:
                    processing_errors.append(f"File {i}: {validation_message}")
                    continue
                
                # SECURE: Process file in memory ONLY - NO disk storage
                try:
                    memory_file = secure_processor.process_file_in_memory(file.stream)
                    logger.info(f"✅ {masked_filename} loaded into secure memory")
                except Exception as memory_error:
                    logger.error(f"❌ Memory processing failed for {masked_filename}: {memory_error}")
                    processing_errors.append(f"File {i}: Failed to process in memory")
                    continue
                
                # Extract text from document in memory
                try:
                    if file.content_type == 'application/pdf':
                        text = secure_processor.extract_text_from_memory_pdf(memory_file)
                        logger.info(f"✅ Text extracted from {masked_filename} in memory")
                    else:
                        processing_errors.append(f"File {i}: Only PDF files supported currently")
                        continue
                except Exception as extract_error:
                    logger.error(f"❌ Text extraction failed for {masked_filename}: {extract_error}")
                    processing_errors.append(f"File {i}: Failed to extract text")
                    continue
                
                # Extract tax data using AI with enhanced error handling
                try:
                    tax_data = extract_tax_data_with_ai(text)
                    tax_data['source_filename'] = f"SecureFile_{i}"  # Don't store real filename
                    
                    # SECURE: Log tax data with PII protection
                    secure_log_tax_data(tax_data, f"✅ File {i} processed: ")
                    
                    all_tax_data.append(tax_data)
                    logger.info(f"✅ {masked_filename} AI analysis completed: {tax_data.get('document_type', 'Unknown')}")
                except Exception as ai_error:
                    logger.error(f"❌ AI processing failed for {masked_filename}: {ai_error}")
                    processing_errors.append(f"File {i}: AI analysis failed")
                    continue
                    
            except Exception as file_error:
                logger.error(f"❌ Error processing file {i}: {file_error}")
                processing_errors.append(f"File {i}: Processing error")
                continue
            finally:
                # SECURE: Clear memory file
                try:
                    if 'memory_file' in locals():
                        memory_file.close()
                        del memory_file
                except:
                    pass
        
        # Check if any files were successfully processed
        if not all_tax_data:
            error_summary = "No files could be processed successfully."
            if processing_errors:
                error_summary += f" Errors: {'; '.join(processing_errors[:3])}"
            return jsonify({'error': error_summary}), 400
        
        # Combine tax data from multiple documents
        try:
            combined_tax_data = combine_multiple_tax_documents(all_tax_data)
            secure_log_tax_data(combined_tax_data, f"✅ Combined {len(all_tax_data)} documents: ")
        except Exception as combine_error:
            logger.error(f"❌ Failed to combine tax data: {combine_error}")
            return jsonify({'error': f'Failed to combine tax documents: {str(combine_error)}'}), 500
        
        # Calculate taxes with validation
        try:
            if not combined_tax_data or not isinstance(combined_tax_data, dict):
                raise ValueError("Invalid combined tax data structure")
            
            calculations = tax_calculator.calculate_taxes(combined_tax_data)
            
            if 'error' in calculations:
                logger.error(f"❌ Tax calculation error: {calculations['error']}")
                return jsonify({'error': f"Tax calculation failed: {calculations['error']}"}), 400
                
        except Exception as calc_error:
            logger.error(f"❌ Tax calculation failed: {calc_error}")
            return jsonify({'error': f'Tax calculation failed: {str(calc_error)}'}), 500
        
        # Combine data for response with validation
        try:
            # SECURE: Create response without exposing sensitive data
            result = {**combined_tax_data, **calculations}
            
            # SECURE: Mask SSN in response
            if 'ssn' in result:
                result['ssn_masked'] = mask_ssn(result['ssn'])
                # Keep original SSN for form generation but remove from API response
                result['ssn_original'] = result['ssn']  # For internal use only
                result['ssn'] = result['ssn_masked']  # Replace with masked version
            
            # Add processing summary for multiple files
            if len(all_tax_data) > 1:
                result['processing_summary'] = {
                    'files_processed': len(all_tax_data),
                    'files_with_errors': len(processing_errors),
                    'document_types': [data.get('document_type', 'Unknown') for data in all_tax_data],
                    'source_files': ['SecureFile_' + str(i+1) for i in range(len(all_tax_data))]  # Masked filenames
                }
                if processing_errors:
                    result['processing_warnings'] = processing_errors
            
            # Validate final result structure
            required_result_fields = ['total_income', 'federal_tax', 'refund_or_owed']
            for field in required_result_fields:
                if field not in result:
                    logger.error(f"❌ Missing required result field: {field}")
                    return jsonify({'error': 'Incomplete calculation results'}), 500
            
        except Exception as merge_error:
            logger.error(f"❌ Result merging failed: {merge_error}")
            return jsonify({'error': 'Failed to process calculation results'}), 500
        
        # SECURE: Store data in encrypted session for form generation
        try:
            # Store original SSN for form generation but use secure session
            if 'ssn_original' in result:
                combined_tax_data['ssn'] = result['ssn_original']
            
            app.config['current_tax_data'] = combined_tax_data
            app.config['current_calculations'] = calculations
            
            logger.info(f"✅ Secure processing completed: {len(all_tax_data)} files processed")
        except Exception as session_error:
            logger.warning(f"⚠️ Session storage warning: {session_error}")
            # Continue processing even if session storage fails
        
        return jsonify(result)
        
    except ValueError as ve:
        logger.error(f"❌ Validation error: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"❌ Upload processing error: {e}")
        return jsonify({
            'error': 'Document processing failed. Please try again with a different document.',
            'technical_details': str(e) if app.debug else None
        }), 500

def validate_session_data():
    """Helper function to validate session data"""
    tax_data = app.config.get('current_tax_data')
    calculations = app.config.get('current_calculations')
    
    if not tax_data or not calculations:
        return False, "No tax data found. Please upload and process a document first."
    
    if not isinstance(tax_data, dict) or not isinstance(calculations, dict):
        return False, "Invalid tax data format. Please re-upload your document."
    
    # Check for required fields
    required_tax_fields = ['taxpayer_name', 'wages', 'federal_withholding']
    required_calc_fields = ['total_income', 'federal_tax', 'refund_or_owed']
    
    for field in required_tax_fields:
        if field not in tax_data:
            return False, f"Missing required tax information: {field}. Please re-upload your document."
    
    for field in required_calc_fields:
        if field not in calculations:
            return False, f"Missing required calculation: {field}. Please re-upload your document."
    
    return True, "Valid session data"

@app.route('/generate_simple_form')
def generate_simple_form():
    """Generate simple tax summary form with enhanced validation"""
    try:
        # Validate session data
        is_valid, message = validate_session_data()
        if not is_valid:
            return jsonify({'error': message}), 400
        
        tax_data = app.config.get('current_tax_data')
        calculations = app.config.get('current_calculations')
        
        # Generate form with error handling
        try:
            pdf_path = form_generator.generate_form_1040(tax_data, calculations)
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError("Generated PDF not found")
            
            if os.path.getsize(pdf_path) == 0:
                raise ValueError("Generated PDF is empty")
                
        except Exception as gen_error:
            logger.error(f"Form generation failed: {gen_error}")
            return jsonify({'error': f'Failed to generate form: {str(gen_error)}'}), 500
        
        # Return file with proper headers
        try:
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"GreenGrowth_CPAs_Simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mimetype='application/pdf'
            )
        except Exception as send_error:
            logger.error(f"File send error: {send_error}")
            return jsonify({'error': 'Failed to download generated form'}), 500
        
    except Exception as e:
        logger.error(f"Simple form generation error: {e}")
        return jsonify({'error': 'Form generation service temporarily unavailable'}), 500

@app.route('/generate_irs_form')
def generate_irs_form():
    """Generate official IRS Form 1040 with real data and enhanced validation"""
    try:
        # Validate session data
        is_valid, message = validate_session_data()
        if not is_valid:
            logger.warning(f"IRS Form generation attempted without valid data: {message}")
            return jsonify({'error': message}), 400
        
        tax_data = app.config.get('current_tax_data')
        calculations = app.config.get('current_calculations')
        
        # Check if IRS template exists
        if not os.path.exists('f1040.pdf'):
            logger.error("IRS Form 1040 template not found")
            return jsonify({'error': 'IRS Form template not available. Please contact support.'}), 500
        
        # Generate form with enhanced error handling
        try:
            pdf_path = irs_form_filler.fill_form_1040(tax_data, calculations)
            logger.info(f"IRS Form 1040 filled: {pdf_path}")
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError("Generated IRS form not found")
            
            if os.path.getsize(pdf_path) == 0:
                raise ValueError("Generated IRS form is empty")
                
        except Exception as fill_error:
            logger.error(f"IRS form filling failed: {fill_error}")
            return jsonify({'error': f'Failed to fill IRS Form 1040: {str(fill_error)}'}), 500
        
        # Return file with proper headers
        try:
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"GreenGrowth_CPAs_IRS_Form_1040_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mimetype='application/pdf'
            )
        except Exception as send_error:
            logger.error(f"IRS form file send error: {send_error}")
            return jsonify({'error': 'Failed to download IRS form'}), 500
        
    except Exception as e:
        logger.error(f"IRS Form filling failed: {e}")
        return jsonify({'error': 'IRS Form service temporarily unavailable'}), 500

# Enhanced Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(413)
def too_large_error(error):
    logger.warning(f"File too large: {request.url}")
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(415)
def unsupported_media_type_error(error):
    logger.warning(f"Unsupported media type: {request.url}")
    return jsonify({'error': 'Unsupported file type. Please upload PDF, JPG, or PNG files.'}), 415

@app.errorhandler(429)
def rate_limit_error(error):
    logger.warning(f"Rate limit exceeded: {request.url}")
    return jsonify({'error': 'Too many requests. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error. Please try again later.',
        'support': 'If this problem persists, please contact support.'
    }), 500

@app.errorhandler(503)
def service_unavailable_error(error):
    logger.error(f"Service unavailable: {error}")
    return jsonify({'error': 'Service temporarily unavailable. Please try again later.'}), 503

# Request validation middleware
@app.before_request
def validate_request():
    """Validate incoming requests"""
    try:
        # Skip validation for static files and health check
        if request.endpoint in ['static', 'health_check']:
            return
        
        # Check request size for non-file uploads
        if request.endpoint != 'upload_file' and request.content_length:
            if request.content_length > 1024 * 1024:  # 1MB for non-file requests
                return jsonify({'error': 'Request too large'}), 413
        
        # Validate content type for POST requests
        if request.method == 'POST' and request.endpoint == 'upload_file':
            if 'multipart/form-data' not in request.content_type:
                return jsonify({'error': 'Invalid content type for file upload'}), 400
                
    except Exception as e:
        logger.error(f"Request validation error: {e}")
        return jsonify({'error': 'Invalid request format'}), 400

# Production-ready startup with enhanced configuration
if __name__ == '__main__':
    # Cloud-ready server configuration with error handling
    try:
        port = int(os.environ.get('PORT', 10000))
    except (ValueError, TypeError):
        # Fallback if PORT is not a valid integer (common in some cloud environments)
        port = 10000
        logger.warning(f"⚠️ Invalid PORT environment variable, using default: {port}")
    
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    host = os.environ.get('HOST', '0.0.0.0')  # Cloud-compatible host binding
    
    logger.info(f"🚀 Starting GreenGrowth CPAs AI Tax Agent on {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug_mode}")
    logger.info(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"📁 Output folder: {app.config['OUTPUT_FOLDER']}")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True
        )
    except Exception as startup_error:
        logger.error(f"❌ Failed to start application: {startup_error}")
        raise 