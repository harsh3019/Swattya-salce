#!/usr/bin/env python3
"""
Create Opportunities at Higher Stages (L4, L5, L6)
Ensure stage management works for ALL stages, not just L2/L3
"""

import requests
import json

# Configuration
BASE_URL = "https://d2400459-c338-4a45-a734-97b20778d811.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def create_higher_stage_opportunities():
    print("🏗️ CREATING OPPORTUNITIES AT HIGHER STAGES (L4, L5, L6)")
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
            print(f"✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Get existing L1 opportunities to progress
    print("\n2. Finding existing L1 opportunities to progress to higher stages...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            
            # Find L1 opportunities that we can progress
            l1_opportunities = [opp for opp in opportunities if opp.get("current_stage") == 1]
            
            if len(l1_opportunities) < 2:
                print(f"❌ Need at least 2 L1 opportunities, found {len(l1_opportunities)}")
                return
                
            print(f"✅ Found {len(l1_opportunities)} L1 opportunities to progress")
            
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
        print(f"✅ Found {len(regions)} regions")
        
    except Exception as e:
        print(f"❌ Error getting regions: {e}")
        return
    
    # Step 4: Progress opportunities to different stages
    target_stages = [
        {"stage": 4, "title": "L4 - Technical Qualification"},
        {"stage": 5, "title": "L5 - Commercial Negotiation"}
    ]
    
    for i, target_info in enumerate(target_stages):
        if i >= len(l1_opportunities):
            print(f"⚠️ Not enough L1 opportunities for {target_info['title']}")
            continue
            
        opportunity = l1_opportunities[i]
        opportunity_id = opportunity.get("id")
        project_title = opportunity.get("project_title", "N/A")
        target_stage = target_info["stage"]
        
        print(f"\n{i+4}. Progressing {project_title} to {target_info['title']}...")
        
        # Progress through each stage until target
        current_stage = 1
        success = True
        
        while current_stage < target_stage and success:
            next_stage = current_stage + 1
            print(f"   🔄 L{current_stage} → L{next_stage}")
            
            # Prepare stage-specific data
            stage_data = {}
            
            if current_stage == 1:  # L1 → L2
                stage_data = {
                    "region_id": regions[0]["id"],
                    "product_interest": f"Advanced system for {target_info['title']} testing",
                    "assigned_representatives": [user_id],
                    "lead_owner_id": user_id
                }
            elif current_stage == 2:  # L2 → L3
                stage_data = {
                    "scorecard": "BANT Qualified - All criteria met",
                    "budget": f"₹{500000 + (target_stage * 100000)} approved",
                    "authority": "CTO and CFO are decision makers",
                    "need": f"Business need validated for {target_info['title']}",
                    "timeline": "Q2 2024 implementation target",
                    "qualification_status": "Qualified"
                }
            elif current_stage == 3:  # L3 → L4
                stage_data = {
                    "proposal_documents": [f"proposal_{target_info['title'].replace(' ', '_').lower()}.pdf"],
                    "submission_date": "2024-01-25",
                    "internal_stakeholder_id": user_id,
                    "client_response": "Proposal approved, moving to technical evaluation"
                }
            elif current_stage == 4:  # L4 → L5
                stage_data = {
                    "selected_quotation_id": "test-quotation-id",  # Will need to handle missing quotation
                    "technical_notes": f"Technical evaluation completed for {target_info['title']}"
                }
            
            # Make progression API call
            progression_data = {
                "target_stage": next_stage,
                "stage_data": stage_data
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                    headers=headers,
                    json=progression_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ {result.get('message', f'Progressed to L{next_stage}')}")
                    current_stage = next_stage
                else:
                    print(f"   ❌ Failed L{current_stage}→L{next_stage}: {response.status_code}")
                    if response.status_code == 400:
                        error_detail = response.json()
                        print(f"      Error: {error_detail}")
                    success = False
                    
            except Exception as e:
                print(f"   ❌ Error progressing L{current_stage}→L{next_stage}: {e}")
                success = False
        
        if current_stage == target_stage:
            print(f"   🎉 Successfully created opportunity at {target_info['title']}!")
        else:
            print(f"   ⚠️ Stopped at L{current_stage} instead of target L{target_stage}")
    
    # Step 5: Create one L6 (Won) opportunity manually if possible
    print(f"\n{len(target_stages)+4}. Attempting to create L6 (Won) opportunity...")
    try:
        # Find any opportunity at L5 or create one at L6 directly
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            l5_opportunities = [opp for opp in opportunities if opp.get("current_stage") == 5]
            
            if l5_opportunities:
                opp = l5_opportunities[0]
                opportunity_id = opp.get("id")
                print(f"   Found L5 opportunity to progress to L6: {opp.get('project_title', 'N/A')}")
                
                # Progress L5 → L6 (Won)
                stage_data = {
                    "updated_price": 800000,
                    "margin": 25.0,
                    "cpc_overhead": 15.0,
                    "po_number": "PO-2024-001",
                    "po_date": "2024-01-30",
                    "won_reason": "Best technical solution and competitive pricing"
                }
                
                progression_data = {
                    "target_stage": 6,
                    "stage_data": stage_data
                }
                
                response = requests.post(
                    f"{BASE_URL}/opportunities/{opportunity_id}/change-stage",
                    headers=headers,
                    json=progression_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Successfully created L6 (Won) opportunity!")
                else:
                    print(f"   ❌ Failed to create L6: {response.status_code}")
            else:
                print(f"   ⚠️ No L5 opportunities found to progress to L6")
                
    except Exception as e:
        print(f"   ❌ Error creating L6 opportunity: {e}")
    
    # Step 6: Verify final stage distribution
    print(f"\n{len(target_stages)+5}. Verifying final stage distribution...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            
            stage_distribution = {}
            print(f"   📊 Current Opportunities by Stage:")
            
            for opp in opportunities:
                current_stage = opp.get("current_stage", 1)
                stage_key = f"L{current_stage}"
                stage_distribution[stage_key] = stage_distribution.get(stage_key, 0) + 1
                
                opp_id = opp.get("opportunity_id", opp.get("id", "N/A"))
                project_title = opp.get("project_title", "N/A")[:40] + "..." if len(opp.get("project_title", "")) > 40 else opp.get("project_title", "N/A")
                print(f"   • {stage_key}: {opp_id} - {project_title}")
            
            print(f"\n   📈 Stage Distribution Summary: {dict(sorted(stage_distribution.items()))}")
            
            # Check if we have good coverage
            stages_with_data = len(stage_distribution.keys())
            if stages_with_data >= 4:
                print(f"   ✅ Excellent coverage: {stages_with_data} different stages for testing")
            else:
                print(f"   ⚠️ Limited coverage: {stages_with_data} different stages")
                
        else:
            print(f"   ❌ Failed to verify opportunities: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error verifying opportunities: {e}")
    
    print(f"\n✅ HIGHER STAGE OPPORTUNITIES CREATION COMPLETED")
    print("   🎯 TESTING COVERAGE:")
    print("   • Multiple opportunities at different stages (L1, L2, L3, L4+)")
    print("   • Ready to test 'Manage Stages' opens at correct current stage")
    print("   • Can verify stage management works for ALL stages, not just L2")
    print("\n   📋 TEST SCENARIOS:")
    print("   1. Click 'Manage Stages' on L1 opportunity → Should open at L1")
    print("   2. Click 'Manage Stages' on L2 opportunity → Should open at L2") 
    print("   3. Click 'Manage Stages' on L3 opportunity → Should open at L3")
    print("   4. Click 'Manage Stages' on L4+ opportunity → Should open at L4+")
    print("   5. Test stage progression from each current stage")

if __name__ == "__main__":
    create_higher_stage_opportunities()