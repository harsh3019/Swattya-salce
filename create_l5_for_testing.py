#!/usr/bin/env python3
"""
Create L5 Opportunity for Won/Lost Testing
"""

import requests
import json

# Configuration
BASE_URL = "https://d2400459-c338-4a45-a734-97b20778d811.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def create_l5_opportunity():
    print("🔄 CREATING L5 OPPORTUNITY FOR WON/LOST TESTING")
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
    
    # Step 2: Find L4 opportunity
    print("\n2. Finding L4 opportunity to progress to L5...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            
            l4_opportunities = [opp for opp in opportunities if opp.get("current_stage") == 4]
            
            if not l4_opportunities:
                print("❌ No L4 opportunities found")
                return
                
            opportunity = l4_opportunities[0]
            opportunity_id = opportunity.get("id")
            project_title = opportunity.get("project_title", "N/A")
            print(f"✅ Found L4 opportunity: {project_title}")
            
        else:
            print(f"❌ Failed to get opportunities: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error getting opportunities: {e}")
        return
    
    # Step 3: Progress L4 → L5
    print(f"\n3. Progressing {project_title[:30]}... from L4 to L5...")
    try:
        stage_data = {
            "target_stage": 5,
            "stage_data": {
                "technical_evaluation": "Technical requirements fully validated",
                "solution_approved": True,
                "technical_score": 95,
                "next_steps": "Proceed to commercial negotiation phase"
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
            print(f"✅ L4→L5 Success: {result.get('message', 'Progressed to L5')}")
            
            # Verify progression
            verify_response = requests.get(
                f"{BASE_URL}/opportunities/{opportunity_id}",
                headers=headers,
                timeout=10
            )
            
            if verify_response.status_code == 200:
                updated_opp = verify_response.json()
                current_stage = updated_opp.get("current_stage")
                print(f"✅ Verified: Now at L{current_stage}")
                
                if current_stage == 5:
                    print(f"🎉 L5 opportunity created successfully!")
                    print(f"   Opportunity ID: {opportunity_id}")
                    print(f"   Project: {project_title}")
                    print(f"   Ready for Won/Lost testing!")
                else:
                    print(f"⚠️ Unexpected stage: L{current_stage}")
            else:
                print(f"❌ Failed to verify progression: {verify_response.status_code}")
                
        else:
            print(f"❌ L4→L5 Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error progressing to L5: {e}")
    
    # Step 4: Show final state
    print(f"\n4. Current opportunities state...")
    try:
        response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
            
            stage_distribution = {}
            for opp in opportunities:
                current_stage = opp.get("current_stage", 1)
                stage_key = f"L{current_stage}"
                stage_distribution[stage_key] = stage_distribution.get(stage_key, 0) + 1
            
            print(f"   📈 Stage Distribution: {dict(sorted(stage_distribution.items()))}")
            
            l5_count = stage_distribution.get("L5", 0)
            if l5_count > 0:
                print(f"   ✅ Success: {l5_count} L5 opportunity(ies) ready for Won/Lost testing!")
            else:
                print(f"   ❌ No L5 opportunities created")
                
        else:
            print(f"   ❌ Failed to get final state: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error getting final state: {e}")
    
    print(f"\n✅ L5 OPPORTUNITY CREATION COMPLETED")
    print("   🎯 Next steps:")
    print("   1. Run the Won/Lost flow test")
    print("   2. Test the frontend L5 form with Won/Lost dropdown")
    print("   3. Verify automatic L6/L7 routing")

if __name__ == "__main__":
    create_l5_opportunity()