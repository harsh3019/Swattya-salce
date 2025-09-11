#!/usr/bin/env python3
"""
Quick test to verify the opportunity data fix
"""

import requests
import json

# Configuration
BASE_URL = "https://crm-dashboard-45.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def test_fix():
    # Authenticate
    auth_response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS, timeout=10)
    if auth_response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test opportunities API
    opp_response = requests.get(f"{BASE_URL}/opportunities", headers=headers, timeout=10)
    if opp_response.status_code == 200:
        data = opp_response.json()
        opportunities = data.get('opportunities', [])
        total = data.get('total', 0)
        
        print(f"✅ Opportunities API working:")
        print(f"   - Total in response: {total}")
        print(f"   - Opportunities array length: {len(opportunities)}")
        print(f"   - Structure: {list(data.keys())}")
        
        if len(opportunities) == total and total > 0:
            print("✅ Data structure is consistent - fix should work!")
        else:
            print("❌ Data structure inconsistency detected")
    else:
        print(f"❌ Opportunities API failed: {opp_response.status_code}")
    
    # Test KPIs API
    kpi_response = requests.get(f"{BASE_URL}/opportunities/kpis", headers=headers, timeout=10)
    if kpi_response.status_code == 200:
        kpi_data = kpi_response.json()
        kpi_total = kpi_data.get('total', 0)
        
        print(f"✅ KPIs API working:")
        print(f"   - KPI Total: {kpi_total}")
        
        if kpi_total == total:
            print("✅ KPIs and Opportunities data are now consistent!")
        else:
            print(f"❌ Still inconsistent: KPIs={kpi_total}, Opportunities={total}")
    else:
        print(f"❌ KPIs API failed: {kpi_response.status_code}")

if __name__ == "__main__":
    test_fix()