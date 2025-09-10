#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ExportRoutingTester:
    def __init__(self, base_url="https://erp-quotation.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.contact_id = None

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
        """Test admin authentication"""
        print("\n🔐 Testing Admin Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_data = response.get('user', {})
            return self.log_test("Admin Login", True, 
                               f"Token received, User: {user_data.get('username', 'N/A')}, Role: {user_data.get('role_id', 'N/A')}")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_export_endpoint(self):
        """Test contacts export endpoint - should work without routing conflict"""
        print("\n📤 Testing Contacts Export Endpoint...")
        
        success, status, response = self.make_request('GET', 'contacts/export')
        
        if success:
            # Check if response contains export data
            if isinstance(response, list):
                has_data = len(response) >= 0  # List response is valid
                filename = "contacts_export.csv"
                data_info = f"List with {len(response)} items"
            elif isinstance(response, dict):
                has_data = 'data' in response or 'contacts' in response
                filename = response.get('filename', 'N/A')
                data_info = f"Dict with keys: {list(response.keys())}"
            else:
                has_data = False
                filename = 'N/A'
                data_info = f"Unexpected response type: {type(response)}"
            
            return self.log_test("GET /api/contacts/export", True, 
                               f"Export successful, Has data: {has_data}, Filename: {filename}, Data: {data_info}")
        else:
            error_msg = response.get('detail', response.get('error', 'Unknown error')) if isinstance(response, dict) else str(response)
            return self.log_test("GET /api/contacts/export", False, 
                               f"Status: {status}, Error: {error_msg}")

    def test_individual_contact_endpoint(self):
        """Test individual contact endpoint - should still work correctly"""
        print("\n👤 Testing Individual Contact Endpoint...")
        
        # First, get list of contacts to find a valid contact ID
        success, status, contacts_response = self.make_request('GET', 'contacts')
        
        if not success or not contacts_response:
            return self.log_test("GET Individual Contact", False, 
                               "Could not get contacts list to test individual contact endpoint")
        
        # Extract contacts from response (could be direct list or nested in 'contacts' key)
        contacts = contacts_response if isinstance(contacts_response, list) else contacts_response.get('contacts', [])
        
        if not contacts:
            return self.log_test("GET Individual Contact", False, 
                               "No contacts available to test individual contact endpoint")
        
        # Get the first contact ID
        contact_id = contacts[0].get('id')
        if not contact_id:
            return self.log_test("GET Individual Contact", False, 
                               "Contact ID not found in contacts list")
        
        self.contact_id = contact_id
        
        # Test individual contact endpoint
        success, status, response = self.make_request('GET', f'contacts/{contact_id}')
        
        if success:
            contact_name = response.get('first_name', 'N/A')
            contact_email = response.get('email', 'N/A')
            return self.log_test("GET /api/contacts/{id}", True, 
                               f"Contact retrieved: {contact_name}, Email: {contact_email}")
        else:
            error_msg = response.get('detail', response.get('error', 'Unknown error')) if isinstance(response, dict) else str(response)
            return self.log_test("GET /api/contacts/{id}", False, 
                               f"Status: {status}, Error: {error_msg}")

    def test_routing_conflict_resolution(self):
        """Test that both endpoints work without conflicts"""
        print("\n🔀 Testing Routing Conflict Resolution...")
        
        # Test that 'export' is not treated as a contact ID
        success, status, response = self.make_request('GET', 'contacts/export')
        export_works = success
        
        # Test that a real contact ID still works
        if self.contact_id:
            success, status, response = self.make_request('GET', f'contacts/{self.contact_id}')
            individual_works = success
        else:
            individual_works = True  # Skip if no contact ID available
        
        both_work = export_works and individual_works
        return self.log_test("Routing Conflict Resolution", both_work, 
                           f"Export works: {export_works}, Individual works: {individual_works}")

    def run_export_routing_tests(self):
        """Run focused tests for export endpoint routing fix"""
        print("🚀 Starting Export Endpoint Routing Tests")
        print("=" * 60)
        print("Testing the fix for export endpoint routing conflict")
        print("Issue: GET /api/contacts/export was conflicting with GET /api/contacts/{id}")
        print("Expected: Both endpoints should work correctly without conflicts")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_admin_login():
            print("\n❌ Authentication failed. Cannot proceed with routing tests.")
            return False
        
        # Run the specific routing tests
        test_results = []
        test_results.append(("Export Endpoint", self.test_export_endpoint()))
        test_results.append(("Individual Contact Endpoint", self.test_individual_contact_endpoint()))
        test_results.append(("Routing Conflict Resolution", self.test_routing_conflict_resolution()))
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 EXPORT ROUTING TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        # Final assessment
        all_passed = all(result for _, result in test_results)
        if all_passed:
            print(f"\n🎉 SUCCESS: Export endpoint routing fix is working correctly!")
            print(f"   ✅ Export endpoint returns data without 404 error")
            print(f"   ✅ Individual contact endpoint still works correctly")
            print(f"   ✅ No routing conflicts between the two endpoints")
        else:
            print(f"\n⚠️  ISSUES DETECTED: Export endpoint routing needs attention")
            failed_tests = [name for name, result in test_results if not result]
            print(f"   Failed tests: {', '.join(failed_tests)}")
        
        return all_passed

def main():
    tester = ExportRoutingTester()
    success = tester.run_export_routing_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())