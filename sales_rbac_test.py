#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class SalesRBACTester:
    def __init__(self, base_url="https://sawayatta-erp-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.sales_module_id = None
        self.companies_menu_id = None
        self.admin_role_id = None

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

    def test_login(self):
        """Test admin login"""
        print("\n🔐 Testing Admin Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return self.log_test("Admin Login", True, f"Token received")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_sales_module_exists(self):
        """Check if Sales module exists"""
        print("\n📦 Testing Sales Module Existence...")
        
        success, status, response = self.make_request('GET', 'modules')
        if not success:
            return self.log_test("Get Modules", False, f"Status: {status}")
        
        # Look for Sales module
        sales_module = None
        for module in response:
            if module.get('name') == 'Sales':
                sales_module = module
                self.sales_module_id = module['id']
                break
        
        if sales_module:
            return self.log_test("Sales Module Exists", True, f"Sales module found with ID: {self.sales_module_id}")
        else:
            return self.log_test("Sales Module Exists", False, "Sales module not found")

    def test_companies_menu_exists(self):
        """Check if Companies menu exists under Sales module"""
        print("\n📋 Testing Companies Menu Existence...")
        
        if not self.sales_module_id:
            return self.log_test("Companies Menu Check", False, "Sales module ID not available")
        
        success, status, response = self.make_request('GET', 'menus')
        if not success:
            return self.log_test("Get Menus", False, f"Status: {status}")
        
        # Look for Companies menu under Sales module
        companies_menu = None
        for menu in response:
            if (menu.get('name') == 'Companies' and 
                menu.get('module_id') == self.sales_module_id):
                companies_menu = menu
                self.companies_menu_id = menu['id']
                break
        
        if companies_menu:
            return self.log_test("Companies Menu Exists", True, 
                               f"Companies menu found with ID: {self.companies_menu_id}, Path: {companies_menu.get('path')}")
        else:
            return self.log_test("Companies Menu Exists", False, "Companies menu not found under Sales module")

    def create_companies_menu_if_missing(self):
        """Create Companies menu under Sales module if it doesn't exist"""
        print("\n➕ Creating Companies Menu...")
        
        if not self.sales_module_id:
            return self.log_test("Create Companies Menu", False, "Sales module ID not available")
        
        if self.companies_menu_id:
            return self.log_test("Create Companies Menu", True, "Companies menu already exists")
        
        # Create Companies menu
        menu_data = {
            "name": "Companies",
            "path": "/companies",
            "module_id": self.sales_module_id,
            "order_index": 1
        }
        
        success, status, response = self.make_request('POST', 'menus', menu_data)
        if success:
            self.companies_menu_id = response.get('id')
            return self.log_test("Create Companies Menu", True, f"Companies menu created with ID: {self.companies_menu_id}")
        else:
            return self.log_test("Create Companies Menu", False, f"Status: {status}, Response: {response}")

    def test_admin_role_exists(self):
        """Find the Admin role"""
        print("\n👑 Testing Admin Role Existence...")
        
        success, status, response = self.make_request('GET', 'roles')
        if not success:
            return self.log_test("Get Roles", False, f"Status: {status}")
        
        # Look for Admin role (could be "Admin", "Super Admin", etc.)
        admin_role = None
        for role in response:
            role_name = role.get('name', '').lower()
            if 'admin' in role_name or 'super' in role_name:
                admin_role = role
                self.admin_role_id = role['id']
                break
        
        if admin_role:
            return self.log_test("Admin Role Exists", True, 
                               f"Admin role found: {admin_role.get('name')} (ID: {self.admin_role_id})")
        else:
            return self.log_test("Admin Role Exists", False, "Admin role not found")

    def test_companies_permissions_exist(self):
        """Check if basic CRUD permissions exist for Companies"""
        print("\n🔑 Testing Companies Permissions...")
        
        success, status, response = self.make_request('GET', 'permissions')
        if not success:
            return self.log_test("Get Permissions", False, f"Status: {status}")
        
        # Check for standard CRUD permissions
        expected_permissions = ['View', 'Add', 'Edit', 'Delete', 'Export']
        found_permissions = {}
        
        for perm in response:
            perm_name = perm.get('name')
            if perm_name in expected_permissions:
                found_permissions[perm_name] = perm['id']
        
        missing_permissions = [p for p in expected_permissions if p not in found_permissions]
        
        if not missing_permissions:
            return self.log_test("Companies Permissions Exist", True, 
                               f"All required permissions found: {', '.join(expected_permissions)}")
        else:
            return self.log_test("Companies Permissions Exist", False, 
                               f"Missing permissions: {', '.join(missing_permissions)}")

    def test_admin_companies_permissions(self):
        """Check if Admin role has permissions for Companies menu"""
        print("\n🔒 Testing Admin Companies Permissions...")
        
        if not all([self.admin_role_id, self.sales_module_id, self.companies_menu_id]):
            return self.log_test("Admin Companies Permissions", False, 
                               "Required IDs not available (admin_role, sales_module, companies_menu)")
        
        # Get role permission matrix for admin role
        success, status, response = self.make_request('GET', f'role-permissions/matrix/{self.admin_role_id}')
        if not success:
            return self.log_test("Get Admin Permission Matrix", False, f"Status: {status}")
        
        # Find Sales module in the matrix
        sales_module_data = None
        for module in response.get('matrix', []):
            if module.get('module', {}).get('id') == self.sales_module_id:
                sales_module_data = module
                break
        
        if not sales_module_data:
            return self.log_test("Admin Companies Permissions", False, "Sales module not found in admin permissions")
        
        # Find Companies menu in the Sales module
        companies_menu_data = None
        for menu in sales_module_data.get('menus', []):
            if menu.get('id') == self.companies_menu_id:
                companies_menu_data = menu
                break
        
        if not companies_menu_data:
            return self.log_test("Admin Companies Permissions", False, "Companies menu not found in admin permissions")
        
        # Check permissions for Companies menu
        permissions = companies_menu_data.get('permissions', {})
        granted_permissions = [perm for perm, data in permissions.items() if data.get('granted', False)]
        
        expected_permissions = ['View', 'Add', 'Edit', 'Delete', 'Export']
        missing_permissions = [p for p in expected_permissions if p not in granted_permissions]
        
        if not missing_permissions:
            return self.log_test("Admin Companies Permissions", True, 
                               f"Admin has all required permissions: {', '.join(granted_permissions)}")
        else:
            return self.log_test("Admin Companies Permissions", False, 
                               f"Admin missing permissions: {', '.join(missing_permissions)}")

    def assign_companies_permissions_to_admin(self):
        """Assign all CRUD permissions for Companies to Admin role"""
        print("\n➕ Assigning Companies Permissions to Admin...")
        
        if not all([self.admin_role_id, self.sales_module_id, self.companies_menu_id]):
            return self.log_test("Assign Companies Permissions", False, 
                               "Required IDs not available")
        
        # Get all permissions
        success, status, permissions_response = self.make_request('GET', 'permissions')
        if not success:
            return self.log_test("Get Permissions for Assignment", False, f"Status: {status}")
        
        # Find permission IDs for CRUD operations
        permission_map = {}
        for perm in permissions_response:
            permission_map[perm.get('name')] = perm.get('id')
        
        expected_permissions = ['View', 'Add', 'Edit', 'Delete', 'Export']
        updates = []
        
        for perm_name in expected_permissions:
            if perm_name in permission_map:
                updates.append({
                    "menu_id": self.companies_menu_id,
                    "module_id": self.sales_module_id,
                    "permission_id": permission_map[perm_name],
                    "granted": True
                })
        
        if not updates:
            return self.log_test("Assign Companies Permissions", False, "No permissions to assign")
        
        # Update role permission matrix
        update_data = {"updates": updates}
        success, status, response = self.make_request('POST', f'role-permissions/matrix/{self.admin_role_id}', update_data)
        
        if success:
            return self.log_test("Assign Companies Permissions", True, 
                               f"Assigned {len(updates)} permissions to admin role")
        else:
            return self.log_test("Assign Companies Permissions", False, f"Status: {status}, Response: {response}")

    def test_sidebar_shows_companies(self):
        """Test that sidebar shows Companies menu under Sales module"""
        print("\n🧭 Testing Sidebar Shows Companies Menu...")
        
        success, status, response = self.make_request('GET', 'nav/sidebar')
        if not success:
            return self.log_test("Get Sidebar Navigation", False, f"Status: {status}")
        
        # Find Sales module in sidebar
        sales_module_in_sidebar = None
        for module in response.get('modules', []):
            if module.get('name') == 'Sales':
                sales_module_in_sidebar = module
                break
        
        if not sales_module_in_sidebar:
            return self.log_test("Sidebar Shows Companies", False, "Sales module not visible in sidebar")
        
        # Find Companies menu in Sales module
        companies_menu_in_sidebar = None
        for menu in sales_module_in_sidebar.get('menus', []):
            if menu.get('name') == 'Companies':
                companies_menu_in_sidebar = menu
                break
        
        if companies_menu_in_sidebar:
            return self.log_test("Sidebar Shows Companies", True, 
                               f"Companies menu visible in sidebar with path: {companies_menu_in_sidebar.get('path')}")
        else:
            return self.log_test("Sidebar Shows Companies", False, "Companies menu not visible in sidebar")

    def test_companies_api_access(self):
        """Test that admin can access company-related endpoints"""
        print("\n🏢 Testing Companies API Access...")
        
        # Test GET companies
        success, status, response = self.make_request('GET', 'companies')
        get_success = self.log_test("GET Companies API", success, 
                                  f"Status: {status}, Found {len(response) if success else 0} companies")
        
        # Test POST companies (create a test company)
        test_company = {
            "company_name": f"Test Company {datetime.now().strftime('%H%M%S')}",
            "company_type": "Private Limited",
            "account_type": "Customer",
            "region": "North America",
            "business_type": "Technology",
            "industry": "Software",
            "is_domestic": True,
            "address": "123 Test Street",
            "country": "USA",
            "state": "California",
            "city": "San Francisco",
            "zip_code": "94105"
        }
        
        success, status, response = self.make_request('POST', 'companies', test_company)
        if success:
            company_id = response.get('id')
            create_success = self.log_test("POST Companies API", True, f"Company created with ID: {company_id}")
            
            # Test GET specific company
            success, status, response = self.make_request('GET', f'companies/{company_id}')
            get_specific_success = self.log_test("GET Specific Company API", success, f"Status: {status}")
            
            return get_success and create_success and get_specific_success
        else:
            create_success = self.log_test("POST Companies API", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_company_add_route_access(self):
        """Test that /company/add route would be accessible (simulate frontend routing)"""
        print("\n🛣️ Testing Company Add Route Access...")
        
        # This simulates checking if the user has Add permission for Companies
        # In a real frontend, this would check the permission context
        success, status, response = self.make_request('GET', 'auth/permissions')
        if not success:
            return self.log_test("Get User Permissions for Route", False, f"Status: {status}")
        
        # Check if user has Add permission for Companies
        has_companies_add = False
        for perm in response.get('permissions', []):
            if (perm.get('menu') == 'Companies' and 
                perm.get('permission') == 'Add' and 
                perm.get('module') == 'Sales'):
                has_companies_add = True
                break
        
        if has_companies_add:
            return self.log_test("Company Add Route Access", True, 
                               "Admin has Add permission for Companies - /company/add route would be accessible")
        else:
            return self.log_test("Company Add Route Access", False, 
                               "Admin lacks Add permission for Companies - /company/add route would be blocked")

    def run_sales_rbac_tests(self):
        """Run all Sales RBAC tests"""
        print("🚀 Starting Sales Module RBAC Tests")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test existing structure
        test_results = []
        test_results.append(("Sales Module Exists", self.test_sales_module_exists()))
        test_results.append(("Companies Menu Exists", self.test_companies_menu_exists()))
        
        # Create missing components if needed
        if not self.companies_menu_id:
            test_results.append(("Create Companies Menu", self.create_companies_menu_if_missing()))
        
        test_results.append(("Admin Role Exists", self.test_admin_role_exists()))
        test_results.append(("Companies Permissions Exist", self.test_companies_permissions_exist()))
        test_results.append(("Admin Companies Permissions", self.test_admin_companies_permissions()))
        
        # Assign permissions if needed
        test_results.append(("Assign Companies Permissions", self.assign_companies_permissions_to_admin()))
        
        # Test functionality
        test_results.append(("Sidebar Shows Companies", self.test_sidebar_shows_companies()))
        test_results.append(("Companies API Access", self.test_companies_api_access()))
        test_results.append(("Company Add Route Access", self.test_company_add_route_access()))
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 SALES RBAC TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SalesRBACTester()
    success = tester.run_sales_rbac_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())