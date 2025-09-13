#!/usr/bin/env python3
"""
Debug Leads API and Create Test Data
"""

import requests
import json

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def debug_leads_and_create_opportunities():
    print("🔍 DEBUGGING LEADS AND CREATING TEST OPPORTUNITIES")
    print("=" * 55)
    
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
    
    # Step 2: Check existing leads
    print("\n2. Checking existing leads...")
    try:
        response = requests.get(
            f"{BASE_URL}/leads",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            leads_data = response.json()
            print(f"Leads response type: {type(leads_data)}")
            
            if isinstance(leads_data, dict):
                leads = leads_data.get('leads', [])
                total_leads = leads_data.get('total', 0)
                print(f"Total leads: {total_leads}")
                
                if leads:
                    print(f"First lead: {json.dumps(leads[0], indent=2, default=str)}")
                    
                    # Look for approved leads that can be converted
                    approved_leads = [lead for lead in leads if lead.get('status') == 'approved']
                    print(f"Approved leads: {len(approved_leads)}")
                    
                    if approved_leads:
                        # Try to convert first approved lead
                        lead_to_convert = approved_leads[0]
                        lead_id = lead_to_convert.get('id')
                        print(f"\n3. Converting lead {lead_id} to opportunity...")
                        
                        convert_response = requests.post(
                            f"{BASE_URL}/leads/{lead_id}/convert",
                            headers=headers,
                            params={"opportunity_date": "2024-01-15"},
                            timeout=10
                        )
                        
                        print(f"Conversion status: {convert_response.status_code}")
                        if convert_response.status_code == 200:
                            conversion_result = convert_response.json()
                            print(f"Conversion result: {json.dumps(conversion_result, indent=2, default=str)}")
                        else:
                            print(f"Conversion failed: {convert_response.text}")
                    
            else:
                print(f"Unexpected leads response: {leads_data}")
                
        else:
            print(f"❌ Failed to get leads: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting leads: {e}")
    
    # Step 3: Check opportunities again
    print("\n4. Checking opportunities after conversion...")
    try:
        response = requests.get(
            f"{BASE_URL}/opportunities",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            opportunities_data = response.json()
            opportunities = opportunities_data.get('opportunities', [])
            total_opps = opportunities_data.get('total', 0)
            
            print(f"Total opportunities: {total_opps}")
            
            if opportunities:
                print(f"First opportunity: {json.dumps(opportunities[0], indent=2, default=str)}")
                
                # Check current_stage values
                for i, opp in enumerate(opportunities[:3]):
                    current_stage = opp.get('current_stage')
                    opp_id = opp.get('opportunity_id') or opp.get('id')
                    project_title = opp.get('project_title', 'N/A')
                    print(f"Opportunity {i+1}: ID={opp_id}, Stage={current_stage}, Title={project_title}")
            
        else:
            print(f"❌ Failed to get opportunities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting opportunities: {e}")

if __name__ == "__main__":
    debug_leads_and_create_opportunities()