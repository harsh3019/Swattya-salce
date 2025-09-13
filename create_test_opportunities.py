#!/usr/bin/env python3
"""
Create Test Opportunities at Different Stages
Create opportunities at L3 and L4 stages to demonstrate stage management working
"""

import requests
import json
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def create_test_opportunities():
    print("🏗️ CREATING TEST OPPORTUNITIES AT DIFFERENT STAGES")
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
            print(f"✅ Authentication successful, User ID: {user_id}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Get master data
    print("\n2. Getting master data...")
    
    try:
        # Get companies
        companies_response = requests.get(f"{BASE_URL}/companies", headers=headers, timeout=10)
        companies = companies_response.json() if companies_response.status_code == 200 else []
        
        # Get product services
        services_response = requests.get(f"{BASE_URL}/product-services", headers=headers, timeout=10)
        services = services_response.json() if services_response.status_code == 200 else []
        
        # Get sub-tender types
        subtender_response = requests.get(f"{BASE_URL}/sub-tender-types", headers=headers, timeout=10)
        subtender_types = subtender_response.json() if subtender_response.status_code == 200 else []
        
        # Get regions for L1 data
        regions_response = requests.get(f"{BASE_URL}/mst/regions", headers=headers, timeout=10)
        regions = regions_response.json() if regions_response.status_code == 200 else []
        
        if not all([companies, services, subtender_types, regions]):
            print(f"❌ Missing master data: companies={len(companies)}, services={len(services)}, subtender={len(subtender_types)}, regions={len(regions)}")
            return
            
        print(f"✅ Master data retrieved: {len(companies)} companies, {len(services)} services, {len(subtender_types)} sub-tender types, {len(regions)} regions")
        
    except Exception as e:
        print(f"❌ Error getting master data: {e}")
        return
    
    # Step 3: Create leads and convert to opportunities, then progress stages
    test_cases = [
        {
            "project_title": "Healthcare Management System - L3 Testing",
            "description": "Testing opportunity at L3 Proposal stage",
            "target_stage": 3,
            "expected_revenue": 750000
        },
        {
            "project_title": "Financial Analytics Platform - L4 Testing", 
            "description": "Testing opportunity at L4 Technical Qualification stage",
            "target_stage": 4,
            "expected_revenue": 1200000
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i+2}. Creating and progressing opportunity: {test_case['project_title']}")
        
        try:
            # Create lead first
            lead_data = {
                "tender_type": "Tender",
                "billing_type": "Fixed Price",
                "sub_tender_type_id": subtender_types[0]["id"],
                "project_title": test_case["project_title"],
                "company_id": companies[0]["id"],
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website",
                "product_service_id": services[0]["id"],
                "expected_orc": test_case["expected_revenue"],
                "revenue": test_case["expected_revenue"],
                "lead_owner": user_id
            }
            
            # Create lead
            lead_response = requests.post(
                f"{BASE_URL}/leads",
                headers=headers,
                json=lead_data,
                timeout=10
            )
            
            if lead_response.status_code not in [200, 201]:
                print(f"   ❌ Failed to create lead: {lead_response.status_code}")
                continue
                
            lead_id = lead_response.json().get("id")
            print(f"   ✅ Created lead: {lead_id}")
            
            # Approve lead
            approval_response = requests.post(
                f"{BASE_URL}/leads/{lead_id}/status",
                headers=headers,
                json={"status": "approved"},
                timeout=10
            )
            
            if approval_response.status_code != 200:
                print(f"   ❌ Failed to approve lead: {approval_response.status_code}")
                continue
                
            print(f"   ✅ Lead approved")
            
            # Convert to opportunity
            convert_response = requests.post(
                f"{BASE_URL}/leads/{lead_id}/convert",
                headers=headers,
                params={"opportunity_date": "2024-01-20"},
                timeout=10
            )
            
            if convert_response.status_code != 200:
                print(f"   ❌ Failed to convert lead: {convert_response.status_code}")
                continue
                
            opportunity_id = convert_response.json().get("opportunity_id")
            print(f"   ✅ Converted to opportunity: {opportunity_id}")
            
            # Now progress through stages to reach target stage
            current_stage = 1
            target_stage = test_case["target_stage"]
            
            while current_stage < target_stage:
                next_stage = current_stage + 1
                print(f"   🔄 Progressing from L{current_stage} to L{next_stage}...")
                
                # Prepare stage data based on the stage
                stage_data = {}
                
                if current_stage == 1:  # L1 -> L2
                    stage_data = {
                        "region_id": regions[0]["id"],
                        "product_interest": test_case["description"],
                        "assigned_representatives": [user_id],
                        "lead_owner_id": user_id
                    }
                elif current_stage == 2:  # L2 -> L3
                    stage_data = {
                        "scorecard": "Qualified",
                        "budget": "Confirmed", 
                        "authority": "Decision maker identified",
                        "need": "Clear business need",
                        "timeline": "Q2 2024",
                        "qualification_status": "Qualified"
                    }
                elif current_stage == 3:  # L3 -> L4 
                    stage_data = {
                        "proposal_documents": ["test_proposal_document.pdf"],
                        "submission_date": "2024-01-25",
                        "internal_stakeholder_id": user_id,
                        "client_response": "Under review"
                    }
                
                # Make stage progression API call
                progression_data = {
                    "target_stage": next_stage,
                    "stage_data": stage_data
                }
                
                stage_response = requests.post(
                    f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                    headers=headers,
                    json=progression_data,
                    timeout=10
                )
                
                if stage_response.status_code == 200:
                    print(f"   ✅ Successfully progressed to L{next_stage}")
                    current_stage = next_stage
                else:
                    print(f"   ❌ Failed to progress to L{next_stage}: {stage_response.status_code} - {stage_response.text}")
                    break
            
            if current_stage == target_stage:
                print(f"   🎉 Successfully created opportunity at L{target_stage} stage!")
            else:
                print(f"   ⚠️ Opportunity ended at L{current_stage} instead of target L{target_stage}")
                
        except Exception as e:
            print(f"   ❌ Error creating test case {i}: {e}")
    
    # Step 4: Verify all opportunities
    print(f"\n{len(test_cases)+3}. Verifying final opportunity states...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            
            print(f"   Total opportunities: {len(opportunities)}")
            stage_distribution = {}
            
            for opp in opportunities:
                current_stage = opp.get("current_stage", 1)
                stage_key = f"L{current_stage}"
                stage_distribution[stage_key] = stage_distribution.get(stage_key, 0) + 1
                
                project_title = opp.get("project_title", "N/A")
                if "Testing" in project_title:
                    print(f"   📊 {opp.get('opportunity_id', 'N/A')}: {stage_key} - {project_title}")
            
            print(f"   📈 Stage Distribution: {dict(sorted(stage_distribution.items()))}")
            
        else:
            print(f"   ❌ Failed to get opportunities: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error verifying opportunities: {e}")
    
    print(f"\n✅ TEST OPPORTUNITY CREATION COMPLETED")
    print("   - Demonstrated multi-stage progression")
    print("   - Created opportunities at different stages")
    print("   - Ready for stage management frontend testing")

if __name__ == "__main__":
    create_test_opportunities()