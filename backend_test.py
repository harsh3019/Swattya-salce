#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class SawayattaERPTester:
    def __init__(self, base_url="https://sawayatta-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {}  # Track created items for cleanup

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
        """Test login functionality"""
        print("\n🔐 Testing Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return self.log_test("Admin Login", True, f"Token received")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_users_crud(self):
        """Test Users CRUD operations"""
        print("\n👥 Testing Users CRUD...")
        
        # First get roles, departments, designations for user creation
        roles_success, _, roles_data = self.make_request('GET', 'roles')
        depts_success, _, depts_data = self.make_request('GET', 'departments')
        desigs_success, _, desigs_data = self.make_request('GET', 'designations')
        
        role_id = roles_data[0]['id'] if roles_success and roles_data else None
        dept_id = depts_data[0]['id'] if depts_success and depts_data else None
        desig_id = desigs_data[0]['id'] if desigs_success and desigs_data else None
        
        # Test GET users
        success, status, response = self.make_request('GET', 'users')
        get_success = self.log_test("GET Users", success, f"Found {len(response) if success else 0} users")
        
        # Check if users have Role, Department, Designation columns
        if success and response:
            user = response[0] if response else {}
            has_role = 'role_id' in user
            has_dept = 'department_id' in user
            has_desig = 'designation_id' in user
            self.log_test("Users have Role/Dept/Designation columns", 
                         has_role and has_dept and has_desig,
                         f"Role: {has_role}, Dept: {has_dept}, Desig: {has_desig}")
        
        # Test CREATE user
        test_user = {
            "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!",
            "role_id": role_id,
            "department_id": dept_id,
            "designation_id": desig_id
        }
        
        success, status, response = self.make_request('POST', 'users', test_user, 200)
        if success:
            user_id = response.get('id')
            self.created_items['user_id'] = user_id
            create_success = self.log_test("CREATE User", True, f"User ID: {user_id}")
            
            # Test UPDATE user
            update_data = {
                "email": f"updated_{datetime.now().strftime('%H%M%S')}@example.com",
                "status": "active"
            }
            success, status, response = self.make_request('PUT', f'users/{user_id}', update_data)
            update_success = self.log_test("UPDATE User", success, f"Status: {status}")
            
            # Test DELETE user
            success, status, response = self.make_request('DELETE', f'users/{user_id}')
            delete_success = self.log_test("DELETE User", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            self.log_test("CREATE User", False, f"Status: {status}, Response: {response}")
            return get_success

    def test_roles_crud(self):
        """Test Roles CRUD operations with new code field"""
        print("\n🎭 Testing Roles CRUD...")
        
        # Test GET roles
        success, status, response = self.make_request('GET', 'roles')
        get_success = self.log_test("GET Roles", success, f"Found {len(response) if success else 0} roles")
        
        # Check if roles have code field
        if success and response:
            role = response[0] if response else {}
            has_code = 'code' in role
            self.log_test("Roles have Code field", has_code, f"Code field present: {has_code}")
        
        # Test CREATE role with code field
        test_role = {
            "name": f"Test Role {datetime.now().strftime('%H%M%S')}",
            "code": f"TEST_{datetime.now().strftime('%H%M%S')}",
            "description": "Test role for CRUD testing"
        }
        
        success, status, response = self.make_request('POST', 'roles', test_role, 200)
        if success:
            role_id = response.get('id')
            self.created_items['role_id'] = role_id
            
            # Check if code field is present in response
            has_code = 'code' in response
            create_success = self.log_test("CREATE Role with Code", success and has_code, 
                         f"Role ID: {role_id}, Has Code: {has_code}")
            
            # Test UPDATE role
            update_data = {
                "name": f"Updated Role {datetime.now().strftime('%H%M%S')}",
                "code": f"UPD_{datetime.now().strftime('%H%M%S')}",
                "description": "Updated description"
            }
            success, status, response = self.make_request('PUT', f'roles/{role_id}', update_data)
            update_success = self.log_test("UPDATE Role", success, f"Status: {status}")
            
            # Test DELETE role
            success, status, response = self.make_request('DELETE', f'roles/{role_id}')
            delete_success = self.log_test("DELETE Role", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Role", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_departments_crud(self):
        """Test Departments CRUD operations"""
        print("\n🏢 Testing Departments CRUD...")
        
        # Test GET departments
        success, status, response = self.make_request('GET', 'departments')
        get_success = self.log_test("GET Departments", success, f"Found {len(response) if success else 0} departments")
        
        # Test CREATE department
        test_dept = {
            "name": f"Test Department {datetime.now().strftime('%H%M%S')}"
        }
        
        success, status, response = self.make_request('POST', 'departments', test_dept, 200)
        if success:
            dept_id = response.get('id')
            self.created_items['dept_id'] = dept_id
            create_success = self.log_test("CREATE Department", True, f"Department ID: {dept_id}")
            
            # Test UPDATE department
            update_data = {
                "name": f"Updated Department {datetime.now().strftime('%H%M%S')}"
            }
            success, status, response = self.make_request('PUT', f'departments/{dept_id}', update_data)
            update_success = self.log_test("UPDATE Department", success, f"Status: {status}")
            
            # Test DELETE department
            success, status, response = self.make_request('DELETE', f'departments/{dept_id}')
            delete_success = self.log_test("DELETE Department", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Department", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_designations_crud(self):
        """Test Designations CRUD operations"""
        print("\n💼 Testing Designations CRUD...")
        
        # Test GET designations
        success, status, response = self.make_request('GET', 'designations')
        get_success = self.log_test("GET Designations", success, f"Found {len(response) if success else 0} designations")
        
        # Test CREATE designation
        test_desig = {
            "name": f"Test Designation {datetime.now().strftime('%H%M%S')}"
        }
        
        success, status, response = self.make_request('POST', 'designations', test_desig, 200)
        if success:
            desig_id = response.get('id')
            self.created_items['desig_id'] = desig_id
            create_success = self.log_test("CREATE Designation", True, f"Designation ID: {desig_id}")
            
            # Test UPDATE designation
            update_data = {
                "name": f"Updated Designation {datetime.now().strftime('%H%M%S')}"
            }
            success, status, response = self.make_request('PUT', f'designations/{desig_id}', update_data)
            update_success = self.log_test("UPDATE Designation", success, f"Status: {status}")
            
            # Test DELETE designation
            success, status, response = self.make_request('DELETE', f'designations/{desig_id}')
            delete_success = self.log_test("DELETE Designation", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Designation", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_permissions_crud(self):
        """Test Permissions CRUD operations"""
        print("\n🔑 Testing Permissions CRUD...")
        
        # First get modules for permission creation
        modules_success, _, modules_data = self.make_request('GET', 'modules')
        module_id = modules_data[0]['id'] if modules_success and modules_data else str(uuid.uuid4())
        
        # Test GET permissions
        success, status, response = self.make_request('GET', 'permissions')
        get_success = self.log_test("GET Permissions", success, f"Found {len(response) if success else 0} permissions")
        
        # Test CREATE permission
        test_perm = {
            "key": f"test_permission_{datetime.now().strftime('%H%M%S')}",
            "label": f"Test Permission {datetime.now().strftime('%H%M%S')}",
            "module_id": module_id
        }
        
        success, status, response = self.make_request('POST', 'permissions', test_perm, 200)
        if success:
            perm_id = response.get('id')
            self.created_items['perm_id'] = perm_id
            create_success = self.log_test("CREATE Permission", True, f"Permission ID: {perm_id}")
            
            # Test UPDATE permission
            update_data = {
                "key": f"updated_permission_{datetime.now().strftime('%H%M%S')}",
                "label": f"Updated Permission {datetime.now().strftime('%H%M%S')}",
                "module_id": module_id
            }
            success, status, response = self.make_request('PUT', f'permissions/{perm_id}', update_data)
            update_success = self.log_test("UPDATE Permission", success, f"Status: {status}")
            
            # Test DELETE permission
            success, status, response = self.make_request('DELETE', f'permissions/{perm_id}')
            delete_success = self.log_test("DELETE Permission", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Permission", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_modules_crud(self):
        """Test Modules CRUD operations"""
        print("\n📦 Testing Modules CRUD...")
        
        # Test GET modules
        success, status, response = self.make_request('GET', 'modules')
        get_success = self.log_test("GET Modules", success, f"Found {len(response) if success else 0} modules")
        
        # Test CREATE module
        test_module = {
            "name": f"Test Module {datetime.now().strftime('%H%M%S')}",
            "description": "Test module for CRUD testing"
        }
        
        success, status, response = self.make_request('POST', 'modules', test_module, 200)
        if success:
            module_id = response.get('id')
            self.created_items['module_id'] = module_id
            create_success = self.log_test("CREATE Module", True, f"Module ID: {module_id}")
            
            # Test UPDATE module
            update_data = {
                "name": f"Updated Module {datetime.now().strftime('%H%M%S')}",
                "description": "Updated description"
            }
            success, status, response = self.make_request('PUT', f'modules/{module_id}', update_data)
            update_success = self.log_test("UPDATE Module", success, f"Status: {status}")
            
            # Test DELETE module
            success, status, response = self.make_request('DELETE', f'modules/{module_id}')
            delete_success = self.log_test("DELETE Module", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Module", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_menus_crud(self):
        """Test Menus CRUD operations"""
        print("\n📋 Testing Menus CRUD...")
        
        # First get modules for menu creation
        modules_success, _, modules_data = self.make_request('GET', 'modules')
        module_id = modules_data[0]['id'] if modules_success and modules_data else str(uuid.uuid4())
        
        # Test GET menus
        success, status, response = self.make_request('GET', 'menus')
        get_success = self.log_test("GET Menus", success, f"Found {len(response) if success else 0} menus")
        
        # Test CREATE menu
        test_menu = {
            "name": f"Test Menu {datetime.now().strftime('%H%M%S')}",
            "module_id": module_id,
            "route_path": f"/test-menu-{datetime.now().strftime('%H%M%S')}",
            "icon": "test-icon",
            "order_index": 1
        }
        
        success, status, response = self.make_request('POST', 'menus', test_menu, 200)
        if success:
            menu_id = response.get('id')
            self.created_items['menu_id'] = menu_id
            create_success = self.log_test("CREATE Menu", True, f"Menu ID: {menu_id}")
            
            # Test UPDATE menu
            update_data = {
                "name": f"Updated Menu {datetime.now().strftime('%H%M%S')}",
                "module_id": module_id,
                "route_path": f"/updated-menu-{datetime.now().strftime('%H%M%S')}",
                "icon": "updated-icon",
                "order_index": 2
            }
            success, status, response = self.make_request('PUT', f'menus/{menu_id}', update_data)
            update_success = self.log_test("UPDATE Menu", success, f"Status: {status}")
            
            # Test DELETE menu
            success, status, response = self.make_request('DELETE', f'menus/{menu_id}')
            delete_success = self.log_test("DELETE Menu", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Menu", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_role_permissions_crud(self):
        """Test Role-Permissions CRUD operations"""
        print("\n🔗 Testing Role-Permissions CRUD...")
        
        # First get roles and permissions for mapping
        roles_success, _, roles_data = self.make_request('GET', 'roles')
        perms_success, _, perms_data = self.make_request('GET', 'permissions')
        
        role_id = roles_data[0]['id'] if roles_success and roles_data else str(uuid.uuid4())
        perm_id = perms_data[0]['id'] if perms_success and perms_data else str(uuid.uuid4())
        
        # Test GET role-permissions
        success, status, response = self.make_request('GET', 'role-permissions')
        get_success = self.log_test("GET Role-Permissions", success, f"Found {len(response) if success else 0} mappings")
        
        # Test CREATE role-permission mapping
        test_rp = {
            "role_id": role_id,
            "permission_id": perm_id
        }
        
        success, status, response = self.make_request('POST', 'role-permissions', test_rp, 200)
        if success:
            rp_id = response.get('id')
            self.created_items['rp_id'] = rp_id
            create_success = self.log_test("CREATE Role-Permission", True, f"Mapping ID: {rp_id}")
            
            # Test UPDATE role-permission (change to different permission if available)
            if len(perms_data) > 1:
                update_data = {
                    "role_id": role_id,
                    "permission_id": perms_data[1]['id']
                }
                success, status, response = self.make_request('PUT', f'role-permissions/{rp_id}', update_data)
                update_success = self.log_test("UPDATE Role-Permission", success, f"Status: {status}")
            else:
                update_success = True  # Skip if no other permissions available
            
            # Test DELETE role-permission
            success, status, response = self.make_request('DELETE', f'role-permissions/{rp_id}')
            delete_success = self.log_test("DELETE Role-Permission", success, f"Status: {status}")
            
            return get_success and create_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Role-Permission", False, f"Status: {status}, Response: {response}")
            return get_success and create_success

    def test_activity_logs(self):
        """Test Activity Logs (read-only)"""
        print("\n📊 Testing Activity Logs...")
        
        success, status, response = self.make_request('GET', 'activity-logs')
        return self.log_test("GET Activity Logs", success, f"Found {len(response) if success else 0} logs")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Sawayatta ERP Backend API Tests")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test all CRUD operations
        test_results = []
        test_results.append(("Users CRUD", self.test_users_crud()))
        test_results.append(("Roles CRUD", self.test_roles_crud()))
        test_results.append(("Departments CRUD", self.test_departments_crud()))
        test_results.append(("Designations CRUD", self.test_designations_crud()))
        test_results.append(("Permissions CRUD", self.test_permissions_crud()))
        test_results.append(("Modules CRUD", self.test_modules_crud()))
        test_results.append(("Menus CRUD", self.test_menus_crud()))
        test_results.append(("Role-Permissions CRUD", self.test_role_permissions_crud()))
        test_results.append(("Activity Logs", self.test_activity_logs()))
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 MODULE TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SawayattaERPTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())