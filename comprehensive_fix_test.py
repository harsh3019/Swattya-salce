#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Recently Implemented Fixes
Testing authentication, lead creation fixes, opportunity CRUD, stage management, and master data APIs
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://lead-opp-crm.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class ComprehensiveFixTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.created_lead_id = None
        self.created_opportunity_id = None
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results.append(result)
        print(result)
        
    def authenticate(self):
        """Test admin authentication with specific credentials"""
        print("\n🔐 TESTING AUTHENTICATION FIRST")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                
                user_data = data.get("user", {})
                self.log_test(
                    "Admin Login with admin/admin123", 
                    True, 
                    f"Token received, User: {user_data.get('username')}, Email: {user_data.get('email')}, Role ID: {user_data.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Login with admin/admin123", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login with admin/admin123", False, f"Exception: {str(e)}")
            return False
    
    def test_lead_creation_fixes(self):
        """Test lead creation fixes with billing_type field and authentication headers"""
        print("\n📝 TESTING LEAD CREATION FIXES")
        print("=" * 50)
        
        # Test 1: Lead creation with Tender type and billing_type field
        try:
            lead_data_tender = {
                "tender_type": "Tender",
                "billing_type": "prepaid",  # This field should be included when tender_type is Tender
                "sub_tender_type_id": "cdb2e33b-8971-41c2-9582-af66fdda2af4",  # Government - Municipal
                "project_title": "Test Lead - Tender Type with Billing",
                "company_id": "df3d438f-d614-4e72-a666-44c2cf600f44",  # Valid company ID
                "state": "Maharashtra",
                "lead_subtype": "Direct",
                "source": "Website",
                "product_service_id": "f9faac48-fc91-421a-bc43-19550c04036b",  # Mobile App Development
                "is_enquiry": False,
                "expected_orc": 50000,
                "revenue": 50000,
                "status": "New",
                "lead_owner": "078ed9d6-a65e-401f-a83f-a18432c9016f",  # Valid user ID
                "approval_status": "Pending",
                "checklist_completed": False
            }
            
            response = requests.post(
                f"{self.base_url}/leads",
                headers=self.headers,  # Authentication headers included
                json=lead_data_tender,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                lead_id = data.get('id')
                self.created_lead_id = lead_id
                
                # Check if billing_type was properly saved
                billing_type = data.get('billing_type')
                if billing_type == "prepaid":
                    self.log_test(
                        "POST /api/leads with Tender type and billing_type", 
                        True, 
                        f"Lead created with ID: {lead_id}, billing_type: {billing_type}"
                    )
                else:
                    self.log_test(
                        "POST /api/leads with Tender type and billing_type", 
                        False, 
                        f"billing_type not properly saved. Expected: prepaid, Got: {billing_type}"
                    )
            else:
                self.log_test(
                    "POST /api/leads with Tender type and billing_type", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                
        except Exception as e:
            self.log_test("POST /api/leads with Tender type and billing_type", False, f"Exception: {str(e)}")
        
        # Test 2: Lead creation with Pre-Tender type and billing_type field
        try:
            lead_data_pre_tender = {
                "tender_type": "Pre-Tender",
                "billing_type": "postpaid",  # This field should be included when tender_type is Pre-Tender
                "sub_tender_type_id": "4304d03c-ccbd-4dac-af97-0e60f88eb8c9",  # Private - Enterprise
                "project_title": "Test Lead - Pre-Tender Type with Billing",
                "company_id": "test-company-id",
                "state": "Karnataka",
                "lead_subtype": "Referral",
                "source": "Email",
                "product_service_id": "f5b77540-b4d7-45f8-b6dd-95630486b299",  # Cloud Services
                "is_enquiry": True,
                "expected_orc": 75000,
                "revenue": 75000,
                "status": "New",
                "lead_owner": "test-user-id",
                "approval_status": "Pending",
                "checklist_completed": False
            }
            
            response = requests.post(
                f"{self.base_url}/leads",
                headers=self.headers,  # Authentication headers included
                json=lead_data_pre_tender,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                lead_id = data.get('id')
                billing_type = data.get('billing_type')
                
                if billing_type == "postpaid":
                    self.log_test(
                        "POST /api/leads with Pre-Tender type and billing_type", 
                        True, 
                        f"Lead created with ID: {lead_id}, billing_type: {billing_type}"
                    )
                else:
                    self.log_test(
                        "POST /api/leads with Pre-Tender type and billing_type", 
                        False, 
                        f"billing_type not properly saved. Expected: postpaid, Got: {billing_type}"
                    )
            else:
                self.log_test(
                    "POST /api/leads with Pre-Tender type and billing_type", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                
        except Exception as e:
            self.log_test("POST /api/leads with Pre-Tender type and billing_type", False, f"Exception: {str(e)}")
        
        # Test 3: Verify authentication headers are properly included
        try:
            # Test without authentication headers (should fail)
            response_no_auth = requests.post(
                f"{self.base_url}/leads",
                json={
                    "tender_type": "Non-Tender",
                    "project_title": "Test Lead - No Auth",
                    "company_id": "test-company-id",
                    "state": "Delhi",
                    "lead_subtype": "Direct",
                    "source": "Phone",
                    "product_service_id": "test-product-service-id",
                    "lead_owner": "test-user-id"
                },
                timeout=10
            )
            
            if response_no_auth.status_code == 401:
                self.log_test(
                    "Lead creation without authentication headers", 
                    True, 
                    "Properly rejected with 401 Unauthorized"
                )
            else:
                self.log_test(
                    "Lead creation without authentication headers", 
                    False, 
                    f"Expected 401, got {response_no_auth.status_code}"
                )
                
        except Exception as e:
            self.log_test("Lead creation without authentication headers", False, f"Exception: {str(e)}")
    
    def test_opportunity_crud_apis(self):
        """Test Opportunity CRUD APIs with proper authentication"""
        print("\n🎯 TESTING OPPORTUNITY CRUD APIs")
        print("=" * 50)
        
        # Test 1: Create new opportunity (POST /api/opportunities)
        try:
            # First get required master data
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            companies_response = requests.get(f"{self.base_url}/companies", headers=self.headers, timeout=10)
            users_response = requests.get(f"{self.base_url}/users", headers=self.headers, timeout=10)
            
            if all(r.status_code == 200 for r in [stages_response, currencies_response, companies_response, users_response]):
                stages = stages_response.json()
                currencies = currencies_response.json()
                companies = companies_response.json()
                users = users_response.json()
                
                # Find required data
                l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), stages[0] if stages else None)
                inr_currency = next((c for c in currencies if c.get('code') == 'INR'), currencies[0] if currencies else None)
                test_company = companies[0] if companies else None
                test_user = users[0] if users else None
                
                if all([l1_stage, inr_currency, test_company, test_user]):
                    opportunity_data = {
                        "project_title": "Test Opportunity - CRUD Testing",
                        "company_id": test_company['id'],
                        "stage_id": l1_stage['id'],
                        "expected_revenue": 150000,
                        "currency_id": inr_currency['id'],
                        "lead_owner_id": test_user['id'],
                        "win_probability": 60
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/opportunities",
                        headers=self.headers,
                        json=opportunity_data,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        self.created_opportunity_id = data.get('id')
                        opportunity_id = data.get('opportunity_id')
                        
                        # Verify weighted_revenue calculation
                        expected_weighted = 150000 * 60 / 100  # expected_revenue * win_probability / 100
                        actual_weighted = data.get('weighted_revenue', 0)
                        
                        if opportunity_id and opportunity_id.startswith('OPP-'):
                            self.log_test(
                                "POST /api/opportunities (create new opportunity)", 
                                True, 
                                f"Created opportunity {opportunity_id}, weighted_revenue: {actual_weighted} (expected: {expected_weighted})"
                            )
                        else:
                            self.log_test(
                                "POST /api/opportunities (create new opportunity)", 
                                False, 
                                f"Invalid opportunity ID format: {opportunity_id}"
                            )
                    else:
                        self.log_test(
                            "POST /api/opportunities (create new opportunity)", 
                            False, 
                            f"Status: {response.status_code}, Response: {response.text[:300]}"
                        )
                else:
                    self.log_test("POST /api/opportunities (create new opportunity)", False, "Required master data not available")
            else:
                self.log_test("POST /api/opportunities (create new opportunity)", False, "Could not get required master data")
                
        except Exception as e:
            self.log_test("POST /api/opportunities (create new opportunity)", False, f"Exception: {str(e)}")
        
        # Test 2: Get single opportunity (GET /api/opportunities/{id})
        if self.created_opportunity_id:
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    project_title = data.get('project_title', data.get('name', 'Unknown'))
                    self.log_test(
                        "GET /api/opportunities/{id} (get single opportunity)", 
                        True, 
                        f"Retrieved opportunity: {project_title}"
                    )
                else:
                    self.log_test(
                        "GET /api/opportunities/{id} (get single opportunity)", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text[:300]}"
                    )
                    
            except Exception as e:
                self.log_test("GET /api/opportunities/{id} (get single opportunity)", False, f"Exception: {str(e)}")
        
        # Test 3: Test opportunity list endpoint (GET /api/opportunities)
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict) and 'opportunities' in data:
                    opportunities = data['opportunities']
                    total = data.get('total', len(opportunities))
                elif isinstance(data, list):
                    opportunities = data
                    total = len(opportunities)
                else:
                    opportunities = []
                    total = 0
                
                self.log_test(
                    "GET /api/opportunities (list all opportunities)", 
                    True, 
                    f"Retrieved {total} opportunities from list endpoint"
                )
            else:
                self.log_test(
                    "GET /api/opportunities (list all opportunities)", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                
        except Exception as e:
            self.log_test("GET /api/opportunities (list all opportunities)", False, f"Exception: {str(e)}")
    
    def test_stage_management(self):
        """Test Stage Management with new PATCH endpoint"""
        print("\n🔄 TESTING STAGE MANAGEMENT")
        print("=" * 50)
        
        if not self.created_opportunity_id:
            self.log_test("Stage Management Testing", False, "No opportunity available for stage testing")
            return
        
        # Test 1: Get available stages first
        try:
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            
            if stages_response.status_code == 200:
                stages = stages_response.json()
                l2_stage = next((s for s in stages if s.get('stage_code') == 'L2'), None)
                
                if l2_stage:
                    # Test 2: Update opportunity stage with valid stage_id
                    try:
                        stage_update_data = {
                            "stage_id": l2_stage['id'],
                            "stage_change_notes": "Moving to L2 stage for backend testing"
                        }
                        
                        response = requests.patch(
                            f"{self.base_url}/opportunities/{self.created_opportunity_id}/stage",
                            headers=self.headers,
                            json=stage_update_data,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            self.log_test(
                                "PATCH /api/opportunities/{id}/stage (valid stage update)", 
                                True, 
                                f"Stage updated successfully to L2, notes saved"
                            )
                        else:
                            self.log_test(
                                "PATCH /api/opportunities/{id}/stage (valid stage update)", 
                                False, 
                                f"Status: {response.status_code}, Response: {response.text[:300]}"
                            )
                            
                    except Exception as e:
                        self.log_test("PATCH /api/opportunities/{id}/stage (valid stage update)", False, f"Exception: {str(e)}")
                    
                    # Test 3: Test stage validation with invalid stage_id
                    try:
                        invalid_stage_data = {
                            "stage_id": "invalid-stage-id-12345",
                            "stage_change_notes": "Testing invalid stage ID"
                        }
                        
                        response = requests.patch(
                            f"{self.base_url}/opportunities/{self.created_opportunity_id}/stage",
                            headers=self.headers,
                            json=invalid_stage_data,
                            timeout=10
                        )
                        
                        if response.status_code == 404:
                            self.log_test(
                                "PATCH /api/opportunities/{id}/stage (invalid stage_id validation)", 
                                True, 
                                "Properly returned 404 for invalid stage_id"
                            )
                        else:
                            self.log_test(
                                "PATCH /api/opportunities/{id}/stage (invalid stage_id validation)", 
                                False, 
                                f"Expected 404, got {response.status_code}"
                            )
                            
                    except Exception as e:
                        self.log_test("PATCH /api/opportunities/{id}/stage (invalid stage_id validation)", False, f"Exception: {str(e)}")
                
                else:
                    self.log_test("Stage Management Testing", False, "L2 stage not found in master data")
            else:
                self.log_test("Stage Management Testing", False, "Could not get stages master data")
                
        except Exception as e:
            self.log_test("Stage Management Testing", False, f"Exception: {str(e)}")
    
    def test_master_data_apis(self):
        """Test Master Data APIs for opportunity forms"""
        print("\n📊 TESTING MASTER DATA APIs")
        print("=" * 50)
        
        # Test cases: (endpoint, expected_name, expected_min_count)
        master_data_tests = [
            ("/mst/stages", "L1-L8 Stages", 8),
            ("/companies", "Company Data", 1),
            ("/mst/currencies", "Currency Options", 3),
            ("/users", "User Data for Lead Owners", 1),
        ]
        
        for endpoint, name, expected_min in master_data_tests:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        count = len(data)
                        items = data
                    elif isinstance(data, dict):
                        if 'data' in data:
                            count = len(data['data'])
                            items = data['data']
                        else:
                            count = len(data)
                            items = [data]
                    else:
                        count = 0
                        items = []
                    
                    if count >= expected_min:
                        # Additional validation for stages
                        if endpoint == "/mst/stages":
                            stage_codes = [item.get('stage_code', '') for item in items]
                            l_stages = [code for code in stage_codes if code.startswith('L')]
                            if len(l_stages) >= 8:
                                self.log_test(
                                    f"GET {endpoint}", 
                                    True, 
                                    f"Retrieved {count} {name.lower()}, L-stages found: {len(l_stages)}"
                                )
                            else:
                                self.log_test(
                                    f"GET {endpoint}", 
                                    False, 
                                    f"Only {len(l_stages)} L-stages found, expected at least 8"
                                )
                        else:
                            self.log_test(
                                f"GET {endpoint}", 
                                True, 
                                f"Retrieved {count} {name.lower()} (expected min: {expected_min})"
                            )
                    else:
                        self.log_test(
                            f"GET {endpoint}", 
                            False, 
                            f"Only {count} {name.lower()} found, expected min: {expected_min}"
                        )
                else:
                    self.log_test(
                        f"GET {endpoint}", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text[:200]}"
                    )
                    
            except Exception as e:
                self.log_test(f"GET {endpoint}", False, f"Exception: {str(e)}")
    
    def test_business_logic_verification(self):
        """Test business logic verification"""
        print("\n🧮 TESTING BUSINESS LOGIC VERIFICATION")
        print("=" * 50)
        
        # Test weighted_revenue calculation
        if self.created_opportunity_id:
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    expected_revenue = data.get('expected_revenue', 0)
                    win_probability = data.get('win_probability', 0)
                    weighted_revenue = data.get('weighted_revenue', 0)
                    
                    # Calculate expected weighted revenue
                    expected_weighted = expected_revenue * win_probability / 100
                    
                    if abs(weighted_revenue - expected_weighted) < 0.01:  # Allow for floating point precision
                        self.log_test(
                            "Weighted Revenue Calculation", 
                            True, 
                            f"Correct calculation: {expected_revenue} * {win_probability}% = {weighted_revenue}"
                        )
                    else:
                        self.log_test(
                            "Weighted Revenue Calculation", 
                            False, 
                            f"Incorrect calculation: Expected {expected_weighted}, Got {weighted_revenue}"
                        )
                else:
                    self.log_test("Weighted Revenue Calculation", False, "Could not retrieve opportunity data")
                    
            except Exception as e:
                self.log_test("Weighted Revenue Calculation", False, f"Exception: {str(e)}")
        
        # Test opportunity ID generation format
        if self.created_opportunity_id:
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    opportunity_id = data.get('opportunity_id', '')
                    
                    # Verify OPP-XXXXXXX format
                    if opportunity_id.startswith('OPP-') and len(opportunity_id) == 11:
                        self.log_test(
                            "Opportunity ID Generation Format", 
                            True, 
                            f"Correct format: {opportunity_id}"
                        )
                    else:
                        self.log_test(
                            "Opportunity ID Generation Format", 
                            False, 
                            f"Incorrect format: {opportunity_id} (expected OPP-XXXXXXX)"
                        )
                else:
                    self.log_test("Opportunity ID Generation Format", False, "Could not retrieve opportunity data")
                    
            except Exception as e:
                self.log_test("Opportunity ID Generation Format", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in the specified order"""
        print("🚀 STARTING COMPREHENSIVE FIX TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Run all test suites in order
        self.test_lead_creation_fixes()
        self.test_opportunity_crud_apis()
        self.test_stage_management()
        self.test_master_data_apis()
        self.test_business_logic_verification()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE FIX TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = ComprehensiveFixTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()