import logging

logger = logging.getLogger(__name__)

class TaxCalculator:
    """Simple tax calculator for 2024 tax year with enhanced error handling"""
    
    def __init__(self):
        # 2024 Tax Brackets for Single filers
        self.tax_brackets_single = [
            (11000, 0.10),    # 10% on income up to $11,000
            (44725, 0.12),    # 12% on income $11,001 to $44,725
            (95375, 0.22),    # 22% on income $44,726 to $95,375
            (182050, 0.24),   # 24% on income $95,376 to $182,050
            (231250, 0.32),   # 32% on income $182,051 to $231,250
            (578125, 0.35),   # 35% on income $231,251 to $578,125
            (float('inf'), 0.37)  # 37% on income over $578,125
        ]
        
        # 2024 Standard Deductions
        self.standard_deductions = {
            'single': 14600,
            'married_filing_jointly': 29200,
            'married_filing_separately': 14600,
            'head_of_household': 21900
        }
    
    def validate_tax_data(self, tax_data):
        """Validate tax data input with comprehensive checks"""
        if not tax_data:
            raise ValueError("Tax data cannot be empty")
        
        if not isinstance(tax_data, dict):
            raise ValueError("Tax data must be a dictionary")
        
        # Validate monetary fields
        monetary_fields = ['wages', 'interest_income', 'other_income', 'federal_withholding']
        for field in monetary_fields:
            value = tax_data.get(field, 0)
            try:
                float_value = float(value)
                if float_value < 0:
                    logger.warning(f"Negative value for {field}: {float_value}, setting to 0")
                    tax_data[field] = 0
                elif float_value > 50000000:  # $50M sanity check
                    raise ValueError(f"Unreasonably high value for {field}: ${float_value:,.2f}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid {field} value: {value}, setting to 0")
                tax_data[field] = 0
        
        # Validate filing status
        filing_status = tax_data.get('filing_status', 'single').lower()
        if filing_status not in self.standard_deductions:
            logger.warning(f"Invalid filing status: {filing_status}, defaulting to single")
            tax_data['filing_status'] = 'single'
        
        return tax_data
    
    def calculate_taxes(self, tax_data):
        """Calculate federal income tax based on tax data with enhanced error handling"""
        try:
            # Validate input data
            tax_data = self.validate_tax_data(tax_data)
            
            # Extract and validate values
            wages = float(tax_data.get('wages', 0))
            interest_income = float(tax_data.get('interest_income', 0))
            other_income = float(tax_data.get('other_income', 0))
            federal_withholding = float(tax_data.get('federal_withholding', 0))
            filing_status = tax_data.get('filing_status', 'single').lower()
            
            # Calculate total income
            total_income = wages + interest_income + other_income
            
            # Validate total income is reasonable
            if total_income < 0:
                logger.warning("Negative total income calculated, setting to 0")
                total_income = 0
            
            # Get standard deduction
            standard_deduction = self.standard_deductions.get(filing_status, 14600)
            
            # Calculate taxable income
            taxable_income = max(0, total_income - standard_deduction)
            
            # Calculate federal tax owed
            federal_tax = self.calculate_federal_tax(taxable_income)
            
            # Calculate refund or amount owed
            refund_or_owed = federal_withholding - federal_tax
            
            # SECURE: Log calculation summary without detailed income data
            logger.info(f"✅ Tax calculation completed securely: Files processed, calculations successful")
            
            return {
                'total_income': round(total_income, 2),
                'standard_deduction': round(standard_deduction, 2),
                'taxable_income': round(taxable_income, 2),
                'federal_tax': round(federal_tax, 2),
                'federal_withholding': round(federal_withholding, 2),
                'refund_or_owed': round(refund_or_owed, 2),
                'is_refund': refund_or_owed > 0,
                'filing_status': filing_status,
                'calculation_success': True
            }
            
        except ValueError as ve:
            logger.error(f"Tax calculation validation error: {ve}")
            return {
                'error': f"Tax calculation validation error: {str(ve)}",
                'total_income': 0,
                'standard_deduction': 14600,
                'taxable_income': 0,
                'federal_tax': 0,
                'federal_withholding': 0,
                'refund_or_owed': 0,
                'is_refund': False,
                'filing_status': 'single',
                'calculation_success': False
            }
        except Exception as e:
            logger.error(f"Tax calculation unexpected error: {e}")
            return {
                'error': f"Tax calculation error: {str(e)}",
                'total_income': 0,
                'standard_deduction': 14600,
                'taxable_income': 0,
                'federal_tax': 0,
                'federal_withholding': 0,
                'refund_or_owed': 0,
                'is_refund': False,
                'filing_status': 'single',
                'calculation_success': False
            }
    
    def calculate_federal_tax(self, taxable_income):
        """Calculate federal tax using 2024 brackets for single filers with validation"""
        try:
            if taxable_income <= 0:
                return 0.0
            
            # Validate input
            if not isinstance(taxable_income, (int, float)):
                raise ValueError(f"Invalid taxable income type: {type(taxable_income)}")
            
            if taxable_income > 100000000:  # $100M sanity check
                raise ValueError(f"Unreasonably high taxable income: ${taxable_income:,.2f}")
            
            total_tax = 0.0
            previous_bracket = 0
            
            for bracket_limit, rate in self.tax_brackets_single:
                if taxable_income <= previous_bracket:
                    break
                    
                taxable_in_bracket = min(taxable_income, bracket_limit) - previous_bracket
                bracket_tax = taxable_in_bracket * rate
                total_tax += bracket_tax
                
                logger.debug(f"Bracket: ${previous_bracket:,.2f}-${bracket_limit:,.2f} @ {rate*100}%: ${bracket_tax:,.2f}")
                
                if taxable_income <= bracket_limit:
                    break
                    
                previous_bracket = bracket_limit
            
            return round(total_tax, 2)
            
        except Exception as e:
            logger.error(f"Federal tax calculation error: {e}")
            return 0.0 