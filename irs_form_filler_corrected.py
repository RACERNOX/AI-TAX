#!/usr/bin/env python3

"""CORRECTED IRS Form 1040 PDF Filler - with SECURE PII handling"""

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject
import os
import re
import hashlib
from datetime import datetime

def mask_ssn_for_display(ssn):
    """Securely mask SSN for display and logging with compact format for PDF fields"""
    if not ssn:
        return "***-**-****"
    
    ssn_clean = re.sub(r'[^\d]', '', str(ssn))
    if len(ssn_clean) >= 9:
        # Use compact format: XXX**XXXX (no dashes for PDF field space)
        return f"XXX**{ssn_clean[-4:]}"
    elif len(ssn_clean) >= 4:
        return f"XXX**{ssn_clean[-4:]}"
    else:
        return "XXX**XXXX"

def hash_name_for_logging(name):
    """Hash name for secure logging"""
    if not name:
        return "NONE"
    return hashlib.sha256(str(name).encode()).hexdigest()[:8]

class CorrectedIRSForm1040Filler:
    """Fill the official IRS Form 1040 PDF template with SECURE PII handling"""
    
    def __init__(self, template_path="f1040.pdf"):
        self.template_path = template_path
        self.output_dir = '/tmp/generated'  # Use temp directory for cloud deployment
        os.makedirs(self.output_dir, exist_ok=True)
        
        # CORRECTED field mapping based on verification tests
        self.field_mapping = {
            # Personal Information (FINAL CORRECTED - based on field positions)
            'first_name': 'topmostSubform[0].Page1[0].f1_04[0]',      # Your first name and middle initial (X=36, Y=690)
            'middle_initial': '',  # Combined with first_name field above
            'last_name': 'topmostSubform[0].Page1[0].f1_05[0]',       # Your last name (X=238, Y=690) 
            'ssn': 'topmostSubform[0].Page1[0].f1_06[0]',             # Your SSN (X=469, Y=690)
            'spouse_first': 'topmostSubform[0].Page1[0].f1_07[0]',    # Spouse first name and middle initial (X=36, Y=666)
            'spouse_middle': '',  # Combined with spouse_first field above  
            'spouse_last': 'topmostSubform[0].Page1[0].f1_08[0]',     # Spouse last name (X=238, Y=666)
            'spouse_ssn': 'topmostSubform[0].Page1[0].f1_09[0]',      # Spouse SSN (X=469, Y=666)
            
            # Address fields (from Address_ReadOrder section)
            'address': 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_10[0]',  # Home address
            'city': 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_12[0]',     # City
            'state': 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_13[0]',    # State  
            'zip': 'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_14[0]',      # ZIP
            
            # Filing status checkboxes (verified working)
            'filing_single': 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]',
            'filing_married_joint': 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]',
            'filing_married_separate': 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]',
            
            # Income section (verified field sequence)
            'wages_1a': 'topmostSubform[0].Page1[0].f1_32[0]',        # Line 1a: W-2 wages ✅
            'household_wages_1b': 'topmostSubform[0].Page1[0].f1_33[0]', # Line 1b: Household wages
            'tip_income_1c': 'topmostSubform[0].Page1[0].f1_34[0]',   # Line 1c: Tip income
            'medicaid_waiver_1d': 'topmostSubform[0].Page1[0].f1_35[0]', # Line 1d: Medicaid waiver
            'dependent_care_1e': 'topmostSubform[0].Page1[0].f1_36[0]', # Line 1e: Dependent care
            'adoption_benefits_1f': 'topmostSubform[0].Page1[0].f1_37[0]', # Line 1f: Adoption benefits
            'form8919_wages_1g': 'topmostSubform[0].Page1[0].f1_38[0]', # Line 1g: Form 8919 wages
            'other_earned_1h': 'topmostSubform[0].Page1[0].f1_39[0]',  # Line 1h: Other earned income
            'nontaxable_combat_1i': 'topmostSubform[0].Page1[0].f1_40[0]', # Line 1i: Combat pay
            'total_wages_1z': 'topmostSubform[0].Page1[0].f1_41[0]',   # Line 1z: Total wages ✅
            
            # Interest and dividends
            'tax_exempt_interest_2a': 'topmostSubform[0].Page1[0].f1_42[0]', # Line 2a: Tax-exempt interest
            'taxable_interest_2b': 'topmostSubform[0].Page1[0].f1_43[0]',    # Line 2b: Taxable interest ✅
            
            # More income lines 
            'qualified_dividends_3a': 'topmostSubform[0].Page1[0].f1_44[0]', # Line 3a: Qualified dividends
            'ordinary_dividends_3b': 'topmostSubform[0].Page1[0].f1_45[0]',  # Line 3b: Ordinary dividends
            
            # Retirement distributions
            'ira_distributions_4a': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_46[0]', # Line 4a: IRA distributions
            'ira_taxable_4b': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_47[0]',       # Line 4b: IRA taxable
            'pensions_5a': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_48[0]',          # Line 5a: Pensions
            'pensions_taxable_5b': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_49[0]',  # Line 5b: Pensions taxable
            'social_security_6a': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_50[0]',   # Line 6a: Social Security
            'social_security_taxable_6b': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_51[0]', # Line 6b: SS taxable
            
            # Capital gains and other income
            'capital_gains_7': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_52[0]',      # Line 7: Capital gains
            'schedule1_income_8': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_53[0]',   # Line 8: Schedule 1 income
            'total_income_9': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_54[0]',       # Line 9: Total income ✅
            'schedule1_adjustments_10': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_55[0]', # Line 10: Adjustments
            'agi_11': 'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_56[0]',               # Line 11: AGI ✅
            
            # Deductions
            'standard_deduction_12': 'topmostSubform[0].Page1[0].f1_57[0]',  # Line 12: Standard deduction ✅
            'qbi_deduction_13': 'topmostSubform[0].Page1[0].f1_58[0]',       # Line 13: QBI deduction
            'total_deductions_14': 'topmostSubform[0].Page1[0].f1_59[0]',    # Line 14: Total deductions
            'taxable_income_15': 'topmostSubform[0].Page1[0].f1_60[0]',      # Line 15: Taxable income ✅
            
            # Page 2 - Tax and Credits (verified working)
            'tax_16': 'topmostSubform[0].Page2[0].f2_01[0]',          # Line 16: Tax ✅
            'schedule2_tax_17': 'topmostSubform[0].Page2[0].f2_02[0]', # Line 17: Schedule 2 tax
            'total_tax_18': 'topmostSubform[0].Page2[0].f2_03[0]',    # Line 18: Total tax before credits
            'child_tax_credit_19': 'topmostSubform[0].Page2[0].f2_04[0]', # Line 19: Child tax credit
            'schedule3_credits_20': 'topmostSubform[0].Page2[0].f2_05[0]', # Line 20: Schedule 3 credits
            'total_credits_21': 'topmostSubform[0].Page2[0].f2_06[0]', # Line 21: Total credits
            'tax_after_credits_22': 'topmostSubform[0].Page2[0].f2_07[0]', # Line 22: Tax after credits
            'schedule2_other_tax_23': 'topmostSubform[0].Page2[0].f2_08[0]', # Line 23: Other tax
            'total_tax_24': 'topmostSubform[0].Page2[0].f2_09[0]',    # Line 24: Total tax ✅
            
            # Payments
            'fed_withholding_25a': 'topmostSubform[0].Page2[0].f2_10[0]', # Line 25a: Federal tax withheld ✅
            'fed_withholding_1099_25b': 'topmostSubform[0].Page2[0].f2_11[0]', # Line 25b: 1099 withholding
            'fed_withholding_other_25c': 'topmostSubform[0].Page2[0].f2_12[0]', # Line 25c: Other withholding
            'fed_withholding_total_25d': 'topmostSubform[0].Page2[0].f2_13[0]', # Line 25d: Total withholding
            'estimated_payments_26': 'topmostSubform[0].Page2[0].f2_14[0]',     # Line 26: Estimated payments
            'eic_27': 'topmostSubform[0].Page2[0].f2_15[0]',                    # Line 27: EIC
            'additional_child_credit_28': 'topmostSubform[0].Page2[0].f2_16[0]', # Line 28: Additional child credit
            'american_opportunity_29': 'topmostSubform[0].Page2[0].f2_17[0]',   # Line 29: American Opportunity Credit
            'reserved_30': 'topmostSubform[0].Page2[0].f2_18[0]',               # Line 30: Reserved
            'schedule3_payments_31': 'topmostSubform[0].Page2[0].f2_19[0]',     # Line 31: Schedule 3 payments
            'total_other_payments_32': 'topmostSubform[0].Page2[0].f2_20[0]',   # Line 32: Total other payments
            'total_payments_33': 'topmostSubform[0].Page2[0].f2_21[0]',         # Line 33: Total payments ✅
            
            # Refund or amount owed
            'refund_34': 'topmostSubform[0].Page2[0].f2_22[0]',       # Line 34: Refund ✅
            'refund_amount_35a': 'topmostSubform[0].Page2[0].f2_23[0]', # Line 35a: Refund amount
            'routing_number': 'topmostSubform[0].Page2[0].RoutingNo[0].f2_25[0]', # Routing number
            'account_number': 'topmostSubform[0].Page2[0].AccountNo[0].f2_26[0]', # Account number
            'apply_to_next_year_36': 'topmostSubform[0].Page2[0].f2_27[0]',     # Line 36: Apply to next year
            'amount_owed_37': 'topmostSubform[0].Page2[0].f2_28[0]',            # Line 37: Amount owed ✅
            'estimated_penalty_38': 'topmostSubform[0].Page2[0].f2_29[0]',      # Line 38: Estimated penalty
        }
    
    def format_ssn_for_form(self, ssn):
        """Format SSN to fit properly in IRS form boxes without overflow"""
        if not ssn:
            return ""
        
        ssn_str = str(ssn).strip()
        
        # Handle masked SSNs like "XXX-XX-5005" - remove all separators for maximum compactness
        if 'X' in ssn_str.upper():
            # For masked SSNs, remove all dashes and spaces to save maximum space
            formatted = ssn_str.replace('-', '').replace(' ', '')
        else:
            # For full numeric SSNs, extract digits and use compact format
            digits_only = ''.join(filter(str.isdigit, ssn_str))
            if len(digits_only) >= 9:
                # Compact format: XXX-XXXXXX (10 chars instead of 11)
                formatted = f"{digits_only[:3]}-{digits_only[3:9]}"
            else:
                # Fallback to original with dash-to-space replacement
                formatted = ssn_str.replace('-', ' ')
        
        return formatted
    
    def set_need_appearances(self, writer):
        """Force PDF viewers to render the new text immediately"""
        try:
            catalog = writer._root_object
            if "/AcroForm" not in catalog:
                catalog["/AcroForm"] = writer._add_object({})
            catalog["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
        except Exception as e:
            print(f"Warning: Could not set NeedAppearances: {e}")
    
    def fill_form_1040(self, tax_data, calculations):
        """Fill the official IRS Form 1040 with CORRECTED field mappings"""
        
        try:
            # Create output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"IRS_Form_1040_CORRECTED_{timestamp}.pdf"
            output_path = os.path.join(self.output_dir, filename)
            
            # Load the official template
            reader = PdfReader(self.template_path)
            writer = PdfWriter()
            
            # Copy all pages from template
            writer.append(reader)
            
            # Extract and format data
            taxpayer_name = str(tax_data.get('taxpayer_name', '')).strip().upper()
            name_parts = taxpayer_name.split() if taxpayer_name else ['', '']
            
            # IRS form has "first name and middle initial" as one field
            if len(name_parts) >= 3:
                # Format: "FIRST MIDDLE LAST" -> "FIRST MIDDLE" + "LAST"
                first_and_middle = f"{name_parts[0]} {name_parts[1]}"
                last_name = ' '.join(name_parts[2:])
            elif len(name_parts) == 2:
                # Format: "FIRST LAST" -> "FIRST" + "LAST"  
                first_and_middle = name_parts[0]
                last_name = name_parts[1]
            else:
                # Single name or empty
                first_and_middle = name_parts[0] if name_parts else ''
                last_name = ''
            
            # Format SSN properly for IRS form boxes
            raw_ssn = str(tax_data.get('ssn', '')).strip()
            formatted_ssn = self.format_ssn_for_form(raw_ssn)
            
            # ✅ SECURITY: Create masked SSN for PDF form (only last 4 digits visible)
            masked_ssn_for_form = mask_ssn_for_display(raw_ssn)
            
            # Extract address information
            address = str(tax_data.get('address', '')).strip()
            city = str(tax_data.get('city', '')).strip()
            state = str(tax_data.get('state', '')).strip().upper()
            zip_code = str(tax_data.get('zip_code', '')).strip()
            
            filing_status = str(tax_data.get('filing_status', 'single')).lower()
            
            # Format monetary values
            wages = float(tax_data.get('wages', 0))
            interest_income = float(tax_data.get('interest_income', 0))
            federal_withholding = float(tax_data.get('federal_withholding', 0))
            
            total_income = float(calculations.get('total_income', 0))
            standard_deduction = float(calculations.get('standard_deduction', 0))
            taxable_income = float(calculations.get('taxable_income', 0))
            federal_tax = float(calculations.get('federal_tax', 0))
            refund_or_owed = float(calculations.get('refund_or_owed', 0))
            is_refund = bool(calculations.get('is_refund', False))
            
            # Prepare CORRECTED field values for the PDF
            field_values = {
                # Personal Information (FINAL CORRECTED)
                self.field_mapping['first_name']: first_and_middle,
                self.field_mapping['last_name']: last_name,
                # ✅ SECURITY: Use masked SSN in PDF form for PII protection
                self.field_mapping['ssn']: (masked_ssn_for_form, "/Helv", 6),  # ✅ SECURE: Masked SSN with smaller font
                
                # Address Information (NEW)
                self.field_mapping['address']: address,
                self.field_mapping['city']: city,
                self.field_mapping['state']: state,
                self.field_mapping['zip']: zip_code,
                
                # Income fields (CORRECTED mappings)
                self.field_mapping['wages_1a']: f"{wages:.2f}",                    # Line 1a ✅
                self.field_mapping['total_wages_1z']: f"{wages:.2f}",              # Line 1z ✅
                self.field_mapping['taxable_interest_2b']: f"{interest_income:.2f}", # Line 2b ✅
                self.field_mapping['total_income_9']: f"{total_income:.2f}",       # Line 9 ✅
                self.field_mapping['agi_11']: f"{total_income:.2f}",               # Line 11 ✅ CORRECTED
                self.field_mapping['standard_deduction_12']: f"{standard_deduction:.2f}", # Line 12 ✅
                self.field_mapping['taxable_income_15']: f"{taxable_income:.2f}",  # Line 15 ✅
                
                # Tax and Payment fields (CORRECTED)
                self.field_mapping['tax_16']: f"{federal_tax:.2f}",                # Line 16 ✅
                self.field_mapping['total_tax_24']: f"{federal_tax:.2f}",          # Line 24 ✅
                self.field_mapping['fed_withholding_25a']: f"{federal_withholding:.2f}", # Line 25a ✅
                self.field_mapping['fed_withholding_total_25d']: f"{federal_withholding:.2f}", # Line 25d ✅
                self.field_mapping['total_payments_33']: f"{federal_withholding:.2f}", # Line 33 ✅
            }
            
            # Set filing status checkbox (verified)
            if filing_status == 'single':
                field_values[self.field_mapping['filing_single']] = "/Yes"
            elif filing_status in ['married_filing_jointly', 'married filing jointly']:
                field_values[self.field_mapping['filing_married_joint']] = "/Yes"
            elif filing_status in ['married_filing_separately', 'married filing separately']:
                field_values[self.field_mapping['filing_married_separate']] = "/Yes"
            else:
                field_values[self.field_mapping['filing_single']] = "/Yes"
            
            # Set refund or amount owed (CORRECTED)
            if is_refund and refund_or_owed > 0:
                field_values[self.field_mapping['refund_34']] = f"{refund_or_owed:.2f}"
                field_values[self.field_mapping['refund_amount_35a']] = f"{refund_or_owed:.2f}"
            elif refund_or_owed < 0:
                field_values[self.field_mapping['amount_owed_37']] = f"{abs(refund_or_owed):.2f}"
            
            # Fill both pages with field values
            try:
                writer.update_page_form_field_values(
                    writer.pages[0], 
                    field_values, 
                    auto_regenerate=False
                )
                writer.update_page_form_field_values(
                    writer.pages[1], 
                    field_values, 
                    auto_regenerate=False
                )
            except Exception as e:
                print(f"Warning: Field update issue: {e}")
            
            # Set the NeedAppearances flag
            self.set_need_appearances(writer)
            
            # Save the filled PDF
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            # SECURE: Console output with PII protection
            print(f"✅ SECURE IRS Form 1040 filled successfully!")
            print(f"📄 Output: {output_path}")
            print(f"📊 SECURE Data Mapping:")
            print(f"   Name Hash: {hash_name_for_logging(first_and_middle + ' ' + last_name)}")
            print(f"   SSN (Form): {masked_ssn_for_form}")  # ✅ SECURE: Shows what's actually in the PDF
            print(f"   Address: {address}")
            print(f"   City: {city}")
            print(f"   State: {state}")
            print(f"   ZIP: {zip_code}")
            print(f"   Line 1a Wages: ${wages:,.2f}")
            print(f"   Line 1z Total Wages: ${wages:,.2f}")
            print(f"   Line 2b Interest: ${interest_income:,.2f}")
            print(f"   Line 9 Total Income: ${total_income:,.2f}")
            print(f"   Line 11 AGI: ${total_income:,.2f}")
            print(f"   Line 12 Standard Deduction: ${standard_deduction:,.2f}")
            print(f"   Line 15 Taxable Income: ${taxable_income:,.2f}")
            print(f"   Line 16 Tax: ${federal_tax:,.2f}")
            print(f"   Line 24 Total Tax: ${federal_tax:,.2f}")
            print(f"   Line 25a Withholding: ${federal_withholding:,.2f}")
            print(f"   Line 33 Total Payments: ${federal_withholding:,.2f}")
            if is_refund:
                print(f"   Line 34 💰 REFUND: ${refund_or_owed:,.2f}")
            else:
                print(f"   Line 37 💸 OWED: ${abs(refund_or_owed):,.2f}")
            
            # ✅ SECURITY NOTE: SSN is masked in both logs AND the actual PDF form
            print(f"🔒 SECURITY: SSN masked in PDF form (XXX**XXXX format) for PII protection")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error filling SECURE Form 1040: {e}")
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise Exception(f"SECURE form filling failed: {str(e)}")

# Test function
def test_corrected_filler():
    """Test the corrected IRS form filler"""
    from tax_calculator import TaxCalculator
    
    print("🧪 Testing CORRECTED IRS Form Filler...")
    
    # Sample data (user's real W-2 data with address)
    test_tax_data = {
        'taxpayer_name': 'SHUBHAM S SOLANKI',
        'ssn': 'XXX-XX-5005',
        'filing_status': 'single',
        'wages': 5207.78,
        'federal_withholding': 55.12,
        'interest_income': 0,
        'other_income': 0,
        'document_type': 'W-2',
        # Address information
        'address': '123 MAIN STREET APT 5B',
        'city': 'SAN FRANCISCO',
        'state': 'CA',
        'zip_code': '94102'
    }
    
    # Calculate taxes
    calc = TaxCalculator()
    calculations = calc.calculate_taxes(test_tax_data)
    
    # Fill the form with CORRECTED mappings
    filler = CorrectedIRSForm1040Filler()
    output_path = filler.fill_form_1040(test_tax_data, calculations)
    
    return output_path

if __name__ == '__main__':
    test_corrected_filler() 