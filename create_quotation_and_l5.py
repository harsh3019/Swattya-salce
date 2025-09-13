#!/usr/bin/env python3
"""
Create Quotation and L5 Opportunity for Testing
"""

import requests
import json

# Configuration
BASE_URL = "https://d2400459-c338-4a45-a734-97b20778d811.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def create_quotation_and_l5():
    print("🔄 CREATING QUOTATION AND L5 OPPORTUNITY")
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
    print("\n2. Finding L4 opportunity...")
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
    
    # Step 3: Get rate cards
    print("\n3. Getting rate cards...")
    try:
        response = requests.get(f"{BASE_URL}/mst/rate-cards", headers=headers, timeout=10)
        if response.status_code == 200:
            rate_cards = response.json()
            if rate_cards:
                rate_card_id = rate_cards[0]["id"]
                print(f"✅ Found rate card: {rate_card_id}")
            else:
                print("❌ No rate cards found")
                return
        else:
            print(f"❌ Failed to get rate cards: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting rate cards: {e}")
        return
    
    # Step 4: Create quotation
    print(f"\n4. Creating quotation for opportunity...")
    try:
        quotation_data = {
            "quotation_name": "Test Quotation for L5 Testing",
            "rate_card_id": rate_card_id,
            "validity_date": "2024-12-31",
            "items": [
                {
                    "product_id": "test-product-1",
                    "product_name": "CRM System Implementation",
                    "qty": 1,
                    "unit": "License",
                    "sales_price": 500000,
                    "discount_percentage": 10,
                    "pricing_type": "one_time"
                },
                {
                    "product_id": "test-product-2", 
                    "product_name": "Training and Support",
                    "qty": 5,
                    "unit": "Days",
                    "sales_price": 25000,
                    "discount_percentage": 5,
                    "pricing_type": "one_time"
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/opportunities/{opportunity_id}/quotations",
            headers=headers,
            json=quotation_data,
            timeout=10
        )
        
        if response.status_code == 200:
            quotation = response.json()
            quotation_id = quotation.get("id")
            quotation_name = quotation.get("quotation_name")
            print(f"✅ Created quotation: {quotation_name}")
            print(f"   Quotation ID: {quotation_id}")
        else:
            print(f"❌ Failed to create quotation: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error creating quotation: {e}")
        return
    
    # Step 5: Progress L4 → L5 with quotation
    print(f"\n5. Progressing L4 to L5 with selected quotation...")
    try:
        stage_data = {
            "target_stage": 5,
            "stage_data": {
                "selected_quotation_id": quotation_id
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
                    print(f"   Associated Quotation: {quotation_name}")
                    print(f"   ✅ Ready for Won/Lost testing!")
                else:
                    print(f"⚠️ Unexpected stage: L{current_stage}")
            else:
                print(f"❌ Failed to verify progression: {verify_response.status_code}")
                
        else:
            print(f"❌ L4→L5 Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error progressing to L5: {e}")
    
    print(f"\n✅ QUOTATION AND L5 OPPORTUNITY CREATION COMPLETED")
    print("   🎯 Ready for Won/Lost flow testing!")

if __name__ == "__main__":
    create_quotation_and_l5()