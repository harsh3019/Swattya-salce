#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class DebugTester:
    def __init__(self, base_url="https://lead-opp-crm.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        
    def login(self):
        """Login and get token"""
        response = requests.post(f"{self.api_url}/auth/login", 
                               json={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            self.token = response.json()['access_token']
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    
    def debug_role_crud(self):
        """Debug role CRUD operations step by step"""
        print("\n🔍 DEBUGGING ROLE CRUD OPERATIONS")
        print("="*50)
        
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        
        # Step 1: Create a role
        print("\n1️⃣ Creating a role...")
        role_data = {
            "name": f"Debug Role {datetime.now().strftime('%H%M%S')}",
            "code": f"DBG_{datetime.now().strftime('%H%M%S')}",
            "description": "Debug role for testing"
        }
        
        create_response = requests.post(f"{self.api_url}/roles", json=role_data, headers=headers)
        print(f"   CREATE Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            created_role = create_response.json()
            role_id = created_role.get('id')
            print(f"   ✅ Role created with ID: {role_id}")
            print(f"   📄 Created role data: {json.dumps(created_role, indent=2)}")
            
            # Step 2: Immediately try to get the role by ID
            print(f"\n2️⃣ Fetching role by ID: {role_id}")
            get_response = requests.get(f"{self.api_url}/roles", headers=headers)
            print(f"   GET all roles Status: {get_response.status_code}")
            
            if get_response.status_code == 200:
                all_roles = get_response.json()
                found_role = None
                for role in all_roles:
                    if role.get('id') == role_id:
                        found_role = role
                        break
                
                if found_role:
                    print(f"   ✅ Role found in GET all roles")
                    print(f"   📄 Found role data: {json.dumps(found_role, indent=2)}")
                else:
                    print(f"   ❌ Role NOT found in GET all roles")
                    print(f"   📄 Available role IDs: {[r.get('id') for r in all_roles]}")
            
            # Step 3: Wait a moment and try UPDATE
            print(f"\n3️⃣ Waiting 2 seconds before UPDATE...")
            time.sleep(2)
            
            update_data = {
                "name": f"Updated Debug Role {datetime.now().strftime('%H%M%S')}",
                "code": f"UPD_{datetime.now().strftime('%H%M%S')}",
                "description": "Updated debug role"
            }
            
            print(f"   Attempting UPDATE on role ID: {role_id}")
            update_response = requests.put(f"{self.api_url}/roles/{role_id}", json=update_data, headers=headers)
            print(f"   UPDATE Status: {update_response.status_code}")
            
            if update_response.status_code != 200:
                print(f"   ❌ UPDATE failed")
                print(f"   📄 Error response: {update_response.text}")
                
                # Check if role still exists
                get_response2 = requests.get(f"{self.api_url}/roles", headers=headers)
                if get_response2.status_code == 200:
                    all_roles2 = get_response2.json()
                    still_exists = any(r.get('id') == role_id for r in all_roles2)
                    print(f"   🔍 Role still exists in database: {still_exists}")
            else:
                print(f"   ✅ UPDATE successful")
                updated_role = update_response.json()
                print(f"   📄 Updated role data: {json.dumps(updated_role, indent=2)}")
            
            # Step 4: Try DELETE
            print(f"\n4️⃣ Attempting DELETE on role ID: {role_id}")
            delete_response = requests.delete(f"{self.api_url}/roles/{role_id}", headers=headers)
            print(f"   DELETE Status: {delete_response.status_code}")
            
            if delete_response.status_code != 200:
                print(f"   ❌ DELETE failed")
                print(f"   📄 Error response: {delete_response.text}")
            else:
                print(f"   ✅ DELETE successful")
                
        else:
            print(f"   ❌ Role creation failed")
            print(f"   📄 Error response: {create_response.text}")

    def debug_user_update_error(self):
        """Debug the specific user update error"""
        print("\n🔍 DEBUGGING USER UPDATE ERROR")
        print("="*50)
        
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        
        # Get existing roles, departments, designations
        roles_resp = requests.get(f"{self.api_url}/roles", headers=headers)
        depts_resp = requests.get(f"{self.api_url}/departments", headers=headers)
        desigs_resp = requests.get(f"{self.api_url}/designations", headers=headers)
        
        role_id = roles_resp.json()[0]['id'] if roles_resp.status_code == 200 and roles_resp.json() else None
        dept_id = depts_resp.json()[0]['id'] if depts_resp.status_code == 200 and depts_resp.json() else None
        desig_id = desigs_resp.json()[0]['id'] if desigs_resp.status_code == 200 and desigs_resp.json() else None
        
        # Create a user
        user_data = {
            "username": f"debuguser_{datetime.now().strftime('%H%M%S')}",
            "email": f"debug_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "DebugPass123!",
            "role_id": role_id,
            "department_id": dept_id,
            "designation_id": desig_id
        }
        
        print("1️⃣ Creating user...")
        create_response = requests.post(f"{self.api_url}/users", json=user_data, headers=headers)
        print(f"   CREATE Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            created_user = create_response.json()
            user_id = created_user.get('id')
            print(f"   ✅ User created with ID: {user_id}")
            print(f"   📄 Created user fields: {list(created_user.keys())}")
            
            # Try UPDATE with minimal data
            print("\n2️⃣ Attempting UPDATE with minimal data...")
            update_data = {
                "email": f"updated_debug_{datetime.now().strftime('%H%M%S')}@example.com"
            }
            
            update_response = requests.put(f"{self.api_url}/users/{user_id}", json=update_data, headers=headers)
            print(f"   UPDATE Status: {update_response.status_code}")
            
            if update_response.status_code != 200:
                print(f"   ❌ UPDATE failed")
                print(f"   📄 Error response: {update_response.text}")
            else:
                print(f"   ✅ UPDATE successful")
            
            # Clean up - delete user
            print("\n3️⃣ Cleaning up - deleting user...")
            delete_response = requests.delete(f"{self.api_url}/users/{user_id}", headers=headers)
            print(f"   DELETE Status: {delete_response.status_code}")

def main():
    tester = DebugTester()
    
    if not tester.login():
        return 1
    
    # Debug role CRUD operations
    tester.debug_role_crud()
    
    # Debug user update error
    tester.debug_user_update_error()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())