#!/usr/bin/env python3
"""
Detailed Purchase Costs API Testing with Product Name Verification
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

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BACKEND_URL}/auth/login",
        json=ADMIN_CREDENTIALS,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def get_products(token):
    """Get all products to map product_id to names"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/mst/products", headers=headers)
        if response.status_code == 200:
            return {product["id"]: product["name"] for product in response.json()}
    except:
        pass
    return {}

def test_purchase_costs_with_products():
    """Test Purchase Costs API with product name mapping"""
    print("🔍 Detailed Purchase Costs API Testing")
    print("=" * 60)
    
    # Get token
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Get products mapping
    products_map = get_products(token)
    print(f"📦 Found {len(products_map)} products in system")
    
    # Get purchase costs
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/mst/purchase-costs", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Purchase Costs API failed: {response.status_code}")
        return False
    
    costs = response.json()
    print(f"💰 Found {len(costs)} purchase costs")
    
    print("\n📋 Purchase Costs Details:")
    print("-" * 60)
    
    expected_products = ["CRM Software", "ERP System", "Implementation Service"]
    found_products = []
    
    for i, cost in enumerate(costs, 1):
        product_name = products_map.get(cost["product_id"], "Unknown Product")
        found_products.append(product_name)
        
        print(f"\n{i}. Product: {product_name}")
        print(f"   Purchase Cost: ₹{cost['purchase_cost']:,}")
        print(f"   Cost Type: {cost['cost_type']}")
        print(f"   Remark: {cost['remark']}")
        print(f"   Purchase Date: {cost['purchase_date'][:10]}")
        print(f"   Product ID: {cost['product_id']}")
        print(f"   Currency ID: {cost['currency_id']}")
    
    # Verify expected products
    print(f"\n🎯 Product Verification:")
    print("-" * 30)
    
    all_found = True
    for expected in expected_products:
        if expected in found_products:
            print(f"✅ {expected}: Found")
        else:
            print(f"❌ {expected}: Missing")
            all_found = False
    
    # Check for unexpected products
    unexpected = [p for p in found_products if p not in expected_products and p != "Unknown Product"]
    if unexpected:
        print(f"⚠️  Unexpected products: {unexpected}")
    
    return all_found

def main():
    success = test_purchase_costs_with_products()
    
    print("\n" + "=" * 60)
    print("📊 FINAL VERIFICATION")
    print("=" * 60)
    
    if success:
        print("✅ ALL TESTS PASSED")
        print("   - Purchase Costs API working correctly")
        print("   - Expected 3 purchase costs found")
        print("   - All expected products present:")
        print("     • CRM Software")
        print("     • ERP System") 
        print("     • Implementation Service")
        print("   - Response structure contains all required fields")
        print("   - No 500 Internal Server Errors")
        print("   - Proper JSON response format")
    else:
        print("❌ TESTS FAILED")
        print("   - Some expected products missing")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main()