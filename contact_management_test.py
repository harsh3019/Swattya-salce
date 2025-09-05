#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid
import time

class ContactManagementTester:
    def __init__(self, base_url="https://swayatta-admin.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {}  # Track created items for cleanup
        self.companies = []  # Store companies for contact creation
        self.designations = []  # Store designations

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

    def test_designations_master_data(self):
        """Test designations master data - should return 20 designations"""
        print("\n📋 Testing Designations Master Data...")
        
        success, status, response = self.make_request('GET', 'designations')
        
        if success and isinstance(response, list):
            designation_count = len(response)
            expected_count = 20
            
            if designation_count == expected_count:
                self.designations = response
                return self.log_test("GET Designations", True, 
                                   f"Found {designation_count}/{expected_count} designations (CEO, CTO, CFO, etc.)")
            else:
                return self.log_test("GET Designations", False, 
                                   f"Expected {expected_count} designations, found {designation_count}")
        else:
            return self.log_test("GET Designations", False, f"Status: {status}, Response: {response}")

    def setup_test_data(self):
        """Setup test companies for contact creation"""
        print("\n🏢 Setting up test companies...")
        
        # Get existing companies first
        success, status, response = self.make_request('GET', 'companies')
        if success and isinstance(response, list) and len(response) > 0:
            self.companies = response[:2]  # Use first 2 companies
            return self.log_test("Setup Test Companies", True, f"Using {len(self.companies)} existing companies")
        
        return self.log_test("Setup Test Companies", False, "No companies available for testing")

    def test_contact_crud_operations(self):
        """Test Contact CRUD operations"""
        print("\n👥 Testing Contact CRUD Operations...")
        
        if not self.companies or not self.designations:
            return self.log_test("Contact CRUD Setup", False, "Missing test data (companies/designations)")
        
        all_success = True
        
        # Test GET contacts (empty initially)
        success, status, response = self.make_request('GET', 'contacts')
        if success and 'contacts' in response:
            get_success = self.log_test("GET Contacts", True, 
                                      f"Found {len(response['contacts'])} contacts with pagination")
        else:
            get_success = self.log_test("GET Contacts", False, f"Status: {status}")
            all_success = False
        
        # Test CREATE contact
        timestamp = datetime.now().strftime('%H%M%S')
        test_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Mr.",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "email": f"rajesh.kumar.{timestamp}@techcorp.com",
            "primary_phone": "+91-9876543210",
            "designation_id": self.designations[0]['id'],
            "decision_maker": True,
            "spoc": True,
            "address": "123 Tech Park, Electronic City, Bangalore",
            "comments": "Key decision maker for technology purchases"
        }
        
        success, status, response = self.make_request('POST', 'contacts', test_contact, 200)
        if success and 'id' in response:
            contact_id = response['id']
            self.created_items['contact_id'] = contact_id
            create_success = self.log_test("CREATE Contact", True, f"Contact ID: {contact_id}")
            
            # Test GET specific contact
            success, status, get_response = self.make_request('GET', f'contacts/{contact_id}')
            get_specific_success = self.log_test("GET Specific Contact", success, 
                                               f"Retrieved contact: {get_response.get('first_name', '')} {get_response.get('last_name', '')}")
            
            # Test UPDATE contact
            update_data = {
                "comments": "Updated: Senior Technology Decision Maker",
                "decision_maker": True
            }
            success, status, update_response = self.make_request('PUT', f'contacts/{contact_id}', update_data)
            update_success = self.log_test("UPDATE Contact", success, f"Status: {status}")
            
            # Test DELETE contact (soft delete)
            success, status, delete_response = self.make_request('DELETE', f'contacts/{contact_id}')
            delete_success = self.log_test("DELETE Contact", success, f"Status: {status}")
            
            return all_success and create_success and get_specific_success and update_success and delete_success
        else:
            create_success = self.log_test("CREATE Contact", False, f"Status: {status}, Response: {response}")
            return all_success and create_success

    def test_duplicate_detection(self):
        """Test duplicate detection with 60% similarity threshold"""
        print("\n🔍 Testing Duplicate Detection...")
        
        if not self.companies or not self.designations:
            return self.log_test("Duplicate Detection Setup", False, "Missing test data")
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create first contact
        first_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Ms.",
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": f"priya.sharma.{timestamp}@company.com",
            "primary_phone": "+91-9876543211",
            "designation_id": self.designations[1]['id'],
            "decision_maker": False,
            "spoc": False
        }
        
        success, status, response = self.make_request('POST', 'contacts', first_contact, 200)
        if success:
            first_contact_id = response['id']
            self.created_items['first_duplicate_contact'] = first_contact_id
            
            # Test 1: Same email (should fail)
            duplicate_email_contact = {
                **first_contact,
                "first_name": "Different",
                "last_name": "Name"
            }
            success, status, response = self.make_request('POST', 'contacts', duplicate_email_contact, 400)
            email_duplicate_test = self.log_test("Duplicate Email Detection", success, 
                                               "Correctly rejected duplicate email")
            
            # Test 2: Similar name + same company (should trigger 60% similarity)
            similar_contact = {
                "company_id": self.companies[0]['id'],
                "salutation": "Ms.",
                "first_name": "Priya",  # Same first name
                "last_name": "Sharmaa",  # Very similar last name
                "email": f"priya.different.{timestamp}@company.com",
                "primary_phone": "+91-9876543212",
                "designation_id": self.designations[1]['id'],
                "decision_maker": False,
                "spoc": False
            }
            success, status, response = self.make_request('POST', 'contacts', similar_contact, 400)
            similarity_test = self.log_test("60% Similarity Detection", success, 
                                          "Correctly detected similar contact (name + company)")
            
            return email_duplicate_test and similarity_test
        else:
            return self.log_test("Duplicate Detection", False, f"Failed to create first contact: {status}")

    def test_spoc_management(self):
        """Test SPOC (Single Point of Contact) management"""
        print("\n🎯 Testing SPOC Management...")
        
        if not self.companies or not self.designations:
            return self.log_test("SPOC Management Setup", False, "Missing test data")
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create first SPOC contact
        first_spoc = {
            "company_id": self.companies[0]['id'],
            "salutation": "Mr.",
            "first_name": "Amit",
            "last_name": "Patel",
            "email": f"amit.patel.{timestamp}@company.com",
            "primary_phone": "+91-9876543213",
            "designation_id": self.designations[2]['id'],
            "decision_maker": True,
            "spoc": True
        }
        
        success, status, response = self.make_request('POST', 'contacts', first_spoc, 200)
        if success:
            first_spoc_id = response['id']
            self.created_items['first_spoc'] = first_spoc_id
            spoc_created = self.log_test("CREATE First SPOC", True, f"SPOC ID: {first_spoc_id}")
            
            # Try to create another SPOC for same company (should fail)
            second_spoc = {
                "company_id": self.companies[0]['id'],  # Same company
                "salutation": "Ms.",
                "first_name": "Neha",
                "last_name": "Singh",
                "email": f"neha.singh.{timestamp}@company.com",
                "primary_phone": "+91-9876543214",
                "designation_id": self.designations[3]['id'],
                "decision_maker": False,
                "spoc": True  # This should fail
            }
            
            success, status, response = self.make_request('POST', 'contacts', second_spoc, 400)
            spoc_enforcement = self.log_test("SPOC Uniqueness Enforcement", success, 
                                           "Correctly rejected second SPOC for same company")
            
            # Test force SPOC update functionality
            if 'first_spoc' in self.created_items:
                # Create a regular contact first
                regular_contact = {
                    "company_id": self.companies[0]['id'],
                    "salutation": "Ms.",
                    "first_name": "Neha",
                    "last_name": "Singh",
                    "email": f"neha.singh.regular.{timestamp}@company.com",
                    "primary_phone": "+91-9876543215",
                    "designation_id": self.designations[3]['id'],
                    "decision_maker": False,
                    "spoc": False
                }
                
                success, status, response = self.make_request('POST', 'contacts', regular_contact, 200)
                if success:
                    regular_contact_id = response['id']
                    self.created_items['regular_contact'] = regular_contact_id
                    
                    # Now try to update this contact to SPOC with force flag
                    force_spoc_update = {"spoc": True}
                    success, status, response = self.make_request('PUT', 
                                                                f'contacts/{regular_contact_id}?force_spoc_update=true', 
                                                                force_spoc_update)
                    force_spoc_test = self.log_test("Force SPOC Update", success, 
                                                  "Successfully transferred SPOC status")
                    
                    return spoc_created and spoc_enforcement and force_spoc_test
            
            return spoc_created and spoc_enforcement
        else:
            return self.log_test("SPOC Management", False, f"Failed to create first SPOC: {status}")

    def test_bulk_operations(self):
        """Test bulk operations (activate/deactivate)"""
        print("\n📦 Testing Bulk Operations...")
        
        if not self.companies or not self.designations:
            return self.log_test("Bulk Operations Setup", False, "Missing test data")
        
        # Create multiple contacts for bulk testing
        timestamp = datetime.now().strftime('%H%M%S')
        contact_ids = []
        
        for i in range(3):
            contact = {
                "company_id": self.companies[0]['id'],
                "salutation": "Mr.",
                "first_name": f"BulkTest{i}",
                "last_name": f"User{i}",
                "email": f"bulktest{i}.{timestamp}@company.com",
                "primary_phone": f"+91-987654321{i}",
                "designation_id": self.designations[i % len(self.designations)]['id'],
                "decision_maker": False,
                "spoc": False
            }
            
            success, status, response = self.make_request('POST', 'contacts', contact, 200)
            if success:
                contact_ids.append(response['id'])
        
        if len(contact_ids) >= 2:
            self.created_items['bulk_contacts'] = contact_ids
            
            # Test bulk deactivate
            bulk_deactivate = {
                "contact_ids": contact_ids[:2],
                "action": "deactivate"
            }
            success, status, response = self.make_request('POST', 'contacts/bulk', bulk_deactivate, 200)
            deactivate_success = self.log_test("Bulk Deactivate", success, 
                                             f"Deactivated {response.get('updated_count', 0)} contacts")
            
            # Test bulk activate
            bulk_activate = {
                "contact_ids": contact_ids[:2],
                "action": "activate"
            }
            success, status, response = self.make_request('POST', 'contacts/bulk', bulk_activate, 200)
            activate_success = self.log_test("Bulk Activate", success, 
                                           f"Activated {response.get('updated_count', 0)} contacts")
            
            return deactivate_success and activate_success
        else:
            return self.log_test("Bulk Operations", False, "Failed to create test contacts")

    def test_validation_rules(self):
        """Test validation rules"""
        print("\n✅ Testing Validation Rules...")
        
        if not self.companies or not self.designations:
            return self.log_test("Validation Setup", False, "Missing test data")
        
        all_success = True
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Test 1: Invalid email format
        invalid_email_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Mr.",
            "first_name": "Test",
            "last_name": "User",
            "email": "invalid-email-format",  # Invalid email
            "primary_phone": "+91-9876543210",
            "designation_id": self.designations[0]['id']
        }
        success, status, response = self.make_request('POST', 'contacts', invalid_email_contact, 422)
        email_validation = self.log_test("Email Format Validation", success, "Rejected invalid email format")
        all_success = all_success and email_validation
        
        # Test 2: Invalid phone format
        invalid_phone_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Mr.",
            "first_name": "Test",
            "last_name": "User",
            "email": f"test.phone.{timestamp}@company.com",
            "primary_phone": "123",  # Too short
            "designation_id": self.designations[0]['id']
        }
        success, status, response = self.make_request('POST', 'contacts', invalid_phone_contact, 422)
        phone_validation = self.log_test("Phone Format Validation", success, "Rejected invalid phone format")
        all_success = all_success and phone_validation
        
        # Test 3: Missing required fields
        incomplete_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Mr.",
            # Missing first_name, email, primary_phone
        }
        success, status, response = self.make_request('POST', 'contacts', incomplete_contact, 422)
        required_fields = self.log_test("Required Fields Validation", success, "Rejected incomplete contact data")
        all_success = all_success and required_fields
        
        # Test 4: Invalid salutation
        invalid_salutation_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Invalid",  # Not in allowed list
            "first_name": "Test",
            "last_name": "User",
            "email": f"test.salutation.{timestamp}@company.com",
            "primary_phone": "+91-9876543210",
            "designation_id": self.designations[0]['id']
        }
        success, status, response = self.make_request('POST', 'contacts', invalid_salutation_contact, 422)
        salutation_validation = self.log_test("Salutation Validation", success, "Rejected invalid salutation")
        all_success = all_success and salutation_validation
        
        # Test 5: Character limits
        long_name_contact = {
            "company_id": self.companies[0]['id'],
            "salutation": "Mr.",
            "first_name": "A" * 100,  # Exceeds 50 char limit
            "last_name": "User",
            "email": f"test.longname.{timestamp}@company.com",
            "primary_phone": "+91-9876543210",
            "designation_id": self.designations[0]['id']
        }
        success, status, response = self.make_request('POST', 'contacts', long_name_contact, 422)
        char_limit_validation = self.log_test("Character Limit Validation", success, "Rejected name exceeding limit")
        all_success = all_success and char_limit_validation
        
        return all_success

    def test_access_control_rbac(self):
        """Test access control and RBAC permissions"""
        print("\n🔒 Testing Access Control & RBAC...")
        
        # Test that admin user has proper access (should work with current token)
        success, status, response = self.make_request('GET', 'contacts')
        admin_access = self.log_test("Admin Access to Contacts", success, "Admin has proper Sales module permissions")
        
        # Test permissions endpoint
        success, status, response = self.make_request('GET', 'auth/permissions')
        if success and 'permissions' in response:
            permissions = response['permissions']
            sales_permissions = [p for p in permissions if p.get('module') == 'Sales' and p.get('menu') == 'Contacts']
            
            expected_perms = ['View', 'Add', 'Edit', 'Delete', 'Export']
            found_perms = [p['permission'] for p in sales_permissions]
            
            has_all_perms = all(perm in found_perms for perm in expected_perms)
            rbac_test = self.log_test("RBAC Permissions Check", has_all_perms, 
                                    f"Found permissions: {', '.join(found_perms)}")
        else:
            rbac_test = self.log_test("RBAC Permissions Check", False, "Failed to get permissions")
        
        return admin_access and rbac_test

    def test_export_and_search(self):
        """Test export and search functionality"""
        print("\n📊 Testing Export & Search...")
        
        all_success = True
        
        # Test search functionality
        success, status, response = self.make_request('GET', 'contacts?search=test')
        if success and isinstance(response, dict) and 'contacts' in response:
            search_count = len(response['contacts'])
        else:
            search_count = 0
        search_test = self.log_test("Search Functionality", success, f"Search returned {search_count} results")
        all_success = all_success and search_test
        
        # Test filtering by company
        if self.companies:
            success, status, response = self.make_request('GET', f'contacts?company_id={self.companies[0]["id"]}')
            filter_test = self.log_test("Company Filter", success, 
                                      f"Company filter returned {len(response.get('contacts', [])) if success else 0} results")
            all_success = all_success and filter_test
        
        # Test filtering by designation
        if self.designations:
            success, status, response = self.make_request('GET', f'contacts?designation_id={self.designations[0]["id"]}')
            designation_filter = self.log_test("Designation Filter", success, 
                                             f"Designation filter returned {len(response.get('contacts', [])) if success else 0} results")
            all_success = all_success and designation_filter
        
        # Test SPOC filter
        success, status, response = self.make_request('GET', 'contacts?spoc=true')
        spoc_filter = self.log_test("SPOC Filter", success, 
                                  f"SPOC filter returned {len(response.get('contacts', [])) if success else 0} results")
        all_success = all_success and spoc_filter
        
        # Test decision maker filter
        success, status, response = self.make_request('GET', 'contacts?decision_maker=true')
        decision_maker_filter = self.log_test("Decision Maker Filter", success, 
                                            f"Decision maker filter returned {len(response.get('contacts', [])) if success else 0} results")
        all_success = all_success and decision_maker_filter
        
        # Test export functionality
        success, status, response = self.make_request('GET', 'contacts/export')
        export_test = self.log_test("CSV Export", success, 
                                  f"Export returned {len(response) if success and isinstance(response, list) else 0} contacts")
        all_success = all_success and export_test
        
        # Test pagination
        success, status, response = self.make_request('GET', 'contacts?page=1&limit=10')
        if success and 'contacts' in response:
            pagination_test = self.log_test("Pagination", True, 
                                          f"Page 1 returned {len(response['contacts'])} contacts, total: {response.get('total', 0)}")
        else:
            pagination_test = self.log_test("Pagination", False, f"Status: {status}")
        all_success = all_success and pagination_test
        
        return all_success

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        cleanup_count = 0
        
        # Clean up individual contacts
        for key, contact_id in self.created_items.items():
            if isinstance(contact_id, str) and key != 'bulk_contacts':
                success, status, response = self.make_request('DELETE', f'contacts/{contact_id}')
                if success:
                    cleanup_count += 1
        
        # Clean up bulk contacts
        if 'bulk_contacts' in self.created_items:
            for contact_id in self.created_items['bulk_contacts']:
                success, status, response = self.make_request('DELETE', f'contacts/{contact_id}')
                if success:
                    cleanup_count += 1
        
        self.log_test("Cleanup Test Data", True, f"Cleaned up {cleanup_count} test contacts")

    def run_comprehensive_contact_tests(self):
        """Run comprehensive Contact Management backend tests"""
        print("🚀 Starting Contact Management Backend API Tests")
        print("=" * 70)
        
        # Test authentication first
        if not self.test_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Failed to setup test data. Cannot proceed.")
            return False
        
        # Run all Contact Management tests
        test_results = []
        test_results.append(("Designations Master Data (20 items)", self.test_designations_master_data()))
        test_results.append(("Contact CRUD Operations", self.test_contact_crud_operations()))
        test_results.append(("Duplicate Detection (60% similarity)", self.test_duplicate_detection()))
        test_results.append(("SPOC Management", self.test_spoc_management()))
        test_results.append(("Bulk Operations", self.test_bulk_operations()))
        test_results.append(("Validation Testing", self.test_validation_rules()))
        test_results.append(("Access Control & RBAC", self.test_access_control_rbac()))
        test_results.append(("Export & Search", self.test_export_and_search()))
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 CONTACT MANAGEMENT TEST SUMMARY")
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
    tester = ContactManagementTester()
    success = tester.run_comprehensive_contact_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())