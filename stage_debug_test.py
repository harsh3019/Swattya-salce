#!/usr/bin/env python3
"""
Stage Master Data Debug Test
Investigating the actual structure of stage master data
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "https://sawayatta-erp-2.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def debug_stage_data():
    """Debug the actual stage data structure"""
    session = requests.Session()
    
    # Authenticate
    print("🔐 Authenticating...")
    response = session.post(f"{API_BASE}/auth/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    data = response.json()
    auth_token = data.get("access_token")
    session.headers.update({
        "Authorization": f"Bearer {auth_token}"
    })
    print("✅ Authentication successful")
    
    # Get stage master data
    print("\n📋 Fetching stage master data...")
    response = session.get(f"{API_BASE}/mst/stages")
    
    if response.status_code != 200:
        print(f"❌ Failed to get stages: {response.status_code}")
        print(response.text)
        return
    
    stages = response.json()
    print(f"✅ Retrieved {len(stages)} stages")
    
    # Debug each stage
    print("\n🔍 STAGE DATA STRUCTURE ANALYSIS:")
    print("=" * 60)
    
    for i, stage in enumerate(stages, 1):
        print(f"\nStage {i}:")
        print(f"  Raw data: {json.dumps(stage, indent=2)}")
        print(f"  Keys: {list(stage.keys())}")
        
        # Check for different possible field names
        possible_code_fields = ['code', 'stage_code', 'stage_name', 'name']
        possible_name_fields = ['name', 'stage_name', 'description', 'title']
        
        print(f"  Possible code fields:")
        for field in possible_code_fields:
            if field in stage:
                print(f"    {field}: {stage[field]}")
        
        print(f"  Possible name fields:")
        for field in possible_name_fields:
            if field in stage:
                print(f"    {field}: {stage[field]}")
    
    # Test opportunities to see how they reference stages
    print("\n\n🎯 OPPORTUNITIES STAGE REFERENCE ANALYSIS:")
    print("=" * 60)
    
    response = session.get(f"{API_BASE}/opportunities")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and "opportunities" in data:
            opportunities = data["opportunities"]
        else:
            opportunities = data if isinstance(data, list) else []
        
        print(f"Found {len(opportunities)} opportunities")
        
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\nOpportunity {i}:")
            opp_id = opp.get("opportunity_id") or opp.get("id")
            print(f"  ID: {opp_id}")
            print(f"  Stage-related fields:")
            
            stage_fields = ['current_stage', 'stage_id', 'stage', 'stage_order']
            for field in stage_fields:
                if field in opp:
                    print(f"    {field}: {opp[field]}")
    else:
        print(f"❌ Failed to get opportunities: {response.status_code}")

if __name__ == "__main__":
    debug_stage_data()