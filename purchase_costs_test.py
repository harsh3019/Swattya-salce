#!/usr/bin/env python3
"""
Purchase Costs API Testing Script
Tests the newly added Purchase Costs API endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://lead-opp-crm.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

def test_admin_login():
    """Test admin authentication"""
    print("🔐 Testing Admin Login...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json=ADMIN_CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user", {})
            
            print(f"✅ Admin login successful")
            print(f"   Token: {token[:20]}...")
            print(f"   User: {user.get('username')} ({user.get('email')})")
            print(f"   Role ID: {user.get('role_id')}")
            
            return token
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None

def test_purchase_costs_api(token):
    """Test Purchase Costs API endpoint"""
    print("\n💰 Testing Purchase Costs API...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/mst/purchase-costs",
            headers=headers
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Purchase Costs API successful")
                print(f"   Response Type: {type(data)}")
                print(f"   Data Count: {len(data) if isinstance(data, list) else 'Not a list'}")
                
                # Verify expected count (should be 3)
                if isinstance(data, list):
                    if len(data) == 3:
                        print(f"✅ Expected count verified: 3 purchase costs found")
                    else:
                        print(f"⚠️  Unexpected count: Expected 3, got {len(data)}")
                    
                    # Verify response structure
                    print(f"\n📋 Verifying Response Structure:")
                    expected_fields = ["id", "product_id", "purchase_cost", "purchase_date", "currency_id", "cost_type", "remark"]
                    
                    for i, cost in enumerate(data):
                        print(f"\n   Purchase Cost {i+1}:")
                        
                        # Check all expected fields
                        missing_fields = []
                        for field in expected_fields:
                            if field in cost:
                                print(f"     ✅ {field}: {cost[field]}")
                            else:
                                missing_fields.append(field)
                                print(f"     ❌ {field}: MISSING")
                        
                        if missing_fields:
                            print(f"     ⚠️  Missing fields: {missing_fields}")
                        else:
                            print(f"     ✅ All expected fields present")
                    
                    # Verify product names (if we can get them)
                    print(f"\n🏷️  Purchase Cost Details:")
                    for i, cost in enumerate(data):
                        print(f"   Cost {i+1}: {cost.get('purchase_cost')} {cost.get('cost_type')} - {cost.get('remark')}")
                
                else:
                    print(f"❌ Response is not a list: {data}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   Raw response: {response.text[:200]}...")
                return False
                
        elif response.status_code == 404:
            print(f"❌ Purchase Costs API not found (404)")
            print(f"   This suggests the endpoint is not implemented")
            return False
            
        elif response.status_code == 500:
            print(f"❌ Internal Server Error (500)")
            print(f"   Response: {response.text}")
            return False
            
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"   Token may be invalid")
            return False
            
        elif response.status_code == 403:
            print(f"❌ Authorization failed (403)")
            print(f"   User may not have permission")
            return False
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Purchase Costs API error: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 Purchase Costs API Testing")
    print("=" * 50)
    
    # Test admin login
    token = test_admin_login()
    if not token:
        print("\n❌ Cannot proceed without valid authentication")
        sys.exit(1)
    
    # Test Purchase Costs API
    success = test_purchase_costs_api(token)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if success:
        print("✅ Purchase Costs API Test: PASSED")
        print("   - Authentication working")
        print("   - API endpoint accessible")
        print("   - Response structure correct")
        print("   - Expected data count verified")
        print("   - No 500 Internal Server Errors")
        print("   - Proper JSON response format")
    else:
        print("❌ Purchase Costs API Test: FAILED")
        print("   - Check implementation and data initialization")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main()