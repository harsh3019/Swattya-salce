#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class SidebarFunctionalityTester:
    def __init__(self, base_url="https://erp-quotation.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user_data = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            return success, response.status_code, response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}
        except json.JSONDecodeError:
            return False, response.status_code, {"error": "Invalid JSON response"}

    def test_admin_login(self):
        """Test admin login functionality"""
        print("\n🔐 Testing Admin Login...")
        
        # Test login with admin credentials
        login_data = {"username": "admin", "password": "admin123"}
        success, status, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response and 'user' in response:
            self.token = response['access_token']
            self.admin_user_data = response['user']
            
            # Verify token format
            token_valid = len(self.token) > 50  # JWT tokens are typically longer
            
            # Verify user data structure
            user_has_id = 'id' in self.admin_user_data
            user_has_username = 'username' in self.admin_user_data
            user_has_role_id = 'role_id' in self.admin_user_data
            
            details = f"Token length: {len(self.token)}, User ID: {self.admin_user_data.get('id', 'N/A')}, Role ID: {self.admin_user_data.get('role_id', 'N/A')}"
            
            if token_valid and user_has_id and user_has_username and user_has_role_id:
                return self.log_test("Admin Login", True, details)
            else:
                return self.log_test("Admin Login", False, f"Missing required fields - {details}")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_sidebar_endpoint(self):
        """Test the sidebar navigation endpoint"""
        print("\n🧭 Testing Sidebar Navigation Endpoint...")
        
        success, status, response = self.make_request('GET', 'nav/sidebar')
        
        if success:
            modules = response.get('modules', [])
            
            if not modules:
                return self.log_test("Sidebar Navigation", False, "No modules returned in sidebar")
            
            # Analyze the structure
            total_modules = len(modules)
            total_menus = 0
            module_details = []
            
            expected_modules = ["User Management", "Sales"]
            found_modules = []
            
            for module in modules:
                module_name = module.get('name', 'Unknown')
                menus = module.get('menus', [])
                menu_count = len(menus)
                total_menus += menu_count
                
                module_details.append(f"{module_name} ({menu_count} menus)")
                
                if module_name in expected_modules:
                    found_modules.append(module_name)
                
                # Check menu structure
                for menu in menus:
                    if not all(key in menu for key in ['id', 'name', 'path']):
                        return self.log_test("Sidebar Navigation", False, 
                                           f"Menu missing required fields in {module_name}")
            
            details = f"Found {total_modules} modules, {total_menus} total menus. Modules: {', '.join(module_details)}"
            
            # Check if we have the expected core modules
            if len(found_modules) >= 1:  # At least one expected module
                return self.log_test("Sidebar Navigation", True, details)
            else:
                return self.log_test("Sidebar Navigation", False, 
                                   f"Missing expected modules. {details}")
        else:
            return self.log_test("Sidebar Navigation", False, f"Status: {status}, Response: {response}")

    def test_permissions_endpoint(self):
        """Test the user permissions endpoint"""
        print("\n🔑 Testing User Permissions Endpoint...")
        
        success, status, response = self.make_request('GET', 'auth/permissions')
        
        if success:
            permissions = response.get('permissions', [])
            
            if not permissions:
                return self.log_test("User Permissions", False, "No permissions returned")
            
            # Analyze permissions structure
            permission_count = len(permissions)
            modules_with_perms = set()
            view_permissions = 0
            
            for perm in permissions:
                if not all(key in perm for key in ['module', 'menu', 'permission', 'path']):
                    return self.log_test("User Permissions", False, 
                                       "Permission missing required fields")
                
                modules_with_perms.add(perm['module'])
                if perm['permission'] == 'View':
                    view_permissions += 1
            
            details = f"Found {permission_count} permissions across {len(modules_with_perms)} modules. View permissions: {view_permissions}"
            
            # Admin should have View permissions for multiple modules
            if view_permissions > 0 and len(modules_with_perms) > 0:
                return self.log_test("User Permissions", True, details)
            else:
                return self.log_test("User Permissions", False, 
                                   f"Insufficient permissions for admin user. {details}")
        else:
            return self.log_test("User Permissions", False, f"Status: {status}, Response: {response}")

    def verify_database_structure(self):
        """Verify database has required data for sidebar functionality"""
        print("\n🗄️ Testing Database Structure...")
        
        # Test if admin user exists and has proper role
        if not self.admin_user_data:
            return self.log_test("Database Structure", False, "No admin user data available")
        
        admin_role_id = self.admin_user_data.get('role_id')
        if not admin_role_id:
            return self.log_test("Database Structure", False, "Admin user has no role_id")
        
        # Check if roles exist
        success, status, roles_response = self.make_request('GET', 'roles')
        if not success:
            return self.log_test("Database Structure", False, f"Cannot fetch roles: {status}")
        
        roles = roles_response if isinstance(roles_response, list) else []
        admin_role = next((role for role in roles if role.get('id') == admin_role_id), None)
        
        if not admin_role:
            return self.log_test("Database Structure", False, f"Admin role {admin_role_id} not found")
        
        # Check if modules exist
        success, status, modules_response = self.make_request('GET', 'modules')
        if not success:
            return self.log_test("Database Structure", False, f"Cannot fetch modules: {status}")
        
        modules = modules_response if isinstance(modules_response, list) else []
        if not modules:
            return self.log_test("Database Structure", False, "No modules found in database")
        
        # Check if menus exist
        success, status, menus_response = self.make_request('GET', 'menus')
        if not success:
            return self.log_test("Database Structure", False, f"Cannot fetch menus: {status}")
        
        menus = menus_response if isinstance(menus_response, list) else []
        if not menus:
            return self.log_test("Database Structure", False, "No menus found in database")
        
        # Check if permissions exist
        success, status, permissions_response = self.make_request('GET', 'permissions')
        if not success:
            return self.log_test("Database Structure", False, f"Cannot fetch permissions: {status}")
        
        permissions = permissions_response if isinstance(permissions_response, list) else []
        if not permissions:
            return self.log_test("Database Structure", False, "No permissions found in database")
        
        # Check if role_permissions exist
        success, status, role_perms_response = self.make_request('GET', 'role-permissions')
        if not success:
            return self.log_test("Database Structure", False, f"Cannot fetch role-permissions: {status}")
        
        role_perms = role_perms_response if isinstance(role_perms_response, list) else []
        admin_role_perms = [rp for rp in role_perms if rp.get('role_id') == admin_role_id]
        
        details = f"Roles: {len(roles)}, Modules: {len(modules)}, Menus: {len(menus)}, Permissions: {len(permissions)}, Admin Role Perms: {len(admin_role_perms)}"
        
        if len(admin_role_perms) > 0:
            return self.log_test("Database Structure", True, details)
        else:
            return self.log_test("Database Structure", False, f"No role permissions for admin role. {details}")

    def test_specific_sidebar_issue(self):
        """Test the specific sidebar issue - admin login but no sidebar menus"""
        print("\n🔍 Testing Specific Sidebar Issue...")
        
        # Step 1: Verify admin can login
        if not self.token:
            return self.log_test("Sidebar Issue Analysis", False, "Admin login failed")
        
        # Step 2: Check if sidebar returns data
        success, status, sidebar_response = self.make_request('GET', 'nav/sidebar')
        if not success:
            return self.log_test("Sidebar Issue Analysis", False, f"Sidebar endpoint failed: {status}")
        
        modules = sidebar_response.get('modules', [])
        
        # Step 3: Analyze the issue
        if not modules:
            # No modules returned - this is the issue
            
            # Check if admin has role_id
            admin_role_id = self.admin_user_data.get('role_id')
            if not admin_role_id:
                return self.log_test("Sidebar Issue Analysis", False, 
                                   "ISSUE FOUND: Admin user has no role_id assigned")
            
            # Check if role_permissions exist for admin role
            success, status, role_perms_response = self.make_request('GET', 'role-permissions')
            if success:
                role_perms = role_perms_response if isinstance(role_perms_response, list) else []
                admin_role_perms = [rp for rp in role_perms if rp.get('role_id') == admin_role_id]
                
                if not admin_role_perms:
                    return self.log_test("Sidebar Issue Analysis", False, 
                                       f"ISSUE FOUND: No role_permissions exist for admin role {admin_role_id}")
                
                # Check if any of the role permissions have 'View' permission
                view_perms = []
                for rp in admin_role_perms:
                    perm_success, _, perm_response = self.make_request('GET', f'permissions')
                    if perm_success:
                        permissions = perm_response if isinstance(perm_response, list) else []
                        view_perm = next((p for p in permissions if p.get('id') == rp.get('permission_id') and p.get('name') == 'View'), None)
                        if view_perm:
                            view_perms.append(rp)
                
                if not view_perms:
                    return self.log_test("Sidebar Issue Analysis", False, 
                                       f"ISSUE FOUND: Admin role has {len(admin_role_perms)} permissions but none are 'View' permissions")
                else:
                    return self.log_test("Sidebar Issue Analysis", False, 
                                       f"ISSUE FOUND: Admin has {len(view_perms)} View permissions but sidebar still returns no modules. Possible sidebar logic issue.")
            else:
                return self.log_test("Sidebar Issue Analysis", False, 
                                   "Cannot fetch role_permissions to analyze issue")
        else:
            return self.log_test("Sidebar Issue Analysis", True, 
                               f"No issue found - sidebar returns {len(modules)} modules")

    def generate_curl_commands(self):
        """Generate curl commands for manual testing"""
        print("\n📋 CURL Commands for Manual Testing:")
        print("=" * 50)
        
        # Login command
        print("1. Admin Login:")
        login_curl = f'''curl -X POST "{self.api_url}/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "admin", "password": "admin123"}}\''''
        print(login_curl)
        
        if self.token:
            print(f"\n2. Sidebar Navigation (use token from login):")
            sidebar_curl = f'''curl -X GET "{self.api_url}/nav/sidebar" \\
  -H "Authorization: Bearer {self.token[:20]}..."'''
            print(sidebar_curl)
            
            print(f"\n3. User Permissions (use token from login):")
            perms_curl = f'''curl -X GET "{self.api_url}/auth/permissions" \\
  -H "Authorization: Bearer {self.token[:20]}..."'''
            print(perms_curl)

    def run_sidebar_tests(self):
        """Run all sidebar-related tests"""
        print("🚀 Starting Sidebar Functionality Tests")
        print("=" * 60)
        
        # Test 1: Admin Login
        login_success = self.test_admin_login()
        if not login_success:
            print("\n❌ Admin login failed. Cannot proceed with sidebar tests.")
            self.generate_curl_commands()
            return False
        
        # Test 2: Database Structure
        db_success = self.verify_database_structure()
        
        # Test 3: Sidebar Endpoint
        sidebar_success = self.test_sidebar_endpoint()
        
        # Test 4: Permissions Endpoint
        permissions_success = self.test_permissions_endpoint()
        
        # Test 5: Specific Issue Analysis
        issue_analysis = self.test_specific_sidebar_issue()
        
        # Generate curl commands for manual testing
        self.generate_curl_commands()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 SIDEBAR TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        test_results = [
            ("Admin Login", login_success),
            ("Database Structure", db_success),
            ("Sidebar Navigation", sidebar_success),
            ("User Permissions", permissions_success),
            ("Issue Analysis", issue_analysis)
        ]
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SidebarFunctionalityTester()
    success = tester.run_sidebar_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())