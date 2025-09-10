#!/usr/bin/env python3

import requests
import json

def test_proper_company_creation():
    """Test company creation with proper CompanyCreate model"""
    base_url = "https://sawayatta-erp-1.preview.emergentagent.com/api"
    
    # Login
    login_response = requests.post(f'{base_url}/auth/login', 
                                  json={'username': 'admin', 'password': 'admin123'})
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("✅ Login successful")
    
    # Get master data IDs
    master_data = {}
    endpoints = ['company-types', 'account-types', 'regions', 'business-types', 'industries', 'sub-industries', 'countries', 'states', 'cities']
    
    for endpoint in endpoints:
        response = requests.get(f'{base_url}/{endpoint}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                master_data[endpoint] = data[0]['id']
    
    print("✅ Master data collected")
    
    # Create proper company data matching CompanyCreate model
    company_data = {
        # General Info - required fields
        "company_name": "TechCorp Solutions Ltd Test",
        "domestic_international": "Domestic",
        "gst_number": "27ABCDE1234Z1Z5",
        "pan_number": "ABCDE1234F",
        "company_type_id": master_data.get('company-types'),
        "account_type_id": master_data.get('account-types'),
        "region_id": master_data.get('regions'),
        "business_type_id": master_data.get('business-types'),
        "industry_id": master_data.get('industries'),
        "sub_industry_id": master_data.get('sub-industries'),
        "employee_count": 250,
        
        # Location - required fields
        "address": "123 Tech Park, Innovation District, Mumbai",
        "country_id": master_data.get('countries'),
        "state_id": master_data.get('states'),
        "city_id": master_data.get('cities'),
        
        # Financials - required fields
        "turnover": [],
        "profit": [],
        "annual_revenue": 50000000.0,
        "revenue_currency": "INR",
        
        # Optional fields
        "website": "https://techcorp.example.com",
        "is_child": False,
        "company_profile": "Leading technology solutions provider",
        
        # Checklist validation
        "valid_gst": True,
        "active_status": True,
        "parent_linkage_valid": True
    }
    
    print("Creating company with proper data structure...")
    create_response = requests.post(f'{base_url}/companies', json=company_data, headers=headers)
    print(f"Company CREATE: {create_response.status_code}")
    
    if create_response.status_code == 200:
        response_data = create_response.json()
        print(f"✅ Company created successfully!")
        print(f"   Company ID: {response_data.get('id')}")
        print(f"   Score: {response_data.get('score', 'N/A')}")
        print(f"   Lead Status: {response_data.get('lead_status', 'N/A')}")
        return True
    else:
        print(f"❌ Company creation failed")
        print(f"Response: {create_response.text}")
        return False

if __name__ == "__main__":
    test_proper_company_creation()