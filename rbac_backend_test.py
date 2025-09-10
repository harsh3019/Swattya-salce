#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class RBACSystemTester:
    def __init__(self, base_url="https://sawayatta-erp-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user = None

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
        """Test admin login with default credentials"""
        print("\n🔐 Testing Admin Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user = response.get('user', {})
            return self.log_test("Admin Login", True, f"Token received, User: {self.admin_user.get('username')}")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_rbac_initialization(self):
        """Test that RBAC system is properly initialized"""
        print("\n🏗️ Testing RBAC System Initialization...")
        
        # Test default permissions exist
        success, status, permissions = self.make_request('GET', 'permissions')
        if success:
            perm_names = [p['name'] for p in permissions]
            expected_perms = ['view', 'add', 'edit', 'delete']
            has_all_perms = all(perm in perm_names for perm in expected_perms)
            self.log_test("Default Permissions Created", has_all_perms, 
                         f"Found: {perm_names}, Expected: {expected_perms}")
        else:
            self.log_test("Default Permissions Created", False, f"Status: {status}")
        
        # Test default modules exist
        success, status, modules = self.make_request('GET', 'modules')
        if success:
            module_names = [m['name'] for m in modules]
            expected_modules = ['User Management', 'Sales', 'System']
            has_all_modules = all(mod in module_names for mod in expected_modules)
            self.log_test("Default Modules Created", has_all_modules,
                         f"Found: {module_names}, Expected: {expected_modules}")
        else:
            self.log_test("Default Modules Created", False, f"Status: {status}")
        
        # Test default menus exist
        success, status, menus = self.make_request('GET', 'menus')
        if success:
            menu_names = [m['name'] for m in menus]
            expected_menus = ['Users', 'Roles', 'Departments', 'Designations', 'Companies', 'Contacts']
            has_key_menus = all(menu in menu_names for menu in expected_menus)
            self.log_test("Default Menus Created", has_key_menus,
                         f"Found {len(menu_names)} menus including: {expected_menus}")
        else:
            self.log_test("Default Menus Created", False, f"Status: {status}")
        
        # Test Super Admin role exists
        success, status, roles = self.make_request('GET', 'roles')
        if success:
            role_names = [r['name'] for r in roles]
            has_super_admin = 'Super Admin' in role_names
            self.log_test("Super Admin Role Created", has_super_admin,
                         f"Found roles: {role_names}")
        else:
            self.log_test("Super Admin Role Created", False, f"Status: {status}")

    def test_sidebar_navigation(self):
        """Test dynamic sidebar navigation endpoint"""
        print("\n🧭 Testing Dynamic Sidebar Navigation...")
        
        success, status, response = self.make_request('GET', 'nav/sidebar')
        
        if success:
            modules = response.get('modules', [])
            self.log_test("Sidebar Navigation Endpoint", True, f"Found {len(modules)} accessible modules")
            
            # Check structure
            if modules:
                first_module = modules[0]
                has_required_fields = all(field in first_module for field in ['id', 'name', 'menus'])
                self.log_test("Sidebar Structure Valid", has_required_fields,
                             f"Module fields: {list(first_module.keys())}")
                
                # Check menus structure
                if 'menus' in first_module and first_module['menus']:
                    first_menu = first_module['menus'][0]
                    menu_has_fields = all(field in first_menu for field in ['id', 'name', 'path'])
                    self.log_test("Menu Structure Valid", menu_has_fields,
                                 f"Menu fields: {list(first_menu.keys())}")
                else:
                    self.log_test("Menu Structure Valid", False, "No menus found in module")
            else:
                self.log_test("Sidebar Structure Valid", False, "No modules returned")
        else:
            self.log_test("Sidebar Navigation Endpoint", False, f"Status: {status}, Response: {response}")

    def test_user_permissions_endpoint(self):
        """Test user permissions endpoint"""
        print("\n🔑 Testing User Permissions Endpoint...")
        
        success, status, response = self.make_request('GET', 'auth/permissions')
        
        if success:
            permissions = response.get('permissions', [])
            self.log_test("User Permissions Endpoint", True, f"Found {len(permissions)} permissions")
            
            # Check permission structure
            if permissions:
                first_perm = permissions[0]
                has_required_fields = all(field in first_perm for field in ['module', 'menu', 'permission', 'path'])
                self.log_test("Permission Structure Valid", has_required_fields,
                             f"Permission fields: {list(first_perm.keys())}")
                
                # Check if admin has all permission types
                perm_types = [p['permission'] for p in permissions]
                has_all_types = all(ptype in perm_types for ptype in ['view', 'add', 'edit', 'delete'])
                self.log_test("Admin Has All Permission Types", has_all_types,
                             f"Permission types: {set(perm_types)}")
            else:
                self.log_test("Permission Structure Valid", False, "No permissions found")
        else:
            self.log_test("User Permissions Endpoint", False, f"Status: {status}, Response: {response}")

    def test_permission_enforcement(self):
        """Test that permission enforcement works on CRUD operations"""
        print("\n🛡️ Testing Permission Enforcement...")
        
        # Test that admin can access protected endpoints
        protected_endpoints = [
            ('GET', 'users', 'Users List'),
            ('GET', 'roles', 'Roles List'),
            ('GET', 'departments', 'Departments List'),
            ('GET', 'designations', 'Designations List'),
            ('GET', 'permissions', 'Permissions List'),
            ('GET', 'modules', 'Modules List'),
            ('GET', 'menus', 'Menus List'),
            ('GET', 'role-permissions', 'Role-Permissions List')
        ]
        
        for method, endpoint, name in protected_endpoints:
            success, status, response = self.make_request(method, endpoint)
            self.log_test(f"Admin Access to {name}", success, f"Status: {status}")

    def test_rbac_crud_operations(self):
        """Test RBAC-specific CRUD operations"""
        print("\n🔧 Testing RBAC CRUD Operations...")
        
        # Test Permissions CRUD
        test_permission = {
            "name": f"test_perm_{datetime.now().strftime('%H%M%S')}",
            "description": "Test permission for RBAC testing",
            "status": "active"
        }
        
        success, status, response = self.make_request('POST', 'permissions', test_permission)
        if success:
            perm_id = response.get('id')
            self.log_test("Create Permission", True, f"Permission ID: {perm_id}")
            
            # Clean up
            self.make_request('DELETE', f'permissions/{perm_id}')
        else:
            self.log_test("Create Permission", False, f"Status: {status}, Response: {response}")
        
        # Test Modules CRUD
        test_module = {
            "name": f"Test Module {datetime.now().strftime('%H%M%S')}",
            "description": "Test module for RBAC testing",
            "status": "active"
        }
        
        success, status, response = self.make_request('POST', 'modules', test_module)
        if success:
            module_id = response.get('id')
            self.log_test("Create Module", True, f"Module ID: {module_id}")
            
            # Clean up
            self.make_request('DELETE', f'modules/{module_id}')
        else:
            self.log_test("Create Module", False, f"Status: {status}, Response: {response}")
        
        # Test Menus CRUD
        # First get a module ID
        success, status, modules = self.make_request('GET', 'modules')
        if success and modules:
            module_id = modules[0]['id']
            
            test_menu = {
                "name": f"Test Menu {datetime.now().strftime('%H%M%S')}",
                "path": f"/test-menu-{datetime.now().strftime('%H%M%S')}",
                "module_id": module_id,
                "order_index": 99
            }
            
            success, status, response = self.make_request('POST', 'menus', test_menu)
            if success:
                menu_id = response.get('id')
                self.log_test("Create Menu", True, f"Menu ID: {menu_id}")
                
                # Clean up
                self.make_request('DELETE', f'menus/{menu_id}')
            else:
                self.log_test("Create Menu", False, f"Status: {status}, Response: {response}")

    def test_role_permission_mappings(self):
        """Test role-permission mapping functionality"""
        print("\n🔗 Testing Role-Permission Mappings...")
        
        # Get existing data
        success, status, roles = self.make_request('GET', 'roles')
        if not success or not roles:
            self.log_test("Get Roles for Mapping", False, "No roles found")
            return
        
        success, status, permissions = self.make_request('GET', 'permissions')
        if not success or not permissions:
            self.log_test("Get Permissions for Mapping", False, "No permissions found")
            return
        
        success, status, modules = self.make_request('GET', 'modules')
        if not success or not modules:
            self.log_test("Get Modules for Mapping", False, "No modules found")
            return
        
        success, status, menus = self.make_request('GET', 'menus')
        if not success or not menus:
            self.log_test("Get Menus for Mapping", False, "No menus found")
            return
        
        # Test creating role-permission mapping
        role_id = roles[0]['id']
        permission_id = permissions[0]['id']
        module_id = modules[0]['id']
        menu_id = menus[0]['id']
        
        test_mapping = {
            "role_id": role_id,
            "module_id": module_id,
            "menu_id": menu_id,
            "permission_id": permission_id
        }
        
        success, status, response = self.make_request('POST', 'role-permissions', test_mapping)
        if success:
            mapping_id = response.get('id')
            self.log_test("Create Role-Permission Mapping", True, f"Mapping ID: {mapping_id}")
            
            # Test getting mappings
            success, status, mappings = self.make_request('GET', 'role-permissions')
            self.log_test("Get Role-Permission Mappings", success, f"Found {len(mappings) if success else 0} mappings")
            
            # Clean up
            self.make_request('DELETE', f'role-permissions/{mapping_id}')
        else:
            self.log_test("Create Role-Permission Mapping", False, f"Status: {status}, Response: {response}")

    def test_admin_user_setup(self):
        """Test that admin user is properly set up with Super Admin role"""
        print("\n👤 Testing Admin User Setup...")
        
        if not self.admin_user:
            self.log_test("Admin User Data Available", False, "No admin user data")
            return
        
        # Check admin user has role_id
        has_role = 'role_id' in self.admin_user and self.admin_user['role_id']
        self.log_test("Admin Has Role Assigned", has_role, f"Role ID: {self.admin_user.get('role_id')}")
        
        # Check admin user has department and designation
        has_dept = 'department_id' in self.admin_user and self.admin_user['department_id']
        has_desig = 'designation_id' in self.admin_user and self.admin_user['designation_id']
        self.log_test("Admin Has Department/Designation", has_dept and has_desig,
                     f"Dept: {self.admin_user.get('department_id')}, Desig: {self.admin_user.get('designation_id')}")

    def run_all_tests(self):
        """Run all RBAC system tests"""
        print("🚀 Starting RBAC System Backend Tests")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_admin_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all RBAC tests
        test_functions = [
            ("RBAC Initialization", self.test_rbac_initialization),
            ("Sidebar Navigation", self.test_sidebar_navigation),
            ("User Permissions Endpoint", self.test_user_permissions_endpoint),
            ("Permission Enforcement", self.test_permission_enforcement),
            ("RBAC CRUD Operations", self.test_rbac_crud_operations),
            ("Role-Permission Mappings", self.test_role_permission_mappings),
            ("Admin User Setup", self.test_admin_user_setup)
        ]
        
        test_results = []
        for test_name, test_func in test_functions:
            try:
                result = test_func()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {str(e)}")
                test_results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 RBAC SYSTEM TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 TEST MODULE RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = RBACSystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())