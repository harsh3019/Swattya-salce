#!/usr/bin/env python3
"""
Progress Existing Opportunity to L3 Stage
Take one of the L1 opportunities and progress it to L3 to demonstrate stage management
"""

import requests
import json

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def progress_opportunity():
    print("🔄 PROGRESSING OPPORTUNITY TO L3 STAGE")
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
            print(f"✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Get opportunities and find an L1 opportunity
    print("\n2. Finding L1 opportunity to progress...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            
            # Find an L1 opportunity
            l1_opportunity = None
            for opp in opportunities:
                if opp.get("current_stage") == 1:
                    l1_opportunity = opp
                    break
            
            if not l1_opportunity:
                print("❌ No L1 opportunities found to progress")
                return
                
            opportunity_id = l1_opportunity.get("id")
            project_title = l1_opportunity.get("project_title", "N/A")
            print(f"✅ Found L1 opportunity: {opportunity_id} - {project_title}")
            
        else:
            print(f"❌ Failed to get opportunities: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error getting opportunities: {e}")
        return
    
    # Step 3: Get regions for stage data
    print("\n3. Getting master data...")
    try:
        regions_response = requests.get(f"{BASE_URL}/mst/regions", headers=headers, timeout=10)
        regions = regions_response.json() if regions_response.status_code == 200 else []
        
        if not regions:
            print("❌ No regions found for stage data")
            return
            
        print(f"✅ Found {len(regions)} regions")
        
    except Exception as e:
        print(f"❌ Error getting regions: {e}")
        return
    
    # Step 4: Progress L1 -> L2
    print(f"\n4. Progressing {opportunity_id} from L1 to L2...")
    try:
        stage_data = {
            "target_stage": 2,
            "stage_data": {
                "region_id": regions[0]["id"],
                "product_interest": "Advanced CRM implementation with analytics",
                "assigned_representatives": [user_id],
                "lead_owner_id": user_id
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
            headers=headers,
            json=stage_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ L1->L2 Success: {result.get('message', 'Progressed to L2')}")
        else:
            print(f"❌ L1->L2 Failed: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error progressing L1->L2: {e}")
        return
    
    # Step 5: Progress L2 -> L3
    print(f"\n5. Progressing {opportunity_id} from L2 to L3...")
    try:
        stage_data = {
            "target_stage": 3,
            "stage_data": {
                "scorecard": "BANT Qualified - Budget confirmed, Authority identified, Need validated, Timeline Q2 2024",
                "budget": "₹500,000 - ₹750,000 approved",
                "authority": "CTO and CFO are decision makers",
                "need": "Current system lacks advanced analytics and integration capabilities",
                "timeline": "Implementation to start Q2 2024, go-live Q3 2024",
                "qualification_status": "Qualified"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
            headers=headers,
            json=stage_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ L2->L3 Success: {result.get('message', 'Progressed to L3')}")
        else:
            print(f"❌ L2->L3 Failed: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error progressing L2->L3: {e}")
        return
    
    # Step 6: Verify final stage
    print(f"\n6. Verifying final stage...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities/{opportunity_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            opportunity = response.json()
            current_stage = opportunity.get("current_stage")
            print(f"✅ Opportunity now at stage L{current_stage}")
            
            # Get updated opportunities list
            response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
                
                stage_distribution = {}
                for opp in opportunities:
                    current_stage = opp.get("current_stage", 1)
                    stage_key = f"L{current_stage}"
                    stage_distribution[stage_key] = stage_distribution.get(stage_key, 0) + 1
                
                print(f"📈 Updated Stage Distribution: {dict(sorted(stage_distribution.items()))}")
                
        else:
            print(f"❌ Failed to verify opportunity: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying opportunity: {e}")
    
    print(f"\n✅ OPPORTUNITY PROGRESSION COMPLETED")
    print("   - Successfully demonstrated L1->L2->L3 progression")
    print("   - Stage management system working correctly")
    print("   - Ready for frontend testing with opportunities at multiple stages")

if __name__ == "__main__":
    progress_opportunity()