#!/usr/bin/env python3
"""
Debug Opportunities API Response
"""

import requests
import json

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def debug_opportunities():
    print("🔍 DEBUGGING OPPORTUNITIES API")
    print("=" * 40)
    
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
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Get opportunities
    print("\n2. Getting opportunities...")
    try:
        response = requests.get(
            f"{BASE_URL}/opportunities",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            opportunities = response.json()
            print(f"Response Type: {type(opportunities)}")
            print(f"Response Length: {len(opportunities) if isinstance(opportunities, (list, dict)) else 'N/A'}")
            
            # Show first few characters of response
            response_text = response.text
            print(f"Response Preview (first 500 chars): {response_text[:500]}")
            
            if isinstance(opportunities, list):
                print(f"\n📋 OPPORTUNITIES LIST ANALYSIS:")
                print(f"Total opportunities: {len(opportunities)}")
                
                if opportunities:
                    first_opp = opportunities[0]
                    print(f"First opportunity type: {type(first_opp)}")
                    print(f"First opportunity keys: {list(first_opp.keys()) if isinstance(first_opp, dict) else 'N/A'}")
                    print(f"First opportunity: {json.dumps(first_opp, indent=2, default=str)}")
                    
                    # Check current_stage values
                    stage_values = []
                    for i, opp in enumerate(opportunities[:5]):  # First 5
                        if isinstance(opp, dict):
                            current_stage = opp.get('current_stage')
                            opp_id = opp.get('opportunity_id') or opp.get('id')
                            stage_values.append(f"Opp {i+1} (ID: {opp_id}): current_stage = {current_stage}")
                    
                    print(f"\n🎯 CURRENT STAGE VALUES:")
                    for stage_info in stage_values:
                        print(f"   {stage_info}")
                        
            elif isinstance(opportunities, dict):
                print(f"\n📋 OPPORTUNITIES DICT ANALYSIS:")
                print(f"Dict keys: {list(opportunities.keys())}")
                print(f"Full response: {json.dumps(opportunities, indent=2, default=str)}")
            
        else:
            print(f"❌ Failed to get opportunities: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting opportunities: {e}")

if __name__ == "__main__":
    debug_opportunities()