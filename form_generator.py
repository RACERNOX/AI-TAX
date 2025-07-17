from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from datetime import datetime

class Form1040Generator:
    """Simple Form 1040 PDF generator (cloud-compatible)"""
    
    def __init__(self):
        self.output_dir = '/tmp/generated'  # Use temp directory for cloud deployment
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_form_1040(self, tax_data, calculations):
        """Generate a simplified Form 1040 PDF"""
        
        # Validate input data
        if not isinstance(tax_data, dict) or not isinstance(calculations, dict):
            raise ValueError("Invalid input data for form generation")
        
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Form_1040_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF with error handling
            c = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter
            
            # Safe data access with defaults
            taxpayer_name = str(tax_data.get('taxpayer_name', 'Not provided'))
            ssn = str(tax_data.get('ssn', 'Not provided'))
            filing_status = str(tax_data.get('filing_status', 'Single')).title()
            wages = float(tax_data.get('wages', 0))
            interest_income = float(tax_data.get('interest_income', 0))
            other_income = float(tax_data.get('other_income', 0))
            federal_withholding = float(tax_data.get('federal_withholding', 0))
            
            total_income = float(calculations.get('total_income', 0))
            standard_deduction = float(calculations.get('standard_deduction', 0))
            taxable_income = float(calculations.get('taxable_income', 0))
            federal_tax = float(calculations.get('federal_tax', 0))
            refund_or_owed = float(calculations.get('refund_or_owed', 0))
            is_refund = bool(calculations.get('is_refund', False))
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 50, "Form 1040 - U.S. Individual Income Tax Return")
            c.drawString(100, height - 70, "2024 Tax Year - AI Generated")
            
            # Taxpayer Information
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 120, "Taxpayer Information:")
            c.setFont("Helvetica", 10)
            
            y_pos = height - 140
            c.drawString(70, y_pos, f"Name: {taxpayer_name}")
            y_pos -= 20
            c.drawString(70, y_pos, f"SSN: {ssn}")
            y_pos -= 20
            c.drawString(70, y_pos, f"Filing Status: {filing_status}")
            
            # Income Section
            y_pos -= 40
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Income:")
            c.setFont("Helvetica", 10)
            
            y_pos -= 20
            c.drawString(70, y_pos, f"Wages (W-2): ${wages:,.2f}")
            y_pos -= 15
            c.drawString(70, y_pos, f"Interest Income: ${interest_income:,.2f}")
            y_pos -= 15
            c.drawString(70, y_pos, f"Other Income: ${other_income:,.2f}")
            y_pos -= 15
            c.setFont("Helvetica-Bold", 10)
            c.drawString(70, y_pos, f"Total Income: ${total_income:,.2f}")
            
            # Deductions
            y_pos -= 30
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Deductions:")
            c.setFont("Helvetica", 10)
            
            y_pos -= 20
            c.drawString(70, y_pos, f"Standard Deduction: ${standard_deduction:,.2f}")
            y_pos -= 15
            c.setFont("Helvetica-Bold", 10)
            c.drawString(70, y_pos, f"Taxable Income: ${taxable_income:,.2f}")
            
            # Tax Calculation
            y_pos -= 30
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Tax Calculation:")
            c.setFont("Helvetica", 10)
            
            y_pos -= 20
            c.drawString(70, y_pos, f"Federal Tax Owed: ${federal_tax:,.2f}")
            y_pos -= 15
            c.drawString(70, y_pos, f"Federal Tax Withheld: ${federal_withholding:,.2f}")
            
            # Refund or Amount Owed
            y_pos -= 30
            if is_refund and refund_or_owed > 0:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos, f"REFUND DUE: ${refund_or_owed:,.2f}")
            elif refund_or_owed < 0:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos, f"AMOUNT OWED: ${abs(refund_or_owed):,.2f}")
            else:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos, "NO REFUND OR AMOUNT OWED")
            
            # Footer
            c.setFont("Helvetica", 8)
            c.drawString(50, 50, "This is a simplified form generated by AI for demonstration purposes only.")
            c.drawString(50, 40, "Please consult a tax professional for actual tax filing.")
            c.drawString(50, 30, f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
            
            # Save PDF
            c.save()
            
            return filepath
            
        except Exception as e:
            # Clean up any partial file
            if 'filepath' in locals() and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            raise Exception(f"PDF generation failed: {str(e)}") 