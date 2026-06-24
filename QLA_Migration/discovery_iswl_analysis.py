"""
ISWL Source Data Discovery Tool
Discovery-only script for analyzing LifePRO extracts to locate ISWL-related rate and value data.
NOT FOR PRODUCTION USE - Analysis only.
"""

import pandas as pd
import os
from pathlib import Path
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DIR = PROJECT_ROOT / "QLA_Migration" / "Source"
RATE_SOURCE_DIR = PROJECT_ROOT / "plan_analysis" / "source_data" / "rates"
PFSA_RATES_DIR = PROJECT_ROOT / "PFSA Rates"

class ISWLDiscoveryAnalyzer:
    def __init__(self):
        self.findings = {
            'files_reviewed': [],
            'iswl_plans_found': set(),
            'interest_candidates': [],
            'coi_candidates': [],
            'gcoi_candidates': [],
            'surrender_candidates': [],
            'premium_candidates': [],
            'cash_value_candidates': [],
            'expense_candidates': [],
            'dimensional_analysis': {},
            'structural_issues': []
        }
        
    def analyze_rate_table_extract(self, filepath):
        """Analyze Rate_Table_Extract for ISWL data"""
        print(f"\nAnalyzing: {filepath}")
        self.findings['files_reviewed'].append(str(filepath))
        
        try:
            # Read first chunk to understand structure
            df = pd.read_csv(filepath, nrows=50000)
            
            print(f"  Columns: {list(df.columns)}")
            print(f"  Total sample rows: {len(df)}")
            
            # Analyze TYPE_CODE values
            if 'TYPE_CODE' in df.columns:
                type_codes = df['TYPE_CODE'].value_counts()
                print(f"  TYPE_CODE values found: {dict(type_codes)}")
                
                # Look for specific code types
                if 'CV' in type_codes.index:
                    self.findings['cash_value_candidates'].append({
                        'file': str(filepath),
                        'type_code': 'CV',
                        'count': int(type_codes['CV']),
                        'fields': list(df.columns),
                        'dimensions': self._analyze_dimensions(df[df['TYPE_CODE'] == 'CV'])
                    })
                    
                if 'COI' in type_codes.index or 'CI' in type_codes.index:
                    self.findings['coi_candidates'].append({
                        'file': str(filepath),
                        'type_code': 'COI' if 'COI' in type_codes.index else 'CI',
                        'count': int(type_codes.get('COI', type_codes.get('CI', 0))),
                        'fields': list(df.columns),
                        'dimensions': self._analyze_dimensions(df[df['TYPE_CODE'].isin(['COI', 'CI'])])
                    })
                    
                if 'SC' in type_codes.index or 'SUR' in type_codes.index:
                    self.findings['surrender_candidates'].append({
                        'file': str(filepath),
                        'type_code': 'SC' if 'SC' in type_codes.index else 'SUR',
                        'count': int(type_codes.get('SC', type_codes.get('SUR', 0))),
                        'fields': list(df.columns),
                        'dimensions': self._analyze_dimensions(df[df['TYPE_CODE'].isin(['SC', 'SUR'])])
                    })
                    
                if 'PR' in type_codes.index or 'GP' in type_codes.index:
                    self.findings['premium_candidates'].append({
                        'file': str(filepath),
                        'type_code': 'PR' if 'PR' in type_codes.index else 'GP',
                        'count': int(type_codes.get('PR', type_codes.get('GP', 0))),
                        'fields': list(df.columns),
                        'dimensions': self._analyze_dimensions(df[df['TYPE_CODE'].isin(['PR', 'GP'])])
                    })
            
            # Look for ISWL plan codes
            if 'COVERAGE_ID' in df.columns:
                plans = df['COVERAGE_ID'].unique()
                iswl_keywords = ['ISWL', 'ISW', 'WL', 'WHOLE']
                for plan in plans:
                    plan_str = str(plan).upper()
                    if any(kw in plan_str for kw in iswl_keywords):
                        self.findings['iswl_plans_found'].add(plan_str)
                        print(f"  Potential ISWL plan found: {plan_str}")
                        
            return True
            
        except Exception as e:
            print(f"  Error analyzing {filepath}: {e}")
            return False
    
    def analyze_attained_age_rates(self, filepath):
        """Analyze PAAGERAT extract"""
        print(f"\nAnalyzing: {filepath}")
        self.findings['files_reviewed'].append(str(filepath))
        
        try:
            df = pd.read_csv(filepath, nrows=50000)
            
            print(f"  Columns: {list(df.columns)}")
            print(f"  Sample rows: {len(df)}")
            
            if 'TYPE_CODE' in df.columns:
                type_codes = df['TYPE_CODE'].value_counts()
                print(f"  TYPE_CODE values: {dict(type_codes)}")
                
            # Analyze structure
            if 'COVERAGE_ID' in df.columns:
                plans = df['COVERAGE_ID'].unique()[:20]
                print(f"  Sample plan codes: {list(plans)}")
                
            return True
            
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def analyze_iswl_premium_file(self, filepath):
        """Analyze iswl-prem.csv file"""
        print(f"\nAnalyzing: {filepath}")
        self.findings['files_reviewed'].append(str(filepath))
        
        try:
            # This appears to be a custom format - read as text first
            with open(filepath, 'r') as f:
                lines = f.readlines()[:20]
                
            print(f"  File format: Custom premium table")
            print(f"  Sample lines:")
            for line in lines[:5]:
                print(f"    {line.strip()[:100]}")
                
            # Try to parse structure
            if lines:
                # First line might be header with ages
                header = lines[0].strip()
                if 'MSP' in header or 'B' in header:
                    print(f"  Appears to be modal premium table with age/duration dimensions")
                    self.findings['premium_candidates'].append({
                        'file': str(filepath),
                        'format': 'Custom modal premium table',
                        'dimensions': 'age x duration matrix format'
                    })
                    
            return True
            
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def _analyze_dimensions(self, df):
        """Analyze dimensional structure of rate data"""
        dims = {}
        
        dimensional_fields = ['AGE', 'SEX', 'BAND', 'UNDERWRITING_CLASS', 'UWCLS', 
                              'DURATION', 'COVERAGE_ID', 'TYPE_CODE']
        
        for field in dimensional_fields:
            if field in df.columns:
                unique_vals = df[field].nunique()
                if unique_vals < 50:  # Only show if reasonable number
                    sample_vals = sorted(df[field].unique())[:10]
                    dims[field] = {
                        'unique_count': int(unique_vals),
                        'sample_values': [str(v) for v in sample_vals]
                    }
                else:
                    dims[field] = {
                        'unique_count': int(unique_vals),
                        'range': f"{df[field].min()} to {df[field].max()}"
                    }
                    
        return dims
    
    def search_for_interest_rates(self):
        """Search for interest rate data in various sources"""
        print("\n" + "="*80)
        print("SEARCHING FOR INTEREST RATE DATA")
        print("="*80)
        
        # Check for interest-related files
        interest_files = [
            SOURCE_DIR / "PINTE_InterestRates_Extract_*.csv",
            SOURCE_DIR / "PRATE_RateInfo_Extract_*.csv"
        ]
        
        # Also check existing extracts for interest fields
        existing_extracts = [
            SOURCE_DIR / "PPBEN_PolicyBenefit_Extract_20260403.csv",
            SOURCE_DIR / "PPOLC_PolicyMaster_Extract_20260403.csv"
        ]
        
        for pattern in existing_extracts:
            if pattern.exists():
                print(f"\nChecking {pattern.name} for interest-related fields...")
                try:
                    df = pd.read_csv(pattern, nrows=1)
                    interest_cols = [col for col in df.columns if 'INT' in col.upper() or 'RATE' in col.upper()]
                    if interest_cols:
                        print(f"  Found potential interest fields: {interest_cols}")
                        self.findings['interest_candidates'].append({
                            'file': str(pattern),
                            'fields': interest_cols
                        })
                except Exception as e:
                    print(f"  Could not read: {e}")
    
    def check_structural_uniformity(self):
        """Check if dimensional structures match across rate tables"""
        print("\n" + "="*80)
        print("STRUCTURAL UNIFORMITY ANALYSIS")
        print("="*80)
        
        rate_types = {
            'COI': self.findings['coi_candidates'],
            'GCOI': self.findings['gcoi_candidates'],
            'Surrender': self.findings['surrender_candidates'],
            'Premium': self.findings['premium_candidates'],
            'Cash Value': self.findings['cash_value_candidates']
        }
        
        # Compare dimensions across rate types
        for rate_type, candidates in rate_types.items():
            if candidates:
                print(f"\n{rate_type}:")
                for candidate in candidates:
                    if 'dimensions' in candidate:
                        dims = candidate['dimensions']
                        if isinstance(dims, dict):
                            dim_summary = ', '.join([f"{k}({v['unique_count']})" for k, v in dims.items()])
                            print(f"  {candidate.get('file', 'unknown')}: {dim_summary}")
                        else:
                            print(f"  {candidate.get('file', 'unknown')}: {dims}")
        
        # Identify mismatches
        # (Would need multiple files to compare - will note in report if insufficient data)
        if len([c for candidates in rate_types.values() for c in candidates]) < 2:
            self.findings['structural_issues'].append(
                "Insufficient rate table variety found for structural comparison"
            )
    
    def generate_report(self, output_path):
        """Generate markdown discovery report"""
        print(f"\n\nGenerating report: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# ISWL Source Data Discovery Report\n\n")
            f.write("**Analysis Date:** 2026-06-23\n\n")
            f.write("**Purpose:** Locate LifePRO source data for configuring QLAdmin ISWL plans\n\n")
            
            # Executive Summary
            f.write("## A. Executive Summary\n\n")
            f.write(f"**Files Reviewed:** {len(self.findings['files_reviewed'])}\n\n")
            f.write(f"**ISWL Plans Identified:** {len(self.findings['iswl_plans_found'])}\n\n")
            
            found_counts = {
                'Interest Values': len(self.findings['interest_candidates']),
                'COI Factors': len(self.findings['coi_candidates']),
                'Guaranteed COI': len(self.findings['gcoi_candidates']),
                'Surrender Charges': len(self.findings['surrender_candidates']),
                'Gross Premiums': len(self.findings['premium_candidates']),
                'Cash Values': len(self.findings['cash_value_candidates']),
                'Expenses': len(self.findings['expense_candidates'])
            }
            
            f.write("### Data Found:\n\n")
            for item, count in found_counts.items():
                status = "✓ Found" if count > 0 else "✗ Not Found"
                f.write(f"- {item}: {status} ({count} candidate sources)\n")
            
            f.write("\n### Assessment:\n\n")
            if sum(found_counts.values()) >= 4:
                f.write("**Partial coverage** - Some rate data located but gaps remain.\n\n")
            elif sum(found_counts.values()) >= 2:
                f.write("**Limited coverage** - Significant data gaps identified.\n\n")
            else:
                f.write("**Insufficient data** - Critical rate tables not found in available extracts.\n\n")
            
            # Source-to-Target Mapping
            f.write("## B. Source-to-Target Mapping Matrix\n\n")
            f.write("| Requirement | QLAdmin Target | LifePRO Source | Candidate Fields | Dimensions | Confidence | Notes |\n")
            f.write("|------------|----------------|----------------|------------------|------------|------------|-------|\n")
            
            mappings = [
                ("Interest Values", "QUIKUINT", self.findings['interest_candidates']),
                ("Expenses", "N/A", self.findings['expense_candidates']),
                ("COI Factors", "QUIKCOI", self.findings['coi_candidates']),
                ("Guaranteed COI", "QUIKGCOI", self.findings['gcoi_candidates']),
                ("Surrender Charges", "QUIKISSC", self.findings['surrender_candidates']),
                ("Gross Premiums", "QUIKGPS", self.findings['premium_candidates']),
                ("Cash Values", "QUIKCVS", self.findings['cash_value_candidates'])
            ]
            
            for req, target, candidates in mappings:
                if candidates:
                    for cand in candidates[:1]:  # Show first candidate
                        file_name = Path(cand.get('file', '')).name
                        fields = ', '.join(cand.get('fields', [])[:3]) if 'fields' in cand else cand.get('type_code', '')
                        dims = self._format_dimensions(cand.get('dimensions', {}))
                        confidence = self._assess_confidence(cand)
                        notes = f"TYPE_CODE={cand.get('type_code', 'N/A')}" if 'type_code' in cand else ""
                        f.write(f"| {req} | {target} | {file_name} | {fields} | {dims} | {confidence} | {notes} |\n")
                else:
                    f.write(f"| {req} | {target} | NOT FOUND | - | - | N/A | Missing from available extracts |\n")
            
            # ISWL Plan Codes
            f.write("\n## C. ISWL Plan Code Findings\n\n")
            if self.findings['iswl_plans_found']:
                f.write("### Potential ISWL Plans:\n\n")
                for plan in sorted(self.findings['iswl_plans_found']):
                    f.write(f"- `{plan}`\n")
            else:
                f.write("**No explicit ISWL plan codes identified.**\n\n")
                f.write("*Recommendation: Request business to provide list of ISWL plan codes for targeted search.*\n\n")
            
            # Table-by-Table Findings
            f.write("## D. Table-by-Table Findings\n\n")
            
            sections = [
                ("Interest Values / QUIKUINT", self.findings['interest_candidates']),
                ("Expenses", self.findings['expense_candidates']),
                ("COI / QUIKCOI", self.findings['coi_candidates']),
                ("Guaranteed COI / QUIKGCOI", self.findings['gcoi_candidates']),
                ("Surrender Charges / QUIKISSC", self.findings['surrender_candidates']),
                ("Gross Premiums / QUIKGPS", self.findings['premium_candidates']),
                ("Cash Values / QUIKCVS", self.findings['cash_value_candidates'])
            ]
            
            for section_name, candidates in sections:
                f.write(f"### {section_name}\n\n")
                if candidates:
                    for cand in candidates:
                        f.write(f"**Source:** `{Path(cand.get('file', '')).name}`\n\n")
                        if 'type_code' in cand:
                            f.write(f"- TYPE_CODE: `{cand['type_code']}`\n")
                        if 'count' in cand:
                            f.write(f"- Record Count: {cand['count']:,}\n")
                        if 'dimensions' in cand:
                            f.write(f"- Dimensions:\n")
                            dims = cand['dimensions']
                            if isinstance(dims, dict):
                                for dim, info in dims.items():
                                    f.write(f"  - {dim}: {info['unique_count']} unique values\n")
                            else:
                                f.write(f"  - {dims}\n")
                        f.write("\n")
                else:
                    f.write("**Status:** Not found in available extracts\n\n")
            
            # Structural Uniformity
            f.write("## E. Structural Uniformity Analysis\n\n")
            if self.findings['structural_issues']:
                for issue in self.findings['structural_issues']:
                    f.write(f"- {issue}\n")
            else:
                f.write("*Analysis pending - requires complete rate table set for comparison.*\n")
            f.write("\n")
            
            # Data Gaps
            f.write("## F. Data Gaps / Questions for Business\n\n")
            
            gaps = []
            if not self.findings['iswl_plans_found']:
                gaps.append("**ISWL Plan Codes:** No ISWL plans explicitly identified - need business to provide plan code list")
            if not self.findings['interest_candidates']:
                gaps.append("**Interest Rates:** No interest rate fields found - where does LifePRO store guaranteed/current credited rates?")
            if not self.findings['expense_candidates']:
                gaps.append("**Expense Charges:** No expense charge data found - need monthly expense, % of premium fields")
            if not self.findings['gcoi_candidates']:
                gaps.append("**Guaranteed COI:** No guaranteed COI table found - separate from current COI?")
            
            gaps.append("**Extract Completeness:** Current analysis limited by disk space - full LifePRO_Extracts_20260530.zip not extracted")
            gaps.append("**Dimensional Consistency:** Need to verify UW class/band structures match across all ISWL rate tables")
            
            for gap in gaps:
                f.write(f"### {gap}\n\n")
            
            # Recommended Next Steps
            f.write("## G. Recommended Next Steps\n\n")
            f.write("1. **Extract Full LifePRO Package**\n")
            f.write("   - Clear disk space and extract complete `LifePRO_Extracts_20260530.zip`\n")
            f.write("   - Search for additional rate/value tables not yet reviewed\n\n")
            
            f.write("2. **Obtain ISWL Plan Code List**\n")
            f.write("   - Request business to provide definitive list of ISWL plan codes\n")
            f.write("   - Use plan codes to filter rate tables for ISWL-specific data\n\n")
            
            f.write("3. **Identify Interest Rate Source**\n")
            f.write("   - Locate LifePRO table/fields for guaranteed and current credited interest rates\n")
            f.write("   - Clarify if rates are plan-level, policy-level, or time-variant\n\n")
            
            f.write("4. **Locate Expense Charge Data**\n")
            f.write("   - Find monthly expense per policy\n")
            f.write("   - Find percent of premium expense\n")
            f.write("   - Find monthly expense per $1,000 if applicable\n\n")
            
            f.write("5. **Verify Guaranteed COI Structure**\n")
            f.write("   - Confirm if guaranteed COI is separate from current COI\n")
            f.write("   - Identify LifePRO table/TYPE_CODE for guaranteed COI\n\n")
            
            f.write("6. **Dimensional Uniformity Validation**\n")
            f.write("   - Once ISWL plans identified, extract all rate tables for those plans\n")
            f.write("   - Compare UW class, band, age, duration structures across:\n")
            f.write("     - COI\n")
            f.write("     - Guaranteed COI\n")
            f.write("     - Surrender charges\n")
            f.write("     - Gross premiums\n")
            f.write("     - Cash values\n")
            f.write("   - Document and resolve any structural mismatches before coding\n\n")
            
            f.write("7. **QLAdmin Schema Validation**\n")
            f.write("   - Confirm QLAdmin table structures for QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC, QUIKGPS, QUIKCVS\n")
            f.write("   - Verify field mappings and data type requirements\n\n")
            
            # Files Reviewed
            f.write("## H. Files Reviewed\n\n")
            for file in self.findings['files_reviewed']:
                f.write(f"- `{file}`\n")
            
        print(f"Report written to: {output_path}")
    
    def _format_dimensions(self, dims):
        """Format dimensions dict for table display"""
        if not dims:
            return "Unknown"
        if isinstance(dims, str):
            return dims
        parts = [f"{k}({v['unique_count']})" for k, v in dims.items()]
        return ', '.join(parts[:3])
    
    def _assess_confidence(self, candidate):
        """Assess confidence level for candidate source"""
        if 'type_code' in candidate and 'dimensions' in candidate:
            dim_count = len(candidate['dimensions'])
            if dim_count >= 4:
                return "High"
            elif dim_count >= 2:
                return "Medium"
        return "Low"

