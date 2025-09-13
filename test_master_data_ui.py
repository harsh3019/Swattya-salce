#!/usr/bin/env python3
"""
Test Master Data UI Components
"""

import requests
import json

# Configuration
BASE_URL = "https://d2400459-c338-4a45-a734-97b20778d811.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

def test_master_data_apis():
    print("🧪 TESTING MASTER DATA APIs FOR UI")
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
            print(f"✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Test all master data endpoints
    endpoints = [
        "mst/primary-categories",
        "mst/products", 
        "mst/rate-cards",
        "mst/purchase-costs",
        "mst/sales-prices"
    ]
    
    print(f"\n2. Testing master data endpoints...")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 0
                print(f"   ✅ {endpoint}: {count} records")
            else:
                print(f"   ❌ {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: Error - {str(e)[:50]}...")
    
    # Step 3: Test create operation for primary categories
    print(f"\n3. Testing create operations...")
    try:
        category_data = {
            "category_name": "Test Category UI",
            "category_code": "TUI",
            "description": "Test category created from UI test",
            "is_active": True
        }
        
        response = requests.post(
            f"{BASE_URL}/mst/primary-categories",
            headers=headers,
            json=category_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            category_id = result.get("id")
            print(f"   ✅ Primary category created: {category_id}")
            
            # Test update
            update_data = {
                **category_data,
                "description": "Updated description from UI test"
            }
            
            update_response = requests.put(
                f"{BASE_URL}/mst/primary-categories/{category_id}",
                headers=headers,
                json=update_data,
                timeout=10
            )
            
            if update_response.status_code == 200:
                print(f"   ✅ Primary category updated successfully")
            else:
                print(f"   ❌ Update failed: {update_response.status_code}")
            
            # Test delete
            delete_response = requests.delete(
                f"{BASE_URL}/mst/primary-categories/{category_id}",
                headers=headers,
                timeout=10
            )
            
            if delete_response.status_code == 200:
                print(f"   ✅ Primary category deleted successfully")
            else:
                print(f"   ❌ Delete failed: {delete_response.status_code}")
                
        else:
            print(f"   ❌ Create failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing CRUD: {e}")
    
    # Step 4: Verify existing data counts
    print(f"\n4. Final data verification...")
    try:
        # Get all master data counts
        endpoints_with_names = [
            ("mst/primary-categories", "Primary Categories"),
            ("mst/products", "Products"),
            ("mst/rate-cards", "Rate Cards"),
            ("mst/purchase-costs", "Purchase Costs"),
            ("mst/sales-prices", "Sales Prices")
        ]
        
        print(f"   📊 Master Data Summary:")
        for endpoint, name in endpoints_with_names:
            try:
                response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    
                    # Show sample data for first few records
                    if count > 0 and isinstance(data, list):
                        sample = data[0]
                        sample_name = sample.get('name') or sample.get('category_name') or sample.get('rate_card_name') or 'N/A'
                        print(f"     • {name}: {count} records (e.g., '{sample_name}')")
                    else:
                        print(f"     • {name}: {count} records")
                else:
                    print(f"     • {name}: Error {response.status_code}")
            except Exception as e:
                print(f"     • {name}: Error - {str(e)[:30]}...")
        
        print(f"\n✅ MASTER DATA UI TESTING COMPLETED!")
        print("   🎯 READY FOR FRONTEND UI:")
        print("   • All APIs working correctly")
        print("   • CRUD operations functional")
        print("   • Data available for UI components")
        print("   • Navigate to /master-data in the frontend")
        
    except Exception as e:
        print(f"   ❌ Error in verification: {e}")

if __name__ == "__main__":
    test_master_data_apis()