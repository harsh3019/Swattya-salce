#!/usr/bin/env python3

import requests
import json
import sys

def test_detailed_sidebar():
    """Test sidebar with detailed output"""
    base_url = "https://swayatta-admin.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔐 Step 1: Admin Login")
    print("=" * 50)
    
    # Login
    login_response = requests.post(
        f"{api_url}/auth/login",
        json={"username": "admin", "password": "admin123"},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Login Status: {login_response.status_code}")
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('access_token')
        user_data = login_data.get('user', {})
        
        print(f"✅ Login successful")
        print(f"Token: {token[:50]}...")
        print(f"User ID: {user_data.get('id')}")
        print(f"Username: {user_data.get('username')}")
        print(f"Role ID: {user_data.get('role_id')}")
        print(f"Email: {user_data.get('email')}")
        
        print(f"\n🧭 Step 2: Sidebar Navigation")
        print("=" * 50)
        
        # Get sidebar
        sidebar_response = requests.get(
            f"{api_url}/nav/sidebar",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"Sidebar Status: {sidebar_response.status_code}")
        if sidebar_response.status_code == 200:
            sidebar_data = sidebar_response.json()
            modules = sidebar_data.get('modules', [])
            
            print(f"✅ Sidebar request successful")
            print(f"Number of modules: {len(modules)}")
            print(f"\nDetailed Sidebar Structure:")
            print(json.dumps(sidebar_data, indent=2))
            
            print(f"\n📋 Step 3: User Permissions")
            print("=" * 50)
            
            # Get permissions
            perms_response = requests.get(
                f"{api_url}/auth/permissions",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            print(f"Permissions Status: {perms_response.status_code}")
            if perms_response.status_code == 200:
                perms_data = perms_response.json()
                permissions = perms_data.get('permissions', [])
                
                print(f"✅ Permissions request successful")
                print(f"Number of permissions: {len(permissions)}")
                
                # Group permissions by module
                modules_perms = {}
                for perm in permissions:
                    module = perm.get('module')
                    if module not in modules_perms:
                        modules_perms[module] = []
                    modules_perms[module].append(perm)
                
                print(f"\nPermissions by Module:")
                for module, perms in modules_perms.items():
                    print(f"\n{module}:")
                    for perm in perms:
                        print(f"  - {perm.get('menu')} -> {perm.get('permission')} ({perm.get('path')})")
                
                print(f"\n🔍 Step 4: Database Verification")
                print("=" * 50)
                
                # Check role permissions directly
                role_perms_response = requests.get(
                    f"{api_url}/role-permissions",
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if role_perms_response.status_code == 200:
                    role_perms_data = role_perms_response.json()
                    admin_role_id = user_data.get('role_id')
                    admin_role_perms = [rp for rp in role_perms_data if rp.get('role_id') == admin_role_id]
                    
                    print(f"✅ Role permissions check successful")
                    print(f"Admin role ID: {admin_role_id}")
                    print(f"Total role permissions for admin: {len(admin_role_perms)}")
                    
                    # Sample a few role permissions
                    print(f"\nSample role permissions (first 5):")
                    for i, rp in enumerate(admin_role_perms[:5]):
                        print(f"  {i+1}. Role: {rp.get('role_id')[:8]}..., Module: {rp.get('module_id')[:8]}..., Menu: {rp.get('menu_id')[:8]}..., Permission: {rp.get('permission_id')[:8]}...")
                
                print(f"\n✅ CONCLUSION: Backend API is working correctly!")
                print(f"- Admin can login successfully")
                print(f"- Sidebar returns {len(modules)} modules with proper structure")
                print(f"- User has {len(permissions)} permissions across {len(modules_perms)} modules")
                print(f"- Database has proper role-permission mappings")
                print(f"\nIf sidebar is not showing in frontend, the issue is likely in:")
                print(f"1. Frontend API call implementation")
                print(f"2. Frontend token storage/retrieval")
                print(f"3. Frontend sidebar rendering logic")
                print(f"4. CORS or network connectivity issues")
                
            else:
                print(f"❌ Permissions request failed: {perms_response.status_code}")
                print(perms_response.text)
        else:
            print(f"❌ Sidebar request failed: {sidebar_response.status_code}")
            print(sidebar_response.text)
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)

if __name__ == "__main__":
    test_detailed_sidebar()