def main():
    """Run ISWL discovery analysis"""
    print("="*80)
    print("ISWL SOURCE DATA DISCOVERY TOOL")
    print("="*80)
    print("\nThis tool analyzes LifePRO extracts to locate ISWL-related rate and value data.")
    print("Analysis only - no production code changes.\n")
    
    analyzer = ISWLDiscoveryAnalyzer()
    
    # Analyze available rate files
    rate_files = [
        RATE_SOURCE_DIR / "Rate_Table_Extract_20260427.csv",
        RATE_SOURCE_DIR / "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv",
        PFSA_RATES_DIR / "iswl-prem.csv"
    ]
    
    for rate_file in rate_files:
        if rate_file.exists():
            if "Rate_Table_Extract" in rate_file.name:
                analyzer.analyze_rate_table_extract(rate_file)
            elif "PAAGERAT" in rate_file.name:
                analyzer.analyze_attained_age_rates(rate_file)
            elif "iswl-prem" in rate_file.name:
                analyzer.analyze_iswl_premium_file(rate_file)
        else:
            print(f"\nFile not found: {rate_file}")
    
    # Search for interest rates
    analyzer.search_for_interest_rates()
    
    # Check structural uniformity
    analyzer.check_structural_uniformity()
    
    # Generate report
    report_path = PROJECT_ROOT / "QLA_Migration" / "ISWL_Source_Data_Discovery_Report.md"
    analyzer.generate_report(report_path)
    
    print("\n" + "="*80)
    print("DISCOVERY ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nReport generated: {report_path}")
    print(f"\nFiles reviewed: {len(analyzer.findings['files_reviewed'])}")
    print(f"ISWL plans found: {len(analyzer.findings['iswl_plans_found'])}")
    print(f"Cash value candidates: {len(analyzer.findings['cash_value_candidates'])}")
    print(f"Premium candidates: {len(analyzer.findings['premium_candidates'])}")
    print(f"COI candidates: {len(analyzer.findings['coi_candidates'])}")
    print(f"Surrender charge candidates: {len(analyzer.findings['surrender_candidates'])}")

if __name__ == "__main__":
    main()
