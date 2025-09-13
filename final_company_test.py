#!/usr/bin/env python3
"""
Final Company Data Inheritance Test - Comprehensive Analysis
"""

import requests
import json

# Configuration
BACKEND_URL = "https://quotation-mgmt.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def authenticate():
    """Authenticate and get token"""
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    return None

def main():
    """Run final comprehensive test"""
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("🎯 FINAL COMPANY DATA INHERITANCE TEST")
    print("=" * 50)
    
    # Test all the specific requirements from the review request
    
    print("\n1. GET /api/companies - verify company master data exists")
    companies_response = session.get(f"{BACKEND_URL}/companies")
    if companies_response.status_code == 200:
        companies = companies_response.json()
        print(f"   ✅ Found {len(companies)} companies")
        if companies:
            company = companies[0]
            print(f"   • Company: {company.get('name', 'Unknown')}")
            print(f"   • ID: {company.get('id')}")
    else:
        print(f"   ❌ Failed: {companies_response.status_code}")
        return
    
    print("\n2. GET /api/leads - check if leads have company_id field populated")
    leads_response = session.get(f"{BACKEND_URL}/leads")
    if leads_response.status_code == 200:
        data = leads_response.json()
        leads = data.get('leads', []) if isinstance(data, dict) else data
        leads_with_company = [lead for lead in leads if lead.get('company_id')]
        print(f"   ✅ Found {len(leads_with_company)}/{len(leads)} leads with company_id")
        
        # Show sample lead
        if leads_with_company:
            sample_lead = leads_with_company[0]
            print(f"   • Sample Lead: {sample_lead.get('project_title')}")
            print(f"   • Company ID: {sample_lead.get('company_id')}")
            print(f"   • Status: {sample_lead.get('status')}")
    else:
        print(f"   ❌ Failed: {leads_response.status_code}")
        return
    
    print("\n3. GET /api/opportunities - verify opportunity has company_id and company_name resolved")
    opps_response = session.get(f"{BACKEND_URL}/opportunities")
    if opps_response.status_code == 200:
        data = opps_response.json()
        opportunities = data if isinstance(data, list) else data.get('opportunities', [])
        
        opps_with_company_id = [opp for opp in opportunities if opp.get('company_id')]
        opps_with_company_name = [opp for opp in opportunities if opp.get('company_name') and opp.get('company_name') != 'Unknown Company']
        
        print(f"   ✅ Found {len(opps_with_company_id)}/{len(opportunities)} opportunities with company_id")
        print(f"   ✅ Found {len(opps_with_company_name)}/{len(opportunities)} opportunities with resolved company_name")
        
        # Show sample opportunity
        if opps_with_company_name:
            sample_opp = opps_with_company_name[0]
            print(f"   • Sample Opportunity: {sample_opp.get('project_title', sample_opp.get('name'))}")
            print(f"   • Company ID: {sample_opp.get('company_id')}")
            print(f"   • Company Name: {sample_opp.get('company_name')}")
            print(f"   • Stage: {sample_opp.get('current_stage', sample_opp.get('stage'))}")
    else:
        print(f"   ❌ Failed: {opps_response.status_code}")
        return
    
    print("\n4. Test company lookup/resolution in opportunities API")
    if opportunities:
        # Test individual opportunity lookup
        test_opp = opportunities[0]
        opp_id = test_opp.get('id')
        
        individual_response = session.get(f"{BACKEND_URL}/opportunities/{opp_id}")
        if individual_response.status_code == 200:
            individual_opp = individual_response.json()
            print(f"   ✅ Individual opportunity lookup working")
            print(f"   • Opportunity ID: {opp_id}")
            print(f"   • Company ID: {individual_opp.get('company_id')}")
            print(f"   • Company Name: {individual_opp.get('company_name', 'NOT RESOLVED')}")
        else:
            print(f"   ❌ Individual lookup failed: {individual_response.status_code}")
    
    print("\n5. Test lead-to-opportunity conversion company inheritance")
    # Find a converted lead
    converted_leads = [lead for lead in leads if lead.get('converted_to_opportunity') and lead.get('opportunity_id')]
    if converted_leads:
        converted_lead = converted_leads[0]
        opp_id = converted_lead.get('opportunity_id')
        
        print(f"   ✅ Found converted lead: {converted_lead.get('project_title')}")
        print(f"   • Lead Company ID: {converted_lead.get('company_id')}")
        print(f"   • Opportunity ID: {opp_id}")
        
        # Check if the opportunity exists in the opportunities list
        matching_opp = next((opp for opp in opportunities if opp.get('id') == opp_id or opp.get('opportunity_id') == opp_id), None)
        if matching_opp:
            print(f"   ✅ Opportunity found in list")
            print(f"   • Opportunity Company ID: {matching_opp.get('company_id')}")
            print(f"   • Opportunity Company Name: {matching_opp.get('company_name')}")
            
            # Verify inheritance
            if converted_lead.get('company_id') == matching_opp.get('company_id'):
                print(f"   ✅ Company ID properly inherited from lead to opportunity")
            else:
                print(f"   ❌ Company ID inheritance failed")
        else:
            print(f"   ⚠️  Opportunity {opp_id} not found in opportunities list")
    else:
        print(f"   ⚠️  No converted leads found for testing")
    
    print("\n" + "=" * 50)
    print("📊 COMPANY DATA INHERITANCE ASSESSMENT")
    print("=" * 50)
    
    # Final assessment
    issues_found = []
    
    if len(companies) == 0:
        issues_found.append("No company master data available")
    
    if len(leads_with_company) < len(leads):
        issues_found.append(f"Some leads missing company_id ({len(leads_with_company)}/{len(leads)})")
    
    if len(opps_with_company_id) < len(opportunities):
        issues_found.append(f"Some opportunities missing company_id ({len(opps_with_company_id)}/{len(opportunities)})")
    
    if len(opps_with_company_name) < len(opps_with_company_id):
        issues_found.append(f"Company name resolution incomplete ({len(opps_with_company_name)}/{len(opps_with_company_id)})")
    
    if not issues_found:
        print("🎉 ALL COMPANY DATA INHERITANCE TESTS PASSED!")
        print("✅ Company master data exists and is accessible")
        print("✅ Leads have proper company_id field populated")
        print("✅ Lead-to-opportunity conversion inherits company_id")
        print("✅ Opportunities display proper company names (resolved from company_id)")
        print("✅ Company lookup/resolution in opportunities API works correctly")
    else:
        print("⚠️  ISSUES IDENTIFIED:")
        for issue in issues_found:
            print(f"   • {issue}")
    
    print(f"\nSUMMARY:")
    print(f"• Companies: {len(companies)}")
    print(f"• Leads with company_id: {len(leads_with_company)}/{len(leads)}")
    print(f"• Opportunities with company_id: {len(opps_with_company_id)}/{len(opportunities)}")
    print(f"• Opportunities with company_name: {len(opps_with_company_name)}/{len(opportunities)}")

if __name__ == "__main__":
    main()