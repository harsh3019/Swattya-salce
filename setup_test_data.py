#!/usr/bin/env python3
"""
Setup Complete Test Data for Opportunity Stage Testing
"""

import requests
import json

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def setup_complete_test_data():
    print("🏗️ SETTING UP COMPLETE TEST DATA FOR OPPORTUNITY STAGE TESTING")
    print("=" * 70)
    
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
    
    # Step 2: Get all required master data IDs
    print("\n2. Getting master data IDs...")
    
    master_data = {}
    
    # Get master data for company creation
    master_endpoints = [
        ('company_types', 'company-types'),
        ('account_types', 'account-types'),
        ('regions', 'regions'),
        ('business_types', 'business-types'),
        ('industries', 'industries'),
        ('sub_industries', 'sub-industries'),
        ('countries', 'countries'),
        ('states', 'states'),
        ('cities', 'cities'),
        ('product_services', 'product-services'),
        ('sub_tender_types', 'sub-tender-types')
    ]
    
    for key, endpoint in master_endpoints:
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    master_data[key] = data[0].get('id')
                    print(f"✅ {key}: {master_data[key]}")
                else:
                    print(f"❌ No {key} found")
                    return
            else:
                print(f"❌ Failed to get {key}: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Error getting {key}: {e}")
            return
    
    # Step 3: Create a company
    print("\n3. Creating test company...")
    
    company_data = {
        "company_name": "TechCorp Solutions Pvt Ltd",
        "domestic_international": "Domestic",
        "gst_number": "27ABCDE1234F1Z5",
        "pan_number": "ABCDE1234F",
        "company_type_id": master_data['company_types'],
        "account_type_id": master_data['account_types'],
        "region_id": master_data['regions'],
        "business_type_id": master_data['business_types'],
        "industry_id": master_data['industries'],
        "sub_industry_id": master_data['sub_industries'],
        "website": "https://techcorp.com",
        "is_child": False,
        "employee_count": 150,
        "address": "123 Tech Park, Sector 5, Pune, Maharashtra",
        "country_id": master_data['countries'],
        "state_id": master_data['states'],
        "city_id": master_data['cities'],
        "turnover": [],
        "profit": [],
        "annual_revenue": 50000000,
        "revenue_currency": "INR",
        "company_profile": "Leading technology solutions provider",
        "valid_gst": True,
        "active_status": True,
        "parent_linkage_valid": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/companies",
            headers=headers,
            json=company_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            created_company = response.json()
            company_id = created_company.get('id')
            print(f"✅ Created company: {company_id}")
            master_data['company_id'] = company_id
        else:
            print(f"❌ Failed to create company: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error creating company: {e}")
        return
    
    # Step 4: Create multiple leads with different stages
    print("\n4. Creating test leads...")
    
    leads_to_create = [
        {
            "project_title": "CRM Implementation - L1 Testing",
            "expected_orc": 500000,
            "target_stage": 1
        },
        {
            "project_title": "ERP System Upgrade - L2 Testing", 
            "expected_orc": 750000,
            "target_stage": 2
        },
        {
            "project_title": "Digital Transformation - L3 Testing",
            "expected_orc": 1000000,
            "target_stage": 3
        },
        {
            "project_title": "Cloud Migration - L4 Testing",
            "expected_orc": 600000,
            "target_stage": 4
        }
    ]
    
    created_opportunities = []
    
    for i, lead_info in enumerate(leads_to_create):
        print(f"\n   Creating lead {i+1}: {lead_info['project_title']}")
        
        lead_data = {
            "tender_type": "Tender",
            "billing_type": "Fixed Price",
            "sub_tender_type_id": master_data['sub_tender_types'],
            "project_title": lead_info['project_title'],
            "company_id": master_data['company_id'],
            "state": "Maharashtra",
            "lead_subtype": "New Business",
            "source": "Website",
            "product_service_id": master_data['product_services'],
            "expected_orc": lead_info['expected_orc'],
            "revenue": lead_info['expected_orc'],
            "lead_owner": user_id
        }
        
        try:
            # Create lead
            response = requests.post(
                f"{BASE_URL}/leads",
                headers=headers,
                json=lead_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                created_lead = response.json()
                lead_id = created_lead.get('id')
                print(f"     ✅ Created lead: {lead_id}")
                
                # Approve lead
                approval_response = requests.post(
                    f"{BASE_URL}/leads/{lead_id}/status",
                    headers=headers,
                    json={"status": "approved"},
                    timeout=10
                )
                
                if approval_response.status_code == 200:
                    print(f"     ✅ Lead approved")
                    
                    # Convert to opportunity
                    convert_response = requests.post(
                        f"{BASE_URL}/leads/{lead_id}/convert",
                        headers=headers,
                        params={"opportunity_date": "2024-01-15"},
                        timeout=10
                    )
                    
                    if convert_response.status_code == 200:
                        conversion_result = convert_response.json()
                        opportunity_id = conversion_result.get('opportunity_id')
                        print(f"     ✅ Converted to opportunity: {opportunity_id}")
                        
                        created_opportunities.append({
                            'id': opportunity_id,
                            'target_stage': lead_info['target_stage'],
                            'title': lead_info['project_title']
                        })
                        
                    else:
                        print(f"     ❌ Conversion failed: {convert_response.status_code}")
                        
                else:
                    print(f"     ❌ Approval failed: {approval_response.status_code}")
                    
            else:
                print(f"     ❌ Lead creation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"     ❌ Error with lead {i+1}: {e}")
    
    # Step 5: Progress opportunities to their target stages
    print("\n5. Progressing opportunities to target stages...")
    
    for opp in created_opportunities:
        if opp['target_stage'] > 1:
            print(f"\n   Progressing {opp['id']} to L{opp['target_stage']}...")
            
            # Progress through stages one by one
            for stage in range(2, opp['target_stage'] + 1):
                stage_data = {
                    "target_stage": stage,
                    "stage_data": {
                        "region_id": master_data['regions'],
                        "product_interest": "CRM Software",
                        "assigned_representatives": ["Test Rep"],
                        "lead_owner_id": user_id
                    }
                }
                
                try:
                    stage_response = requests.post(
                        f"{BASE_URL}/opportunities/{opp['id']}/change-stage",
                        headers=headers,
                        json=stage_data,
                        timeout=10
                    )
                    
                    if stage_response.status_code == 200:
                        print(f"     ✅ Progressed to L{stage}")
                    else:
                        print(f"     ❌ Failed to progress to L{stage}: {stage_response.status_code}")
                        break
                        
                except Exception as e:
                    print(f"     ❌ Error progressing to L{stage}: {e}")
                    break
    
    # Step 6: Verify final state
    print("\n6. Verifying final opportunity states...")
    
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            opportunities_data = response.json()
            opportunities = opportunities_data.get('opportunities', [])
            total_opps = opportunities_data.get('total', 0)
            
            print(f"\n📊 FINAL OPPORTUNITY STAGE ANALYSIS:")
            print(f"Total opportunities: {total_opps}")
            
            stage_distribution = {}
            
            for opp in opportunities:
                current_stage = opp.get('current_stage')
                opp_id = opp.get('opportunity_id') or opp.get('id')
                project_title = opp.get('project_title', 'N/A')
                
                if current_stage not in stage_distribution:
                    stage_distribution[current_stage] = 0
                stage_distribution[current_stage] += 1
                
                print(f"   ID: {opp_id}, Stage: L{current_stage}, Title: {project_title}")
            
            print(f"\n📈 STAGE DISTRIBUTION:")
            for stage in sorted(stage_distribution.keys()):
                print(f"   L{stage}: {stage_distribution[stage]} opportunities")
            
            # Check if we have opportunities beyond L1
            beyond_l1 = sum(count for stage, count in stage_distribution.items() if stage > 1)
            
            if beyond_l1 > 0:
                print(f"\n✅ SUCCESS: {beyond_l1} opportunities are beyond L1 stage")
                print(f"✅ This should resolve the 'Manage Stages always opens L1' issue")
            else:
                print(f"\n❌ ISSUE: All opportunities are still at L1 stage")
                
        else:
            print(f"❌ Failed to verify opportunities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying opportunities: {e}")
    
    print(f"\n🎉 TEST DATA SETUP COMPLETED!")

if __name__ == "__main__":
    setup_complete_test_data()