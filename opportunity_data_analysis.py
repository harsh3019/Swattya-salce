#!/usr/bin/env python3
"""
Opportunity Data Analysis - Root Cause Analysis
Based on the debug test results, analyzing the data format mismatch
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://lead-opp-crm.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class OpportunityDataAnalyzer:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        
    def authenticate(self):
        """Authenticate and get token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                return True
            return False
        except:
            return False
    
    def analyze_data_structure_mismatch(self):
        """Analyze the root cause of the data structure mismatch"""
        print("🔍 ROOT CAUSE ANALYSIS: OPPORTUNITY DATA DISPLAY ISSUE")
        print("=" * 60)
        
        # Get the actual API response
        response = requests.get(f"{self.base_url}/opportunities", headers=self.headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("📊 ACTUAL API RESPONSE STRUCTURE:")
            print("-" * 40)
            print(f"Response Type: {type(data)}")
            print(f"Top-level Keys: {list(data.keys())}")
            print(f"Opportunities Array Length: {len(data.get('opportunities', []))}")
            print(f"Total Field Value: {data.get('total', 'NOT FOUND')}")
            
            print("\n🔍 ISSUE IDENTIFIED:")
            print("-" * 40)
            print("❌ FRONTEND EXPECTS: Direct array [] or data.data structure")
            print("✅ BACKEND RETURNS: Wrapped object with 'opportunities' key")
            print("")
            print("Backend Response Structure:")
            print("  {")
            print("    'opportunities': [...],  ← Data is here")
            print("    'total': 7,")
            print("    'page': 1,")
            print("    'limit': 20,")
            print("    'total_pages': 1")
            print("  }")
            print("")
            print("Frontend Expects:")
            print("  [...] OR { 'data': [...] }")
            
            print("\n📋 OPPORTUNITY FIELD ANALYSIS:")
            print("-" * 40)
            
            if data.get('opportunities'):
                opportunities = data['opportunities']
                
                # Analyze different opportunity structures
                converted_opportunities = []  # From leads (POT-* IDs)
                direct_opportunities = []     # Direct opportunities (OPP-* IDs)
                
                for opp in opportunities:
                    if opp.get('id', '').startswith('POT-'):
                        converted_opportunities.append(opp)
                    elif opp.get('opportunity_id', '').startswith('OPP-'):
                        direct_opportunities.append(opp)
                
                print(f"Converted Opportunities (from leads): {len(converted_opportunities)}")
                print(f"Direct Opportunities: {len(direct_opportunities)}")
                
                # Analyze field differences
                if converted_opportunities:
                    print("\n🔍 CONVERTED OPPORTUNITY FIELDS:")
                    conv_opp = converted_opportunities[0]
                    conv_fields = set(conv_opp.keys())
                    print(f"  Fields: {sorted(conv_fields)}")
                    
                    # Check for frontend expected fields
                    expected_frontend_fields = {
                        'id', 'opportunity_id', 'project_title', 'company_id', 
                        'stage_id', 'status', 'expected_revenue', 'weighted_revenue', 
                        'win_probability', 'lead_owner_id', 'created_at'
                    }
                    
                    missing_fields = expected_frontend_fields - conv_fields
                    extra_fields = conv_fields - expected_frontend_fields
                    
                    print(f"  Missing Frontend Fields: {sorted(missing_fields)}")
                    print(f"  Extra Backend Fields: {sorted(extra_fields)}")
                
                if direct_opportunities:
                    print("\n🔍 DIRECT OPPORTUNITY FIELDS:")
                    direct_opp = direct_opportunities[0]
                    direct_fields = set(direct_opp.keys())
                    print(f"  Fields: {sorted(direct_fields)}")
                    
                    # Check for frontend expected fields
                    expected_frontend_fields = {
                        'id', 'opportunity_id', 'project_title', 'company_id', 
                        'stage_id', 'status', 'expected_revenue', 'weighted_revenue', 
                        'win_probability', 'lead_owner_id', 'created_at'
                    }
                    
                    missing_fields = expected_frontend_fields - direct_fields
                    extra_fields = direct_fields - expected_frontend_fields
                    
                    print(f"  Missing Frontend Fields: {sorted(missing_fields)}")
                    print(f"  Extra Backend Fields: {sorted(extra_fields)}")
            
            print("\n🛠️  SOLUTION RECOMMENDATIONS:")
            print("-" * 40)
            print("1. FRONTEND FIX (Recommended):")
            print("   - Update frontend to handle response.opportunities instead of direct array")
            print("   - Change: data.map() → data.opportunities.map()")
            print("   - Handle pagination metadata (total, page, limit)")
            print("")
            print("2. BACKEND FIX (Alternative):")
            print("   - Change API to return direct array instead of wrapped object")
            print("   - Move pagination metadata to headers")
            print("")
            print("3. FIELD MAPPING FIXES:")
            print("   - Map 'name' field to 'project_title' for converted opportunities")
            print("   - Map 'stage' field to 'stage_id' for converted opportunities")
            print("   - Add 'status' field mapping")
            print("   - Ensure consistent field names across all opportunity types")
            
            return True
        else:
            print(f"❌ Failed to get opportunities data: {response.status_code}")
            return False
    
    def generate_frontend_fix_code(self):
        """Generate the exact frontend code fix"""
        print("\n💻 FRONTEND CODE FIX:")
        print("=" * 60)
        
        print("In OpportunityList.js, change the data handling:")
        print("")
        print("❌ CURRENT (INCORRECT):")
        print("```javascript")
        print("const response = await fetch(`${API_URL}/opportunities`);")
        print("const data = await response.json();")
        print("setOpportunities(data || []);  // ← This is wrong!")
        print("```")
        print("")
        print("✅ FIXED (CORRECT):")
        print("```javascript")
        print("const response = await fetch(`${API_URL}/opportunities`);")
        print("const data = await response.json();")
        print("setOpportunities(data.opportunities || []);  // ← Use data.opportunities")
        print("setPagination({")
        print("  total: data.total,")
        print("  page: data.page,")
        print("  limit: data.limit,")
        print("  totalPages: data.total_pages")
        print("});")
        print("```")
        
    def run_analysis(self):
        """Run the complete analysis"""
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        self.analyze_data_structure_mismatch()
        self.generate_frontend_fix_code()
        
        return True

def main():
    """Main function"""
    analyzer = OpportunityDataAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()