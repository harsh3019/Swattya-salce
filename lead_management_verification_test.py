#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class LeadManagementVerificationTester:
    def __init__(self, base_url="https://sawayatta-erp-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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
            username = user_data.get('username', 'unknown')
            role_id = user_data.get('role_id', 'unknown')
            return self.log_test("Admin Login", True, f"Username: {username}, Role ID: {role_id}")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_product_services_api(self):
        """Test Product Services API - should return ~10 services"""
        print("\n📦 Testing Product Services API...")
        
        success, status, response = self.make_request('GET', 'product-services')
        
        if success and isinstance(response, list):
            count = len(response)
            expected_count = 10
            
            # Check if we have the expected number of services
            count_ok = count >= 8  # Allow some flexibility (8-12 services)
            
            # Check structure of first service if available
            structure_ok = True
            if response:
                service = response[0]
                required_fields = ['id', 'name', 'is_active', 'created_at']
                structure_ok = all(field in service for field in required_fields)
            
            # Log some service names for verification
            service_names = [s.get('name', 'Unknown') for s in response[:5]]  # First 5 names
            
            overall_success = success and count_ok and structure_ok
            details = f"Count: {count} (expected ~{expected_count}), Structure OK: {structure_ok}, Sample names: {service_names}"
            
            return self.log_test("GET Product Services", overall_success, details)
        else:
            return self.log_test("GET Product Services", False, f"Status: {status}, Response type: {type(response)}")

    def test_sub_tender_types_api(self):
        """Test Sub-Tender Types API - should return ~8 types"""
        print("\n📋 Testing Sub-Tender Types API...")
        
        success, status, response = self.make_request('GET', 'sub-tender-types')
        
        if success and isinstance(response, list):
            count = len(response)
            expected_count = 8
            
            # Check if we have the expected number of types
            count_ok = count >= 6  # Allow some flexibility (6-10 types)
            
            # Check structure of first type if available
            structure_ok = True
            if response:
                sub_type = response[0]
                required_fields = ['id', 'name', 'is_active', 'created_at']
                structure_ok = all(field in sub_type for field in required_fields)
            
            # Log some type names for verification
            type_names = [t.get('name', 'Unknown') for t in response[:5]]  # First 5 names
            
            overall_success = success and count_ok and structure_ok
            details = f"Count: {count} (expected ~{expected_count}), Structure OK: {structure_ok}, Sample names: {type_names}"
            
            return self.log_test("GET Sub-Tender Types", overall_success, details)
        else:
            return self.log_test("GET Sub-Tender Types", False, f"Status: {status}, Response type: {type(response)}")

    def test_partners_api(self):
        """Test Partners API - basic functionality"""
        print("\n🤝 Testing Partners API...")
        
        success, status, response = self.make_request('GET', 'partners')
        
        if success and isinstance(response, list):
            count = len(response)
            
            # Check structure if partners exist
            structure_ok = True
            if response:
                partner = response[0]
                required_fields = ['id', 'name', 'is_active', 'created_at']
                structure_ok = all(field in partner for field in required_fields)
                
                # Log some partner names for verification
                partner_names = [p.get('name', 'Unknown') for p in response[:3]]
                details = f"Count: {count}, Structure OK: {structure_ok}, Sample names: {partner_names}"
            else:
                # Empty list is acceptable for partners
                details = f"Count: {count} (empty list is acceptable), Structure OK: {structure_ok}"
            
            overall_success = success and structure_ok
            return self.log_test("GET Partners", overall_success, details)
        else:
            return self.log_test("GET Partners", False, f"Status: {status}, Response type: {type(response)}")

    def test_rbac_permissions(self):
        """Test RBAC permissions are working"""
        print("\n🔑 Testing RBAC Permissions...")
        
        success, status, response = self.make_request('GET', 'auth/permissions')
        
        if success and 'permissions' in response:
            permissions = response['permissions']
            
            # Look for lead management related permissions
            lead_permissions = [p for p in permissions if 'Product Services' in p.get('menu', '') or 
                             'Sub-Tender Types' in p.get('menu', '') or 'Partners' in p.get('menu', '')]
            
            # Check if admin has the required permissions
            has_product_services = any('Product Services' in p.get('menu', '') for p in permissions)
            has_sub_tender_types = any('Sub-Tender Types' in p.get('menu', '') for p in permissions)
            has_partners = any('Partners' in p.get('menu', '') or 'Channel Partners' in p.get('menu', '') for p in permissions)
            
            total_permissions = len(permissions)
            lead_permissions_count = len(lead_permissions)
            
            rbac_working = has_product_services or has_sub_tender_types or has_partners
            details = f"Total permissions: {total_permissions}, Lead permissions: {lead_permissions_count}, Product Services: {has_product_services}, Sub-Tender Types: {has_sub_tender_types}, Partners: {has_partners}"
            
            return self.log_test("RBAC Permissions Check", rbac_working, details)
        else:
            return self.log_test("RBAC Permissions Check", False, f"Status: {status}, Response: {response}")

    def test_no_500_errors(self):
        """Verify no 500 Internal Server Errors on key endpoints"""
        print("\n🚫 Testing for 500 Internal Server Errors...")
        
        endpoints_to_test = [
            'product-services',
            'sub-tender-types', 
            'partners',
            'auth/permissions'
        ]
        
        all_success = True
        error_details = []
        
        for endpoint in endpoints_to_test:
            success, status, response = self.make_request('GET', endpoint)
            
            if status == 500:
                all_success = False
                error_details.append(f"{endpoint}: 500 Error")
                self.log_test(f"No 500 Error - {endpoint}", False, f"Got 500 Internal Server Error")
            else:
                self.log_test(f"No 500 Error - {endpoint}", True, f"Status: {status}")
        
        if all_success:
            return self.log_test("Overall 500 Error Check", True, "No 500 errors found on any endpoint")
        else:
            return self.log_test("Overall 500 Error Check", False, f"500 errors found: {', '.join(error_details)}")

    def run_verification_tests(self):
        """Run the specific verification tests requested"""
        print("🚀 Starting Lead Management Backend API Verification Tests")
        print("=" * 70)
        print("📋 SCOPE: Product Services, Sub-Tender Types, Partners APIs")
        print("🎯 FOCUS: Verify 500 Internal Server Error is fixed")
        print("=" * 70)
        
        # Test authentication first
        if not self.test_admin_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run the specific verification tests
        test_results = []
        test_results.append(("No 500 Errors", self.test_no_500_errors()))
        test_results.append(("Product Services API", self.test_product_services_api()))
        test_results.append(("Sub-Tender Types API", self.test_sub_tender_types_api()))
        test_results.append(("Partners API", self.test_partners_api()))
        test_results.append(("RBAC Permissions", self.test_rbac_permissions()))
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 VERIFICATION TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        # Overall assessment
        critical_tests_passed = test_results[0][1] and test_results[1][1] and test_results[2][1] and test_results[3][1]  # No 500 errors + all 3 APIs working
        
        print(f"\n🎯 VERIFICATION RESULT:")
        if critical_tests_passed:
            print("✅ VERIFICATION SUCCESSFUL: Lead Management APIs are working correctly")
            print("✅ 500 Internal Server Error has been fixed")
            print("✅ All required APIs return data without errors")
        else:
            print("❌ VERIFICATION FAILED: Issues found with Lead Management APIs")
            if not test_results[0][1]:
                print("❌ 500 Internal Server Errors still present")
            
        return critical_tests_passed

def main():
    tester = LeadManagementVerificationTester()
    success = tester.run_verification_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())