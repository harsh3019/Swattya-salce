#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class ContactManagementTester:
    def __init__(self, base_url="https://sawayatta-erp-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {}  # Track created items for cleanup
        self.companies = []  # Store companies for testing

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

    def setup_test_data(self):
        """Setup test data - get existing companies or create test companies"""
        print("\n🏢 Setting up test data...")
        
        # Get existing companies
        success, status, response = self.make_request('GET', 'companies')
        if success and isinstance(response, list) and len(response) > 0:
            self.companies = response[:3]  # Use first 3 companies
            return self.log_test("Get Existing Companies", True, f"Found {len(self.companies)} companies for testing")
        
        # If no companies exist, create test companies
        return self.create_test_companies()

    def create_test_companies(self):
        """Create test companies for contact testing"""
        print("Creating test companies...")
        
        # Get master data first
        master_data = {}
        endpoints = ['company-types', 'account-types', 'regions', 'business-types', 'industries', 'countries']
        
        for endpoint in endpoints:
            success, status, response = self.make_request('GET', endpoint)
            if success and response:
                master_data[endpoint] = response
        
        if not all(endpoint in master_data for endpoint in endpoints):
            return self.log_test("Create Test Companies", False, "Missing master data")
        
        # Create 2 test companies
        companies_data = [
            {
                "company_name": f"TechCorp Solutions {datetime.now().strftime('%H%M%S')}",
                "domestic_international": "Domestic",
                "gst_number": f"27ABCDE{datetime.now().strftime('%H%M')}Z1Z5",
                "pan_number": f"ABCDE{datetime.now().strftime('%H%M')}F",
                "company_type_id": master_data['company-types'][0]['id'],
                "account_type_id": master_data['account-types'][0]['id'],
                "region_id": master_data['regions'][0]['id'],
                "business_type_id": master_data['business-types'][0]['id'],
                "industry_id": master_data['industries'][0]['id'],
                "employee_count": 250,
                "address": "123 Tech Park, Electronic City",
                "country_id": master_data['countries'][0]['id'],
                "annual_revenue": 50000000,
                "revenue_currency": "INR",
                "valid_gst": True,
                "active_status": True,
                "parent_linkage_valid": True
            },
            {
                "company_name": f"Global Innovations {datetime.now().strftime('%H%M%S')}",
                "domestic_international": "Domestic",
                "gst_number": f"29XYZAB{datetime.now().strftime('%H%M')}Z1Z5",
                "pan_number": f"XYZAB{datetime.now().strftime('%H%M')}F",
                "company_type_id": master_data['company-types'][0]['id'],
                "account_type_id": master_data['account-types'][0]['id'],
                "region_id": master_data['regions'][0]['id'],
                "business_type_id": master_data['business-types'][0]['id'],
                "industry_id": master_data['industries'][0]['id'],
                "employee_count": 150,
                "address": "456 Innovation Drive, Cyber City",
                "country_id": master_data['countries'][0]['id'],
                "annual_revenue": 30000000,
                "revenue_currency": "INR",
                "valid_gst": True,
                "active_status": True,
                "parent_linkage_valid": True
            }
        ]
        
        created_companies = []
        for company_data in companies_data:
            success, status, response = self.make_request('POST', 'companies', company_data)
            if success and 'id' in response:
                created_companies.append(response)
                self.created_items[f"company_{len(created_companies)}"] = response['id']
        
        if len(created_companies) >= 2:
            self.companies = created_companies
            return self.log_test("Create Test Companies", True, f"Created {len(created_companies)} companies")
        else:
            return self.log_test("Create Test Companies", False, f"Only created {len(created_companies)} companies")

    def test_contact_crud_operations(self):
        """Test Contact CRUD Operations"""
        print("\n👤 Testing Contact CRUD Operations...")
        
        if not self.companies:
            return self.log_test("Contact CRUD", False, "No companies available for testing")
        
        company_id = self.companies[0]['id']
        
        # Test 1: CREATE Contact
        contact_data = {
            "company_id": company_id,
            "salutation": "Mr.",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "email": f"rajesh.kumar.{datetime.now().strftime('%H%M%S')}@techcorp.com",
            "primary_phone": "+91-9876543210",
            "decision_maker": True,
            "spoc": False,
            "address": "123 Business District, Mumbai",
            "comments": "Key decision maker for technology purchases"
        }
        
        success, status, response = self.make_request('POST', 'contacts', contact_data)
        if success and 'id' in response:
            contact_id = response['id']
            self.created_items['contact_1'] = contact_id
            create_success = self.log_test("CREATE Contact", True, f"Contact ID: {contact_id}")
            
            # Test 2: GET specific contact
            success, status, get_response = self.make_request('GET', f'contacts/{contact_id}')
            get_success = self.log_test("GET Contact by ID", success, f"Status: {status}")
            
            # Test 3: UPDATE Contact
            update_data = {
                "decision_maker": False,
                "spoc": True,
                "comments": "Updated to SPOC role"
            }
            success, status, update_response = self.make_request('PUT', f'contacts/{contact_id}', update_data)
            update_success = self.log_test("UPDATE Contact", success, f"Status: {status}")
            
            # Test 4: GET contacts list
            success, status, list_response = self.make_request('GET', 'contacts')
            if success and 'contacts' in list_response:
                contacts_count = len(list_response['contacts'])
                list_success = self.log_test("GET Contacts List", True, f"Found {contacts_count} contacts")
            else:
                list_success = self.log_test("GET Contacts List", False, f"Status: {status}")
            
            # Test 5: DELETE Contact (soft delete)
            success, status, delete_response = self.make_request('DELETE', f'contacts/{contact_id}')
            delete_success = self.log_test("DELETE Contact", success, f"Status: {status}")
            
            return create_success and get_success and update_success and list_success and delete_success
        else:
            return self.log_test("CREATE Contact", False, f"Status: {status}, Response: {response}")

    def test_duplicate_detection(self):
        """Test Duplicate Detection"""
        print("\n🔍 Testing Duplicate Detection...")
        
        if not self.companies:
            return self.log_test("Duplicate Detection", False, "No companies available")
        
        company_id = self.companies[0]['id']
        
        # Create first contact
        contact_data_1 = {
            "company_id": company_id,
            "salutation": "Ms.",
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": f"priya.sharma.{datetime.now().strftime('%H%M%S')}@techcorp.com",
            "primary_phone": "+91-9876543211",
            "decision_maker": False,
            "spoc": False
        }
        
        success, status, response = self.make_request('POST', 'contacts', contact_data_1)
        if success and 'id' in response:
            contact_1_id = response['id']
            self.created_items['contact_duplicate_1'] = contact_1_id
            
            # Try to create duplicate with same email
            contact_data_2 = {
                "company_id": company_id,
                "salutation": "Ms.",
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": contact_data_1['email'],  # Same email
                "primary_phone": "+91-9876543212",
                "decision_maker": False,
                "spoc": False
            }
            
            success, status, response = self.make_request('POST', 'contacts', contact_data_2, 400)
            email_duplicate_success = self.log_test("Email Duplicate Detection", success, 
                                                  f"Correctly rejected duplicate email")
            
            # Try to create similar contact (same name, same company)
            contact_data_3 = {
                "company_id": company_id,
                "salutation": "Ms.",
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": f"priya.s.{datetime.now().strftime('%H%M%S')}@techcorp.com",  # Different email
                "primary_phone": "+91-9876543213",
                "decision_maker": False,
                "spoc": False
            }
            
            success, status, response = self.make_request('POST', 'contacts', contact_data_3, 400)
            similarity_success = self.log_test("Similarity Detection", success, 
                                             f"Correctly detected similar contact")
            
            return email_duplicate_success and similarity_success
        else:
            return self.log_test("Duplicate Detection Setup", False, f"Failed to create first contact")

    def test_spoc_management(self):
        """Test SPOC Management"""
        print("\n👑 Testing SPOC Management...")
        
        if len(self.companies) < 2:
            return self.log_test("SPOC Management", False, "Need at least 2 companies")
        
        company_1_id = self.companies[0]['id']
        company_2_id = self.companies[1]['id']
        
        # Create first SPOC for company 1
        spoc_1_data = {
            "company_id": company_1_id,
            "salutation": "Mr.",
            "first_name": "Amit",
            "last_name": "Patel",
            "email": f"amit.patel.{datetime.now().strftime('%H%M%S')}@company1.com",
            "primary_phone": "+91-9876543220",
            "decision_maker": True,
            "spoc": True
        }
        
        success, status, response = self.make_request('POST', 'contacts', spoc_1_data)
        if success and 'id' in response:
            spoc_1_id = response['id']
            self.created_items['spoc_1'] = spoc_1_id
            spoc_1_success = self.log_test("CREATE First SPOC", True, f"SPOC ID: {spoc_1_id}")
            
            # Try to create another SPOC for same company (should fail)
            spoc_2_data = {
                "company_id": company_1_id,  # Same company
                "salutation": "Ms.",
                "first_name": "Neha",
                "last_name": "Singh",
                "email": f"neha.singh.{datetime.now().strftime('%H%M%S')}@company1.com",
                "primary_phone": "+91-9876543221",
                "decision_maker": False,
                "spoc": True
            }
            
            success, status, response = self.make_request('POST', 'contacts', spoc_2_data, 400)
            spoc_conflict_success = self.log_test("SPOC Conflict Detection", success, 
                                                f"Correctly rejected second SPOC for same company")
            
            # Create SPOC for different company (should succeed)
            spoc_3_data = {
                "company_id": company_2_id,  # Different company
                "salutation": "Mr.",
                "first_name": "Vikram",
                "last_name": "Gupta",
                "email": f"vikram.gupta.{datetime.now().strftime('%H%M%S')}@company2.com",
                "primary_phone": "+91-9876543222",
                "decision_maker": True,
                "spoc": True
            }
            
            success, status, response = self.make_request('POST', 'contacts', spoc_3_data)
            if success and 'id' in response:
                self.created_items['spoc_2'] = response['id']
                spoc_different_company_success = self.log_test("SPOC Different Company", True, 
                                                             f"SPOC created for different company")
            else:
                spoc_different_company_success = self.log_test("SPOC Different Company", False, 
                                                             f"Status: {status}")
            
            return spoc_1_success and spoc_conflict_success and spoc_different_company_success
        else:
            return self.log_test("CREATE First SPOC", False, f"Status: {status}")

    def test_bulk_operations(self):
        """Test Bulk Operations"""
        print("\n📦 Testing Bulk Operations...")
        
        if not self.companies:
            return self.log_test("Bulk Operations", False, "No companies available")
        
        company_id = self.companies[0]['id']
        
        # Create multiple contacts for bulk testing
        contacts_data = [
            {
                "company_id": company_id,
                "salutation": "Mr.",
                "first_name": "Bulk",
                "last_name": "Contact1",
                "email": f"bulk1.{datetime.now().strftime('%H%M%S')}@test.com",
                "primary_phone": "+91-9876543230"
            },
            {
                "company_id": company_id,
                "salutation": "Ms.",
                "first_name": "Bulk",
                "last_name": "Contact2",
                "email": f"bulk2.{datetime.now().strftime('%H%M%S')}@test.com",
                "primary_phone": "+91-9876543231"
            }
        ]
        
        created_contact_ids = []
        for i, contact_data in enumerate(contacts_data):
            success, status, response = self.make_request('POST', 'contacts', contact_data)
            if success and 'id' in response:
                contact_id = response['id']
                created_contact_ids.append(contact_id)
                self.created_items[f'bulk_contact_{i+1}'] = contact_id
        
        if len(created_contact_ids) >= 2:
            create_success = self.log_test("CREATE Bulk Test Contacts", True, 
                                         f"Created {len(created_contact_ids)} contacts")
            
            # Test bulk deactivate
            bulk_deactivate_data = {
                "contact_ids": created_contact_ids,
                "action": "deactivate"
            }
            
            success, status, response = self.make_request('POST', 'contacts/bulk', bulk_deactivate_data)
            if success and 'updated_count' in response:
                deactivate_success = self.log_test("Bulk Deactivate", True, 
                                                 f"Deactivated {response['updated_count']} contacts")
            else:
                deactivate_success = self.log_test("Bulk Deactivate", False, f"Status: {status}")
            
            # Test bulk activate
            bulk_activate_data = {
                "contact_ids": created_contact_ids,
                "action": "activate"
            }
            
            success, status, response = self.make_request('POST', 'contacts/bulk', bulk_activate_data)
            if success and 'updated_count' in response:
                activate_success = self.log_test("Bulk Activate", True, 
                                                f"Activated {response['updated_count']} contacts")
            else:
                activate_success = self.log_test("Bulk Activate", False, f"Status: {status}")
            
            return create_success and deactivate_success and activate_success
        else:
            return self.log_test("CREATE Bulk Test Contacts", False, 
                               f"Only created {len(created_contact_ids)} contacts")

    def test_search_and_filtering(self):
        """Test Search and Filtering"""
        print("\n🔍 Testing Search and Filtering...")
        
        if not self.companies:
            return self.log_test("Search and Filtering", False, "No companies available")
        
        company_id = self.companies[0]['id']
        
        # Create a test contact for searching
        search_contact_data = {
            "company_id": company_id,
            "salutation": "Dr.",
            "first_name": "SearchTest",
            "last_name": "Contact",
            "email": f"searchtest.{datetime.now().strftime('%H%M%S')}@search.com",
            "primary_phone": "+91-9876543240",
            "decision_maker": True,
            "spoc": False
        }
        
        success, status, response = self.make_request('POST', 'contacts', search_contact_data)
        if success and 'id' in response:
            search_contact_id = response['id']
            self.created_items['search_contact'] = search_contact_id
            
            # Test search by name
            success, status, response = self.make_request('GET', f'contacts?search=SearchTest')
            if success and 'contacts' in response and len(response['contacts']) > 0:
                name_search_success = self.log_test("Search by Name", True, 
                                                  f"Found {len(response['contacts'])} contacts")
            else:
                name_search_success = self.log_test("Search by Name", False, f"Status: {status}")
            
            # Test filter by company
            success, status, response = self.make_request('GET', f'contacts?company_id={company_id}')
            if success and 'contacts' in response:
                company_filter_success = self.log_test("Filter by Company", True, 
                                                     f"Found {len(response['contacts'])} contacts")
            else:
                company_filter_success = self.log_test("Filter by Company", False, f"Status: {status}")
            
            # Test filter by decision maker
            success, status, response = self.make_request('GET', 'contacts?decision_maker=true')
            if success and 'contacts' in response:
                decision_maker_filter_success = self.log_test("Filter by Decision Maker", True, 
                                                            f"Found {len(response['contacts'])} decision makers")
            else:
                decision_maker_filter_success = self.log_test("Filter by Decision Maker", False, 
                                                            f"Status: {status}")
            
            # Test pagination
            success, status, response = self.make_request('GET', 'contacts?page=1&limit=5')
            if success and 'contacts' in response and 'total_pages' in response:
                pagination_success = self.log_test("Pagination", True, 
                                                 f"Page 1, Total pages: {response['total_pages']}")
            else:
                pagination_success = self.log_test("Pagination", False, f"Status: {status}")
            
            return name_search_success and company_filter_success and decision_maker_filter_success and pagination_success
        else:
            return self.log_test("CREATE Search Test Contact", False, f"Status: {status}")

    def test_export_functionality(self):
        """Test Export Functionality"""
        print("\n📤 Testing Export Functionality...")
        
        success, status, response = self.make_request('GET', 'contacts/export')
        if success and isinstance(response, list):
            return self.log_test("Export Contacts", True, f"Exported {len(response)} contacts")
        else:
            return self.log_test("Export Contacts", False, f"Status: {status}")

    def test_real_world_scenarios(self):
        """Test Real-world Scenarios"""
        print("\n🌍 Testing Real-world Scenarios...")
        
        if not self.companies:
            return self.log_test("Real-world Scenarios", False, "No companies available")
        
        company_id = self.companies[0]['id']
        
        # Scenario 1: Complete contact creation with all fields
        complete_contact_data = {
            "company_id": company_id,
            "salutation": "Mr.",
            "first_name": "Arjun",
            "middle_name": "Kumar",
            "last_name": "Reddy",
            "email": f"arjun.reddy.{datetime.now().strftime('%H%M%S')}@realworld.com",
            "primary_phone": "+91-9876543250",
            "decision_maker": True,
            "spoc": False,
            "address": "Plot 123, Hi-Tech City, Hyderabad, Telangana 500081",
            "comments": "CTO of the company, handles all technology decisions",
            "option": "Email preferred"
        }
        
        success, status, response = self.make_request('POST', 'contacts', complete_contact_data)
        if success and 'id' in response:
            complete_contact_id = response['id']
            self.created_items['complete_contact'] = complete_contact_id
            complete_creation_success = self.log_test("Complete Contact Creation", True, 
                                                    f"Contact ID: {complete_contact_id}")
            
            # Scenario 2: Update contact to SPOC with force update
            spoc_update_data = {
                "spoc": True,
                "comments": "Promoted to SPOC role"
            }
            
            success, status, response = self.make_request('PUT', f'contacts/{complete_contact_id}', spoc_update_data)
            spoc_update_success = self.log_test("Update to SPOC", success, f"Status: {status}")
            
            # Scenario 3: Email uniqueness validation
            duplicate_email_data = {
                "company_id": company_id,
                "salutation": "Ms.",
                "first_name": "Different",
                "last_name": "Person",
                "email": complete_contact_data['email'],  # Same email
                "primary_phone": "+91-9876543251"
            }
            
            success, status, response = self.make_request('POST', 'contacts', duplicate_email_data, 400)
            email_validation_success = self.log_test("Email Uniqueness Validation", success, 
                                                   f"Correctly rejected duplicate email")
            
            return complete_creation_success and spoc_update_success and email_validation_success
        else:
            return self.log_test("Complete Contact Creation", False, f"Status: {status}")

    def run_contact_management_tests(self):
        """Run all Contact Management tests"""
        print("🚀 Starting Contact Management Backend API Tests")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Failed to setup test data. Cannot proceed with contact tests.")
            return False
        
        # Run all contact tests
        test_results = []
        test_results.append(("Contact CRUD Operations", self.test_contact_crud_operations()))
        test_results.append(("Duplicate Detection", self.test_duplicate_detection()))
        test_results.append(("SPOC Management", self.test_spoc_management()))
        test_results.append(("Bulk Operations", self.test_bulk_operations()))
        test_results.append(("Search and Filtering", self.test_search_and_filtering()))
        test_results.append(("Export Functionality", self.test_export_functionality()))
        test_results.append(("Real-world Scenarios", self.test_real_world_scenarios()))
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 CONTACT MANAGEMENT TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 CONTACT TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ContactManagementTester()
    success = tester.run_contact_management_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())