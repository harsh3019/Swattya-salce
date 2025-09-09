import requests
import sys
import json
from datetime import datetime

class ComprehensiveUserManagementTester:
    def __init__(self, base_url="https://lead-opp-crm.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_data = None
        self.created_items = {}  # Track created items for cleanup

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {json.dumps(response_data, indent=2)}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n{'='*60}")
        print("TESTING AUTHENTICATION")
        print(f"{'='*60}")
        
        success, response = self.run_test(
            "Login with admin credentials",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response.get('user', {})
            print(f"   Token received: {self.token[:20]}...")
            print(f"   User ID: {self.user_data.get('id')}")
            print(f"   Username: {self.user_data.get('username')}")
            return True
        return False

    def test_departments_crud(self):
        """Test Departments CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING DEPARTMENTS MODULE")
        print(f"{'='*60}")
        
        # GET all departments
        success, departments = self.run_test(
            "Get all departments",
            "GET",
            "departments",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(departments)} departments")
        
        # CREATE new department
        timestamp = datetime.now().strftime('%H%M%S')
        test_dept = {
            "name": f"Test Department {timestamp}",
            "is_active": True
        }
        
        create_success, dept_data = self.run_test(
            "Create new department",
            "POST",
            "departments",
            200,
            data=test_dept
        )
        
        if create_success and dept_data:
            dept_id = dept_data.get('id')
            self.created_items['department_id'] = dept_id
            
            # UPDATE department
            updated_dept = {
                "name": f"Updated Department {timestamp}",
                "is_active": True
            }
            
            update_success, _ = self.run_test(
                "Update department",
                "PUT",
                f"departments/{dept_id}",
                200,
                data=updated_dept
            )
            
            # DELETE department (soft delete)
            delete_success, _ = self.run_test(
                "Delete department",
                "DELETE",
                f"departments/{dept_id}",
                200
            )
            
            return success and create_success and update_success and delete_success
        
        return success and create_success

    def test_designations_crud(self):
        """Test Designations CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING DESIGNATIONS MODULE")
        print(f"{'='*60}")
        
        # GET all designations
        success, designations = self.run_test(
            "Get all designations",
            "GET",
            "designations",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(designations)} designations")
        
        # CREATE new designation
        timestamp = datetime.now().strftime('%H%M%S')
        test_desig = {
            "name": f"Test Designation {timestamp}",
            "is_active": True
        }
        
        create_success, desig_data = self.run_test(
            "Create new designation",
            "POST",
            "designations",
            200,
            data=test_desig
        )
        
        if create_success and desig_data:
            desig_id = desig_data.get('id')
            self.created_items['designation_id'] = desig_id
            
            # UPDATE designation
            updated_desig = {
                "name": f"Updated Designation {timestamp}",
                "is_active": True
            }
            
            update_success, _ = self.run_test(
                "Update designation",
                "PUT",
                f"designations/{desig_id}",
                200,
                data=updated_desig
            )
            
            # DELETE designation (soft delete)
            delete_success, _ = self.run_test(
                "Delete designation",
                "DELETE",
                f"designations/{desig_id}",
                200
            )
            
            return success and create_success and update_success and delete_success
        
        return success and create_success

    def test_roles_crud(self):
        """Test Roles CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING ROLES MODULE")
        print(f"{'='*60}")
        
        # GET all roles
        success, roles = self.run_test(
            "Get all roles",
            "GET",
            "roles",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(roles)} roles")
        
        # CREATE new role
        timestamp = datetime.now().strftime('%H%M%S')
        test_role = {
            "name": f"Test Role {timestamp}",
            "description": f"Test role created at {timestamp}",
            "is_active": True
        }
        
        create_success, role_data = self.run_test(
            "Create new role",
            "POST",
            "roles",
            200,
            data=test_role
        )
        
        if create_success and role_data:
            self.created_items['role_id'] = role_data.get('id')
        
        return success and create_success

    def test_modules_crud(self):
        """Test Modules CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING MODULES MODULE")
        print(f"{'='*60}")
        
        # GET all modules
        success, modules = self.run_test(
            "Get all modules",
            "GET",
            "modules",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(modules)} modules")
        
        # CREATE new module
        timestamp = datetime.now().strftime('%H%M%S')
        test_module = {
            "name": f"Test Module {timestamp}",
            "description": f"Test module created at {timestamp}",
            "is_active": True
        }
        
        create_success, module_data = self.run_test(
            "Create new module",
            "POST",
            "modules",
            200,
            data=test_module
        )
        
        if create_success and module_data:
            self.created_items['module_id'] = module_data.get('id')
        
        return success and create_success

    def test_permissions_crud(self):
        """Test Permissions CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING PERMISSIONS MODULE")
        print(f"{'='*60}")
        
        # GET all permissions
        success, permissions = self.run_test(
            "Get all permissions",
            "GET",
            "permissions",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(permissions)} permissions")
        
        # CREATE new permission (requires module_id)
        if 'module_id' in self.created_items:
            timestamp = datetime.now().strftime('%H%M%S')
            test_permission = {
                "key": f"test_permission_{timestamp}",
                "label": f"Test Permission {timestamp}",
                "module_id": self.created_items['module_id'],
                "is_active": True
            }
            
            create_success, perm_data = self.run_test(
                "Create new permission",
                "POST",
                "permissions",
                200,
                data=test_permission
            )
            
            if create_success and perm_data:
                self.created_items['permission_id'] = perm_data.get('id')
            
            return success and create_success
        else:
            print("   Skipping permission creation - no module_id available")
            return success

    def test_menus_crud(self):
        """Test Menus CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING MENUS MODULE")
        print(f"{'='*60}")
        
        # GET all menus
        success, menus = self.run_test(
            "Get all menus",
            "GET",
            "menus",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(menus)} menus")
        
        # CREATE new menu (requires module_id)
        if 'module_id' in self.created_items:
            timestamp = datetime.now().strftime('%H%M%S')
            test_menu = {
                "name": f"Test Menu {timestamp}",
                "module_id": self.created_items['module_id'],
                "route_path": f"/test-menu-{timestamp}",
                "icon": "TestIcon",
                "order_index": 99,
                "is_active": True
            }
            
            create_success, menu_data = self.run_test(
                "Create new menu",
                "POST",
                "menus",
                200,
                data=test_menu
            )
            
            if create_success and menu_data:
                self.created_items['menu_id'] = menu_data.get('id')
            
            return success and create_success
        else:
            print("   Skipping menu creation - no module_id available")
            return success

    def test_role_permissions_crud(self):
        """Test Role-Permissions CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING ROLE-PERMISSIONS MODULE")
        print(f"{'='*60}")
        
        # GET all role-permissions
        success, role_perms = self.run_test(
            "Get all role-permissions",
            "GET",
            "role-permissions",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(role_perms)} role-permission mappings")
        
        # CREATE new role-permission mapping
        if 'role_id' in self.created_items and 'permission_id' in self.created_items:
            test_role_perm = {
                "role_id": self.created_items['role_id'],
                "permission_id": self.created_items['permission_id'],
                "is_active": True
            }
            
            create_success, rp_data = self.run_test(
                "Create new role-permission mapping",
                "POST",
                "role-permissions",
                200,
                data=test_role_perm
            )
            
            return success and create_success
        else:
            print("   Skipping role-permission creation - missing role_id or permission_id")
            return success

    def test_users_crud(self):
        """Test Users CRUD operations"""
        print(f"\n{'='*60}")
        print("TESTING USERS MODULE")
        print(f"{'='*60}")
        
        # GET all users
        success, users = self.run_test(
            "Get all users",
            "GET",
            "users",
            200
        )
        
        if not success:
            return False
        
        print(f"   Found {len(users)} users")
        
        # CREATE new user
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "username": f"testuser{timestamp}",
            "email": f"testuser{timestamp}@example.com",
            "password": "TestPassword123!",
            "role_id": self.created_items.get('role_id'),
            "department_id": self.created_items.get('department_id'),
            "designation_id": self.created_items.get('designation_id')
        }
        
        create_success, user_data = self.run_test(
            "Create new user",
            "POST",
            "users",
            200,
            data=test_user
        )
        
        return success and create_success

    def test_activity_logs(self):
        """Test Activity Logs (read-only)"""
        print(f"\n{'='*60}")
        print("TESTING ACTIVITY LOGS MODULE")
        print(f"{'='*60}")
        
        # GET all activity logs
        success, logs = self.run_test(
            "Get activity logs",
            "GET",
            "activity-logs",
            200
        )
        
        if success:
            print(f"   Found {len(logs)} activity log entries")
        
        return success

def main():
    print("🚀 Starting Comprehensive User Management Backend Tests")
    print("=" * 70)
    
    tester = ComprehensiveUserManagementTester()
    
    # Test sequence - order matters for dependencies
    tests = [
        ("Authentication", tester.test_login),
        ("Departments CRUD", tester.test_departments_crud),
        ("Designations CRUD", tester.test_designations_crud),
        ("Roles CRUD", tester.test_roles_crud),
        ("Modules CRUD", tester.test_modules_crud),
        ("Permissions CRUD", tester.test_permissions_crud),
        ("Menus CRUD", tester.test_menus_crud),
        ("Role-Permissions CRUD", tester.test_role_permissions_crud),
        ("Users CRUD", tester.test_users_crud),
        ("Activity Logs", tester.test_activity_logs)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*70}")
    print("COMPREHENSIVE TEST RESULTS")
    print(f"{'='*70}")
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"✅ Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed test categories:")
        for test in failed_tests:
            print(f"   - {test}")
        return 1
    else:
        print(f"\n🎉 All User Management modules tested successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())