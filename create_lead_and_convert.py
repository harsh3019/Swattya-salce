#!/usr/bin/env python3
"""
Create Lead and Convert to Opportunity for Testing
"""

import requests
import json

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def create_lead_and_convert():
    print("🏗️ CREATING LEAD AND CONVERTING TO OPPORTUNITY")
    print("=" * 50)
    
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
            print(f"✅ Authentication successful, User ID: {user_id}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Get master data needed for lead creation
    print("\n2. Getting master data...")
    
    master_data = {}
    
    # Get companies
    try:
        response = requests.get(f"{BASE_URL}/companies", headers=headers, timeout=10)
        if response.status_code == 200:
            companies = response.json()
            if companies:
                master_data['company_id'] = companies[0].get('id')
                print(f"✅ Found company: {master_data['company_id']}")
            else:
                print("❌ No companies found")
                return
        else:
            print(f"❌ Failed to get companies: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting companies: {e}")
        return
    
    # Get product services
    try:
        response = requests.get(f"{BASE_URL}/product-services", headers=headers, timeout=10)
        if response.status_code == 200:
            services = response.json()
            if services:
                master_data['product_service_id'] = services[0].get('id')
                print(f"✅ Found product service: {master_data['product_service_id']}")
            else:
                print("❌ No product services found")
                return
        else:
            print(f"❌ Failed to get product services: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting product services: {e}")
        return
    
    # Get sub-tender types
    try:
        response = requests.get(f"{BASE_URL}/sub-tender-types", headers=headers, timeout=10)
        if response.status_code == 200:
            sub_tender_types = response.json()
            if sub_tender_types:
                master_data['sub_tender_type_id'] = sub_tender_types[0].get('id')
                print(f"✅ Found sub-tender type: {master_data['sub_tender_type_id']}")
            else:
                print("❌ No sub-tender types found")
                return
        else:
            print(f"❌ Failed to get sub-tender types: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting sub-tender types: {e}")
        return
    
    # Step 3: Create a lead
    print("\n3. Creating lead...")
    
    lead_data = {
        "tender_type": "Tender",
        "billing_type": "Fixed Price",
        "sub_tender_type_id": master_data['sub_tender_type_id'],
        "project_title": "CRM Implementation Project - Stage Testing",
        "company_id": master_data['company_id'],
        "state": "Maharashtra",
        "lead_subtype": "New Business",
        "source": "Website",
        "product_service_id": master_data['product_service_id'],
        "expected_orc": 500000,
        "revenue": 500000,
        "lead_owner": user_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/leads",
            headers=headers,
            json=lead_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            created_lead = response.json()
            lead_id = created_lead.get('id')
            print(f"✅ Created lead: {lead_id}")
            
            # Step 4: Approve the lead
            print(f"\n4. Approving lead {lead_id}...")
            
            approval_response = requests.post(
                f"{BASE_URL}/leads/{lead_id}/status",
                headers=headers,
                json={"status": "approved"},
                timeout=10
            )
            
            if approval_response.status_code == 200:
                print(f"✅ Lead approved successfully")
                
                # Step 5: Convert lead to opportunity
                print(f"\n5. Converting lead {lead_id} to opportunity...")
                
                convert_response = requests.post(
                    f"{BASE_URL}/leads/{lead_id}/convert",
                    headers=headers,
                    params={"opportunity_date": "2024-01-15"},
                    timeout=10
                )
                
                if convert_response.status_code == 200:
                    conversion_result = convert_response.json()
                    opportunity_id = conversion_result.get('opportunity_id')
                    print(f"✅ Lead converted to opportunity: {opportunity_id}")
                    
                    # Step 6: Verify the opportunity
                    print(f"\n6. Verifying opportunity {opportunity_id}...")
                    
                    opp_response = requests.get(
                        f"{BASE_URL}/opportunities/{opportunity_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if opp_response.status_code == 200:
                        opportunity = opp_response.json()
                        current_stage = opportunity.get('current_stage')
                        project_title = opportunity.get('project_title')
                        print(f"✅ Opportunity verified: Stage L{current_stage}, Title: {project_title}")
                        
                        # Step 7: Test stage progression
                        print(f"\n7. Testing stage progression to L2...")
                        
                        stage_data = {
                            "target_stage": 2,
                            "stage_data": {
                                "region_id": "test-region",
                                "product_interest": "CRM Software",
                                "assigned_representatives": ["Test Rep"],
                                "lead_owner_id": user_id
                            }
                        }
                        
                        stage_response = requests.post(
                            f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                            headers=headers,
                            json=stage_data,
                            timeout=10
                        )
                        
                        if stage_response.status_code == 200:
                            stage_result = stage_response.json()
                            print(f"✅ Stage progression to L2 successful: {stage_result.get('message')}")
                            
                            # Verify stage change
                            verify_response = requests.get(
                                f"{BASE_URL}/opportunities/{opportunity_id}",
                                headers=headers,
                                timeout=10
                            )
                            
                            if verify_response.status_code == 200:
                                updated_opp = verify_response.json()
                                new_stage = updated_opp.get('current_stage')
                                print(f"✅ Stage verified: Now at L{new_stage}")
                            
                        else:
                            print(f"❌ Stage progression failed: {stage_response.status_code} - {stage_response.text}")
                        
                    else:
                        print(f"❌ Failed to verify opportunity: {opp_response.status_code}")
                        
                else:
                    print(f"❌ Lead conversion failed: {convert_response.status_code} - {convert_response.text}")
                    
            else:
                print(f"❌ Lead approval failed: {approval_response.status_code} - {approval_response.text}")
                
        else:
            print(f"❌ Failed to create lead: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error creating lead: {e}")
    
    # Step 8: Check all opportunities
    print(f"\n8. Checking all opportunities...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            opportunities_data = response.json()
            opportunities = opportunities_data.get('opportunities', [])
            total_opps = opportunities_data.get('total', 0)
            
            print(f"Total opportunities: {total_opps}")
            
            for opp in opportunities:
                current_stage = opp.get('current_stage')
                opp_id = opp.get('opportunity_id') or opp.get('id')
                project_title = opp.get('project_title', 'N/A')
                print(f"   ID: {opp_id}, Stage: L{current_stage}, Title: {project_title}")
                
        else:
            print(f"❌ Failed to get opportunities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting opportunities: {e}")

if __name__ == "__main__":
    create_lead_and_convert()