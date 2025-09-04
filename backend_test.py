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
        print(f"\n{'='*50}")
        print("TESTING AUTHENTICATION")
        print(f"{'='*50}")
        
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

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        success, response = self.run_test(
            "Get current user info",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_auth_logout(self):
        """Test logout endpoint"""
        success, response = self.run_test(
            "Logout",
            "POST",
            "auth/logout",
            200
        )
        return success

    def test_users_endpoints(self):
        """Test user management endpoints"""
        print(f"\n{'='*50}")
        print("TESTING USER MANAGEMENT")
        print(f"{'='*50}")
        
        # Get all users
        success, users = self.run_test(
            "Get all users",
            "GET",
            "users",
            200
        )
        
        if success:
            print(f"   Found {len(users)} users")
        
        return success

    def test_companies_endpoints(self):
        """Test companies endpoints"""
        print(f"\n{'='*50}")
        print("TESTING COMPANIES")
        print(f"{'='*50}")
        
        # Get all companies
        success, companies = self.run_test(
            "Get all companies",
            "GET",
            "companies",
            200
        )
        
        if success:
            print(f"   Found {len(companies)} companies")
        
        # Test creating a company
        test_company = {
            "company_name": f"Test Company {datetime.now().strftime('%H%M%S')}",
            "company_type": "Private",
            "region": "North America",
            "industry": "Technology"
        }
        
        create_success, company_data = self.run_test(
            "Create new company",
            "POST",
            "companies",
            200,
            data=test_company
        )
        
        if create_success and company_data:
            company_id = company_data.get('id')
            if company_id:
                # Test getting specific company
                get_success, _ = self.run_test(
                    f"Get company by ID",
                    "GET",
                    f"companies/{company_id}",
                    200
                )
                return success and create_success and get_success
        
        return success and create_success

    def test_contacts_endpoints(self):
        """Test contacts endpoints"""
        print(f"\n{'='*50}")
        print("TESTING CONTACTS")
        print(f"{'='*50}")
        
        # Get all contacts
        success, contacts = self.run_test(
            "Get all contacts",
            "GET",
            "contacts",
            200
        )
        
        if success:
            print(f"   Found {len(contacts)} contacts")
        
        # Test creating a contact
        test_contact = {
            "first_name": "Test",
            "last_name": f"Contact{datetime.now().strftime('%H%M%S')}",
            "email": f"test{datetime.now().strftime('%H%M%S')}@example.com"
        }
        
        create_success, contact_data = self.run_test(
            "Create new contact",
            "POST",
            "contacts",
            200,
            data=test_contact
        )
        
        return success and create_success

    def test_other_endpoints(self):
        """Test other master data endpoints"""
        print(f"\n{'='*50}")
        print("TESTING OTHER ENDPOINTS")
        print(f"{'='*50}")
        
        endpoints = [
            ("departments", "Get departments"),
            ("designations", "Get designations"),
            ("roles", "Get roles"),
            ("activity-logs", "Get activity logs")
        ]
        
        all_success = True
        for endpoint, description in endpoints:
            success, data = self.run_test(
                description,
                "GET",
                endpoint,
                200
            )
            if success and isinstance(data, list):
                print(f"   Found {len(data)} {endpoint}")
            all_success = all_success and success
        
        return all_success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        print(f"\n{'='*50}")
        print("TESTING INVALID AUTHENTICATION")
        print(f"{'='*50}")
        
        success, response = self.run_test(
            "Login with invalid credentials",
            "POST",
            "auth/login",
            401,
            data={"username": "invalid", "password": "invalid"}
        )
        
        return success  # Success means we got the expected 401 status

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without token"""
        print(f"\n{'='*50}")
        print("TESTING UNAUTHORIZED ACCESS")
        print(f"{'='*50}")
        
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Access protected endpoint without token",
            "GET",
            "users",
            401
        )
        
        # Restore token
        self.token = original_token
        
        return success  # Success means we got the expected 401 status

def main():
    print("🚀 Starting Sawayatta ERP Backend API Tests")
    print("=" * 60)
    
    tester = SawayattaERPTester()
    
    # Test sequence
    tests = [
        ("Login Test", tester.test_login),
        ("Auth Me Test", tester.test_auth_me),
        ("Users Endpoints", tester.test_users_endpoints),
        ("Companies Endpoints", tester.test_companies_endpoints),
        ("Contacts Endpoints", tester.test_contacts_endpoints),
        ("Other Endpoints", tester.test_other_endpoints),
        ("Invalid Login Test", tester.test_invalid_login),
        ("Unauthorized Access Test", tester.test_unauthorized_access),
        ("Logout Test", tester.test_auth_logout)
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
    print(f"\n{'='*60}")
    print("FINAL TEST RESULTS")
    print(f"{'='*60}")
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"✅ Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed test categories:")
        for test in failed_tests:
            print(f"   - {test}")
        return 1
    else:
        print(f"\n🎉 All test categories passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())