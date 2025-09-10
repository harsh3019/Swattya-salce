#!/usr/bin/env python3

import requests
import json

def test_basic_company_functionality():
    """Test basic company functionality"""
    base_url = "https://erp-quotation.preview.emergentagent.com/api"
    
    # Login
    login_response = requests.post(f'{base_url}/auth/login', 
                                  json={'username': 'admin', 'password': 'admin123'})
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("✅ Login successful")
    
    # Test existing companies endpoint
    companies_response = requests.get(f'{base_url}/companies', headers=headers)
    print(f"Companies GET: {companies_response.status_code}")
    
    if companies_response.status_code == 200:
        companies = companies_response.json()
        print(f"✅ Found {len(companies)} existing companies")
    
    # Test simple company creation using the original Company model
    simple_company = {
        "company_name": "Test Company Simple",
        "employee_count": 50,
        "is_domestic": True,
        "gst_number": "27ABCDE1234Z1Z5",
        "pan_number": "ABCDE1234F"
    }
    
    create_response = requests.post(f'{base_url}/companies', json=simple_company, headers=headers)
    print(f"Company CREATE: {create_response.status_code}")
    
    if create_response.status_code != 200:
        print(f"Create response: {create_response.text}")
        return False
    
    print("✅ Company creation successful")
    return True

if __name__ == "__main__":
    test_basic_company_functionality()