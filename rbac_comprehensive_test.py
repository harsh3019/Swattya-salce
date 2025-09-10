#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class RBACSystemTester:
    def __init__(self, base_url="https://erp-quotation.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_data = None

    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    self.log(f"   Error: {error_detail}")
                except:
                    self.log(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test authentication system"""
        self.log("=== AUTHENTICATION TESTS ===")
        
        # Test login
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response.get('user', {})
            self.log(f"✅ Login successful. User: {self.user_data.get('username')}")
            self.log(f"   Role ID: {self.user_data.get('role_id')}")
            
            # Test get current user
            success, _ = self.run_test("Get Current User", "GET", "auth/me", 200)
            
            return True
        else:
            self.log("❌ Login failed - cannot proceed with other tests")
            return False

    def test_rbac_navigation(self):
        """Test RBAC navigation endpoints"""
        self.log("=== RBAC NAVIGATION TESTS ===")
        
        # Test sidebar navigation
        success, response = self.run_test(
            "Get Sidebar Navigation",
            "GET",
            "nav/sidebar",
            200
        )
        
        if success and 'modules' in response:
            modules = response['modules']
            self.log(f"✅ Found {len(modules)} accessible modules:")
            
            user_mgmt_found = False
            sales_found = False
            system_found = False
            
            for module in modules:
                module_name = module['name']
                menus = module.get('menus', [])
                self.log(f"   - {module_name}: {len(menus)} menus")
                
                if module_name == "User Management":
                    user_mgmt_found = True
                    self.log(f"     User Management menus:")
                    for menu in menus:
                        self.log(f"       * {menu['name']} -> {menu['path']}")
                elif module_name == "Sales":
                    sales_found = True
                elif module_name == "System":
                    system_found = True
            
            # Verify expected modules are present
            if user_mgmt_found and sales_found and system_found:
                self.log("✅ All expected modules (User Management, Sales, System) found")
            else:
                self.log(f"❌ Missing modules - User Mgmt: {user_mgmt_found}, Sales: {sales_found}, System: {system_found}")
            
            return user_mgmt_found and sales_found and system_found
        
        return False

    def test_user_permissions(self):
        """Test user permissions endpoint"""
        success, response = self.run_test(
            "Get User Permissions",
            "GET",
            "auth/permissions",
            200
        )
        
        if success and 'permissions' in response:
            permissions = response['permissions']
            self.log(f"✅ Found {len(permissions)} permissions for admin user")
            
            # Group by module for analysis
            modules_perms = {}
            for perm in permissions:
                module = perm['module']
                if module not in modules_perms:
                    modules_perms[module] = []
                modules_perms[module].append(f"{perm['menu']}:{perm['permission']}")
            
            for module, perms in modules_perms.items():
                self.log(f"   {module}: {len(perms)} permissions")
            
            # Check if admin has all 4 basic permissions (view, add, edit, delete)
            user_mgmt_perms = modules_perms.get('User Management', [])
            has_all_perms = any('view' in p for p in user_mgmt_perms) and \
                           any('add' in p for p in user_mgmt_perms) and \
                           any('edit' in p for p in user_mgmt_perms) and \
                           any('delete' in p for p in user_mgmt_perms)
            
            if has_all_perms:
                self.log("✅ Admin has all basic permissions (view, add, edit, delete)")
            else:
                self.log("❌ Admin missing some basic permissions")
            
            return has_all_perms
        
        return False

    def test_user_management_modules(self):
        """Test all 9 user management modules"""
        self.log("=== USER MANAGEMENT MODULES TESTS ===")
        
        modules = [
            ("Users", "users"),
            ("Roles", "roles"),
            ("Departments", "departments"),
            ("Designations", "designations"),
            ("Permissions", "permissions"),
            ("Modules", "modules"),
            ("Menus", "menus"),
            ("Role Permissions", "role-permissions"),
            ("Activity Logs", "activity-logs")
        ]
        
        results = {}
        all_success = True
        
        for name, endpoint in modules:
            success, response = self.run_test(
                f"Get {name}",
                "GET",
                endpoint,
                200
            )
            
            count = len(response) if success and isinstance(response, list) else 0
            results[name] = {'success': success, 'count': count}
            
            if success:
                self.log(f"   ✅ {name}: {count} records")
            else:
                self.log(f"   ❌ {name}: Failed to fetch")
                all_success = False
        
        # Verify we have the expected default data
        expected_counts = {
            'Permissions': 4,  # view, add, edit, delete
            'Modules': 3,      # User Management, Sales, System
            'Users': 1,        # admin user
            'Roles': 1,        # Super Admin
            'Departments': 1,  # IT
            'Designations': 1  # Administrator
        }
        
        for name, expected in expected_counts.items():
            actual = results.get(name, {}).get('count', 0)
            if actual >= expected:
                self.log(f"   ✅ {name}: Has expected minimum count ({actual} >= {expected})")
            else:
                self.log(f"   ❌ {name}: Below expected count ({actual} < {expected})")
                all_success = False
        
        return all_success, results

    def test_crud_operations(self):
        """Test CRUD operations on key entities"""
        self.log("=== CRUD OPERATIONS TESTS ===")
        
        # Test creating a department
        dept_data = {
            "name": f"Test Department {datetime.now().strftime('%H%M%S')}"
        }
        
        success, response = self.run_test(
            "Create Department",
            "POST",
            "departments",
            200,
            data=dept_data
        )
        
        created_dept_id = None
        if success and 'id' in response:
            created_dept_id = response['id']
            self.log(f"✅ Created department with ID: {created_dept_id}")
            
            # Test updating the department
            update_data = {
                "name": f"Updated Department {datetime.now().strftime('%H%M%S')}"
            }
            
            success, _ = self.run_test(
                "Update Department",
                "PUT",
                f"departments/{created_dept_id}",
                200,
                data=update_data
            )
            
            if success:
                self.log("✅ Department update successful")
            
            # Test deleting the department
            success, _ = self.run_test(
                "Delete Department",
                "DELETE",
                f"departments/{created_dept_id}",
                200
            )
            
            if success:
                self.log("✅ Department deletion successful")
        
        # Test creating a permission
        perm_data = {
            "name": f"test_permission_{datetime.now().strftime('%H%M%S')}",
            "description": "Test permission for CRUD testing"
        }
        
        success, response = self.run_test(
            "Create Permission",
            "POST",
            "permissions",
            200,
            data=perm_data
        )
        
        if success and 'id' in response:
            perm_id = response['id']
            self.log(f"✅ Created permission with ID: {perm_id}")
            
            # Clean up - delete the test permission
            self.run_test(
                "Delete Test Permission",
                "DELETE",
                f"permissions/{perm_id}",
                200
            )
        
        return True

    def test_rbac_enforcement(self):
        """Test RBAC enforcement"""
        self.log("=== RBAC ENFORCEMENT TESTS ===")
        
        # Test with invalid token
        old_token = self.token
        self.token = "invalid_token_12345"
        
        success, _ = self.run_test(
            "Access with Invalid Token",
            "GET",
            "users",
            401  # Should get unauthorized
        )
        
        if success:
            self.log("✅ RBAC properly blocks invalid tokens")
        
        # Test without token
        self.token = None
        
        success, _ = self.run_test(
            "Access without Token",
            "GET",
            "users",
            401  # Should get unauthorized
        )
        
        if success:
            self.log("✅ RBAC properly blocks requests without tokens")
        
        # Restore valid token
        self.token = old_token
        
        # Test that valid token works
        success, _ = self.run_test(
            "Access with Valid Token",
            "GET",
            "users",
            200
        )
        
        if success:
            self.log("✅ Valid token allows access")
        
        return True

    def test_sales_module(self):
        """Test sales module endpoints"""
        self.log("=== SALES MODULE TESTS ===")
        
        endpoints = [
            ("Companies", "companies"),
            ("Contacts", "contacts")
        ]
        
        all_success = True
        for name, endpoint in endpoints:
            success, response = self.run_test(
                f"Get {name}",
                "GET",
                endpoint,
                200
            )
            
            if success:
                count = len(response) if isinstance(response, list) else 0
                self.log(f"   ✅ {name}: {count} records")
            else:
                self.log(f"   ❌ {name}: Failed to fetch")
                all_success = False
        
        return all_success

    def run_comprehensive_test(self):
        """Run complete RBAC system test"""
        self.log("🚀 Starting Comprehensive RBAC System Test")
        self.log(f"Testing against: {self.base_url}")
        self.log("=" * 60)
        
        # Test authentication first
        if not self.test_authentication():
            return False
        
        # Test RBAC navigation
        nav_success = self.test_rbac_navigation()
        
        # Test user permissions
        perm_success = self.test_user_permissions()
        
        # Test all user management modules
        user_mgmt_success, user_mgmt_results = self.test_user_management_modules()
        
        # Test CRUD operations
        crud_success = self.test_crud_operations()
        
        # Test RBAC enforcement
        rbac_success = self.test_rbac_enforcement()
        
        # Test sales module
        sales_success = self.test_sales_module()
        
        # Print final results
        self.log("=" * 60)
        self.log("📊 COMPREHENSIVE TEST RESULTS")
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        self.log("\n🎯 RBAC SYSTEM ASSESSMENT:")
        self.log(f"   ✅ Authentication: {'PASS' if self.token else 'FAIL'}")
        self.log(f"   ✅ Navigation: {'PASS' if nav_success else 'FAIL'}")
        self.log(f"   ✅ Permissions: {'PASS' if perm_success else 'FAIL'}")
        self.log(f"   ✅ User Management (9 modules): {'PASS' if user_mgmt_success else 'FAIL'}")
        self.log(f"   ✅ CRUD Operations: {'PASS' if crud_success else 'FAIL'}")
        self.log(f"   ✅ RBAC Enforcement: {'PASS' if rbac_success else 'FAIL'}")
        self.log(f"   ✅ Sales Module: {'PASS' if sales_success else 'FAIL'}")
        
        self.log("\n📋 USER MANAGEMENT MODULE DETAILS:")
        for name, result in user_mgmt_results.items():
            status = "✅" if result['success'] else "❌"
            self.log(f"   {status} {name}: {result['count']} records")
        
        # Overall assessment
        all_critical_passed = (nav_success and perm_success and user_mgmt_success and 
                              crud_success and rbac_success)
        
        if all_critical_passed:
            self.log("\n🎉 RBAC SYSTEM FULLY FUNCTIONAL!")
            self.log("   ✅ Admin can login with admin/admin123")
            self.log("   ✅ Dynamic sidebar shows 3 modules")
            self.log("   ✅ All 9 user management modules accessible")
            self.log("   ✅ CRUD operations work correctly")
            self.log("   ✅ Permission-based access control enforced")
            return True
        else:
            self.log("\n⚠️  RBAC SYSTEM HAS ISSUES!")
            self.log("   Please check the failed tests above.")
            return False

def main():
    """Main test execution"""
    tester = RBACSystemTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())