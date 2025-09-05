#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import os

class AuthSidebarTester:
    def __init__(self):
        # Get backend URL from frontend .env file
        try:
            with open('/app/frontend/.env', 'r') as f:
                env_content = f.read()
                for line in env_content.split('\n'):
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        backend_url = line.split('=', 1)[1]
                        break
                else:
                    backend_url = 'http://localhost:8001'
        except:
            backend_url = 'http://localhost:8001'
        
        # Fix the None issue if present or use internal URL for testing
        if 'None' in backend_url or not backend_url.startswith('http'):
            backend_url = 'http://localhost:8001'
        
        self.base_url = backend_url
        self.api_url = f"{backend_url}/api"
        self.token = None
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

            success = response.status_code == expected_status
            return success, response.status_code, response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}
        except json.JSONDecodeError:
            return False, response.status_code, {"error": "Invalid JSON response"}

    def test_admin_login(self):
        """Test POST /api/auth/login - Admin authentication"""
        print("\n🔐 Testing Admin Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response and 'user' in response:
            self.token = response['access_token']
            user_data = response['user']
            
            # Validate JWT token format (should be 3 parts separated by dots)
            token_parts = self.token.split('.')
            token_valid = len(token_parts) == 3
            
            # Validate user data structure
            has_user_id = 'id' in user_data
            has_username = 'username' in user_data
            has_email = 'email' in user_data
            has_role_id = 'role_id' in user_data
            
            details = f"Token format valid: {token_valid}, User ID: {user_data.get('id', 'N/A')}, Username: {user_data.get('username', 'N/A')}, Role ID: {user_data.get('role_id', 'N/A')}"
            
            return self.log_test("Admin Login", success and token_valid and has_user_id and has_username, details)
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_get_current_user(self):
        """Test GET /api/auth/me - Get current user info"""
        print("\n👤 Testing Get Current User...")
        
        if not self.token:
            return self.log_test("Get Current User", False, "No authentication token available")
        
        success, status, response = self.make_request('GET', 'auth/me')
        
        if success:
            # Validate user info structure
            has_id = 'id' in response
            has_username = 'username' in response
            has_email = 'email' in response
            has_role_id = 'role_id' in response
            no_password = 'password_hash' not in response
            
            details = f"User ID: {response.get('id', 'N/A')}, Username: {response.get('username', 'N/A')}, Password hidden: {no_password}"
            
            return self.log_test("Get Current User", success and has_id and has_username and no_password, details)
        else:
            return self.log_test("Get Current User", False, f"Status: {status}, Response: {response}")

    def test_get_user_permissions(self):
        """Test GET /api/auth/permissions - Get user permissions"""
        print("\n🔑 Testing Get User Permissions...")
        
        if not self.token:
            return self.log_test("Get User Permissions", False, "No authentication token available")
        
        success, status, response = self.make_request('GET', 'auth/permissions')
        
        if success and 'permissions' in response:
            permissions = response['permissions']
            permissions_count = len(permissions)
            
            # Validate permissions structure
            if permissions_count > 0:
                sample_perm = permissions[0]
                has_module = 'module' in sample_perm
                has_menu = 'menu' in sample_perm
                has_permission = 'permission' in sample_perm
                has_path = 'path' in sample_perm
                
                # Count permissions by type
                view_perms = len([p for p in permissions if p.get('permission') == 'View'])
                add_perms = len([p for p in permissions if p.get('permission') == 'Add'])
                edit_perms = len([p for p in permissions if p.get('permission') == 'Edit'])
                delete_perms = len([p for p in permissions if p.get('permission') == 'Delete'])
                export_perms = len([p for p in permissions if p.get('permission') == 'Export'])
                
                # Count modules
                modules = set(p.get('module') for p in permissions)
                modules_count = len(modules)
                
                details = f"Total: {permissions_count} permissions, Modules: {modules_count}, View: {view_perms}, Add: {add_perms}, Edit: {edit_perms}, Delete: {delete_perms}, Export: {export_perms}"
                
                # Expected: Admin should have around 70-75 permissions across 3 modules
                expected_total_min = 70
                expected_total_max = 75
                expected_modules = 3
                
                is_expected = expected_total_min <= permissions_count <= expected_total_max and modules_count == expected_modules
                
                return self.log_test("Get User Permissions", success and has_module and has_menu and has_permission, details)
            else:
                return self.log_test("Get User Permissions", False, "No permissions found")
        else:
            return self.log_test("Get User Permissions", False, f"Status: {status}, Response: {response}")

    def test_get_sidebar_navigation(self):
        """Test GET /api/nav/sidebar - Get sidebar navigation data"""
        print("\n🧭 Testing Get Sidebar Navigation...")
        
        if not self.token:
            return self.log_test("Get Sidebar Navigation", False, "No authentication token available")
        
        success, status, response = self.make_request('GET', 'nav/sidebar')
        
        if success and 'modules' in response:
            modules = response['modules']
            modules_count = len(modules)
            
            # Count total menus across all modules
            total_menus = 0
            module_details = []
            
            for module in modules:
                if 'menus' in module:
                    menus_count = len(module['menus'])
                    total_menus += menus_count
                    module_details.append(f"{module.get('name', 'Unknown')} ({menus_count} menus)")
                    
                    # Validate menu structure
                    if menus_count > 0:
                        sample_menu = module['menus'][0]
                        has_id = 'id' in sample_menu
                        has_name = 'name' in sample_menu
                        has_path = 'path' in sample_menu
                        has_order = 'order_index' in sample_menu
            
            details = f"Modules: {modules_count}, Total menus: {total_menus}, Details: {', '.join(module_details)}"
            
            # Expected: 3 modules with around 15 total menus (allow some flexibility)
            expected_modules = 3
            expected_menus_min = 14
            expected_menus_max = 16
            
            is_expected = modules_count == expected_modules and expected_menus_min <= total_menus <= expected_menus_max
            
            return self.log_test("Get Sidebar Navigation", success and is_expected, details)
        else:
            return self.log_test("Get Sidebar Navigation", False, f"Status: {status}, Response: {response}")

    def test_authentication_enforcement(self):
        """Test that all endpoints require proper authentication"""
        print("\n🔒 Testing Authentication Enforcement...")
        
        # Save current token
        original_token = self.token
        
        # Test without token
        self.token = None
        
        endpoints_to_test = [
            ('auth/me', 'GET'),
            ('auth/permissions', 'GET'),
            ('nav/sidebar', 'GET')
        ]
        
        all_protected = True
        results = []
        
        for endpoint, method in endpoints_to_test:
            success, status, response = self.make_request(method, endpoint, expected_status=401)
            is_protected = status == 401
            all_protected = all_protected and is_protected
            results.append(f"{endpoint}: {'Protected' if is_protected else f'Unprotected (Status: {status})'}")
        
        # Restore token
        self.token = original_token
        
        details = f"Endpoints tested: {', '.join(results)}"
        
        return self.log_test("Authentication Enforcement", all_protected, details)

    def run_auth_sidebar_tests(self):
        """Run authentication and sidebar specific tests"""
        print("🚀 Starting Sawayatta ERP Authentication & Sidebar API Tests")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        
        # Run tests in order
        test_results = []
        
        # 1. Test admin login
        login_success = self.test_admin_login()
        test_results.append(("Admin Login", login_success))
        
        if not login_success:
            print("\n❌ Authentication failed. Cannot proceed with authenticated tests.")
            return False
        
        # 2. Test authenticated endpoints
        test_results.append(("Get Current User", self.test_get_current_user()))
        test_results.append(("Get User Permissions", self.test_get_user_permissions()))
        test_results.append(("Get Sidebar Navigation", self.test_get_sidebar_navigation()))
        test_results.append(("Authentication Enforcement", self.test_authentication_enforcement()))
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        # Overall result
        all_passed = self.tests_passed == self.tests_run
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        
        return all_passed

def main():
    tester = AuthSidebarTester()
    success = tester.run_auth_sidebar_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())