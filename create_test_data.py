#!/usr/bin/env python3
"""
Create Test Data for Opportunity Stage Testing
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def create_test_data():
    print("🏗️ CREATING TEST DATA FOR OPPORTUNITY STAGE TESTING")
    print("=" * 60)
    
    # Step 1: Authenticate
    print("\n1. Authenticating...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=ADMIN_CREDENTIALS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            user_id = data.get("user", {}).get("id")
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Check master data
    print("\n2. Checking master data...")
    
    # Check companies
    try:
        response = requests.get(f"{BASE_URL}/companies", headers=headers, timeout=10)
        if response.status_code == 200:
            companies = response.json()
            print(f"Companies available: {len(companies)}")
            if companies:
                company_id = companies[0].get('id')
                print(f"Using company ID: {company_id}")
            else:
                print("No companies found - creating one...")
                # Create a test company
                company_data = {
                    "company_name": "Test Tech Solutions",
                    "company_type": "Private Limited",
                    "industry": "Technology",
                    "website": "https://testtech.com",
                    "employee_count": 100
                }
                create_response = requests.post(f"{BASE_URL}/companies", headers=headers, json=company_data, timeout=10)
                if create_response.status_code == 201:
                    company_id = create_response.json().get('id')
                    print(f"Created company with ID: {company_id}")
                else:
                    print(f"Failed to create company: {create_response.status_code} - {create_response.text}")
                    company_id = None
        else:
            print(f"Failed to get companies: {response.status_code}")
            company_id = None
    except Exception as e:
        print(f"Error checking companies: {e}")
        company_id = None
    
    # Check product services
    try:
        response = requests.get(f"{BASE_URL}/product-services", headers=headers, timeout=10)
        if response.status_code == 200:
            services = response.json()
            print(f"Product services available: {len(services)}")
            if services:
                service_id = services[0].get('id')
                print(f"Using service ID: {service_id}")
            else:
                service_id = None
        else:
            service_id = None
    except Exception as e:
        print(f"Error checking product services: {e}")
        service_id = None
    
    # Step 3: Create opportunities directly (since lead conversion might be complex)
    print("\n3. Creating test opportunities...")
    
    opportunities_to_create = [
        {
            "project_title": "CRM Implementation Project",
            "company_id": company_id,
            "expected_revenue": 500000,
            "currency_id": "inr-uuid",
            "lead_owner_id": user_id,
            "win_probability": 25,
            "current_stage": 1
        },
        {
            "project_title": "ERP System Upgrade",
            "company_id": company_id,
            "expected_revenue": 750000,
            "currency_id": "inr-uuid",
            "lead_owner_id": user_id,
            "win_probability": 50,
            "current_stage": 2
        },
        {
            "project_title": "Digital Transformation Initiative",
            "company_id": company_id,
            "expected_revenue": 1000000,
            "currency_id": "inr-uuid",
            "lead_owner_id": user_id,
            "win_probability": 75,
            "current_stage": 3
        }
    ]
    
    created_opportunities = []
    
    for i, opp_data in enumerate(opportunities_to_create):
        try:
            response = requests.post(
                f"{BASE_URL}/opportunities",
                headers=headers,
                json=opp_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                created_opp = response.json()
                created_opportunities.append(created_opp)
                opp_id = created_opp.get('opportunity_id') or created_opp.get('id')
                print(f"✅ Created opportunity {i+1}: {opp_id} - {opp_data['project_title']}")
            else:
                print(f"❌ Failed to create opportunity {i+1}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating opportunity {i+1}: {e}")
    
    # Step 4: Verify created opportunities
    print("\n4. Verifying created opportunities...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            opportunities_data = response.json()
            opportunities = opportunities_data.get('opportunities', [])
            total_opps = opportunities_data.get('total', 0)
            
            print(f"Total opportunities now: {total_opps}")
            
            if opportunities:
                print(f"\n📋 OPPORTUNITY STAGE ANALYSIS:")
                for opp in opportunities:
                    current_stage = opp.get('current_stage')
                    opp_id = opp.get('opportunity_id') or opp.get('id')
                    project_title = opp.get('project_title', 'N/A')
                    print(f"   ID: {opp_id}, Stage: L{current_stage}, Title: {project_title}")
                    
                # Test stage progression by updating one opportunity to L4
                if len(opportunities) > 0:
                    test_opp = opportunities[0]
                    test_opp_id = test_opp.get('opportunity_id') or test_opp.get('id')
                    
                    print(f"\n5. Testing stage progression for opportunity {test_opp_id}...")
                    
                    # Try to change stage to L4
                    stage_data = {
                        "target_stage": 4,
                        "stage_data": {
                            "region_id": "test-region",
                            "product_interest": "CRM Software",
                            "assigned_representatives": ["Test Rep"],
                            "lead_owner_id": user_id
                        }
                    }
                    
                    stage_response = requests.post(
                        f"{BASE_URL}/opportunities/{test_opp_id}/change-stage",
                        headers=headers,
                        json=stage_data,
                        timeout=10
                    )
                    
                    if stage_response.status_code == 200:
                        stage_result = stage_response.json()
                        print(f"✅ Stage progression successful: {stage_result.get('message', 'Success')}")
                    else:
                        print(f"❌ Stage progression failed: {stage_response.status_code} - {stage_response.text}")
            
        else:
            print(f"❌ Failed to verify opportunities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying opportunities: {e}")
    
    print(f"\n✅ Test data creation completed!")

if __name__ == "__main__":
    create_test_data()