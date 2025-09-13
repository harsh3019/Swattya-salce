#!/usr/bin/env python3
"""
Detailed Company Data Inheritance Analysis
"""

import requests
import json

# Configuration
BACKEND_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
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

def analyze_company_inheritance():
    """Analyze company data inheritance in detail"""
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("🔍 DETAILED COMPANY DATA INHERITANCE ANALYSIS")
    print("=" * 60)
    
    # 1. Get companies
    print("\n1. COMPANY MASTER DATA:")
    companies_response = session.get(f"{BACKEND_URL}/companies")
    if companies_response.status_code == 200:
        companies = companies_response.json()
        print(f"   Found {len(companies)} companies")
        for company in companies:
            name = company.get('company_name', company.get('name', 'Unknown'))
            print(f"   • {name} (ID: {company.get('id')})")
            print(f"     Structure: {list(company.keys())}")
    else:
        print(f"   ❌ Failed to get companies: {companies_response.status_code}")
        return
    
    # 2. Get leads with company data
    print("\n2. LEADS WITH COMPANY DATA:")
    leads_response = session.get(f"{BACKEND_URL}/leads")
    if leads_response.status_code == 200:
        data = leads_response.json()
        leads = data.get('leads', []) if isinstance(data, dict) else data
        print(f"   Found {len(leads)} leads")
        
        for lead in leads[:3]:  # Show first 3 leads
            company_id = lead.get('company_id')
            company_name = next((c.get('company_name', c.get('name', 'Unknown')) for c in companies if c.get('id') == company_id), 'Unknown')
            print(f"   • Lead: {lead.get('project_title')}")
            print(f"     Company ID: {company_id}")
            print(f"     Company Name: {company_name}")
            print(f"     Status: {lead.get('status')}")
            print(f"     Converted: {lead.get('converted_to_opportunity', False)}")
            if lead.get('opportunity_id'):
                print(f"     Opportunity ID: {lead.get('opportunity_id')}")
            print()
    else:
        print(f"   ❌ Failed to get leads: {leads_response.status_code}")
        return
    
    # 3. Get opportunities with company data
    print("\n3. OPPORTUNITIES WITH COMPANY DATA:")
    opps_response = session.get(f"{BACKEND_URL}/opportunities")
    if opps_response.status_code == 200:
        data = opps_response.json()
        opportunities = data if isinstance(data, list) else data.get('opportunities', [])
        print(f"   Found {len(opportunities)} opportunities")
        
        for opp in opportunities[:5]:  # Show first 5 opportunities
            print(f"   • Opportunity: {opp.get('project_title', opp.get('name', 'Unknown'))}")
            print(f"     ID: {opp.get('id')}")
            print(f"     Company ID: {opp.get('company_id')}")
            print(f"     Company Name: {opp.get('company_name', 'NOT RESOLVED')}")
            print(f"     Stage: {opp.get('current_stage', opp.get('stage'))}")
            print(f"     Status: {opp.get('status')}")
            print()
    else:
        print(f"   ❌ Failed to get opportunities: {opps_response.status_code}")
        return
    
    # 4. Test specific opportunity lookup
    print("\n4. TESTING SPECIFIC OPPORTUNITY LOOKUP:")
    if opportunities:
        test_opp_id = opportunities[0].get('id')
        opp_detail_response = session.get(f"{BACKEND_URL}/opportunities/{test_opp_id}")
        if opp_detail_response.status_code == 200:
            opp_detail = opp_detail_response.json()
            print(f"   ✅ Successfully retrieved opportunity {test_opp_id}")
            print(f"   Company ID: {opp_detail.get('company_id')}")
            print(f"   Company Name: {opp_detail.get('company_name', 'NOT RESOLVED')}")
        else:
            print(f"   ❌ Failed to get opportunity detail: {opp_detail_response.status_code}")
    
    # 5. Summary
    print("\n5. COMPANY INHERITANCE SUMMARY:")
    leads_with_company = sum(1 for lead in leads if lead.get('company_id'))
    opps_with_company_id = sum(1 for opp in opportunities if opp.get('company_id'))
    opps_with_company_name = sum(1 for opp in opportunities if opp.get('company_name'))
    
    print(f"   • Companies in master data: {len(companies)}")
    print(f"   • Leads with company_id: {leads_with_company}/{len(leads)}")
    print(f"   • Opportunities with company_id: {opps_with_company_id}/{len(opportunities)}")
    print(f"   • Opportunities with company_name: {opps_with_company_name}/{len(opportunities)}")
    
    # Check if company names are being resolved
    if opps_with_company_id > 0 and opps_with_company_name == 0:
        print("   🚨 ISSUE IDENTIFIED: Opportunities have company_id but company_name is not being resolved!")
    elif opps_with_company_id == opps_with_company_name:
        print("   ✅ Company name resolution is working correctly!")
    else:
        print("   ⚠️  Partial company name resolution - some opportunities missing company names")

if __name__ == "__main__":
    analyze_company_inheritance()