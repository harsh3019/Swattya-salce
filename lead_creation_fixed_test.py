#!/usr/bin/env python3
"""
Lead Creation Functionality Testing - Fixed Version
Testing comprehensive lead creation APIs with correct data structure
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://sawayatta-erp-1.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class LeadCreationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.company_id = None
        self.service_id = None
        self.subtender_id = None
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def authenticate(self):
        """Test admin authentication"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_data = data.get("user", {})
                username = user_data.get("username")
                role_id = user_data.get("role_id")
                
                self.log_test("Admin Authentication", True, 
                            f"Login successful. Username: {username}, Role ID: {role_id}")
                return True
            else:
                self.log_test("Admin Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_master_data(self):
        """Get required master data for lead creation"""
        try:
            # Get companies
            companies_response = self.session.get(f"{BACKEND_URL}/companies")
            if companies_response.status_code == 200:
                companies = companies_response.json()
                if isinstance(companies, list) and len(companies) > 0:
                    self.company_id = companies[0].get("id")
                elif isinstance(companies, dict) and companies.get("data"):
                    self.company_id = companies["data"][0].get("id")
            
            # Get product services
            services_response = self.session.get(f"{BACKEND_URL}/product-services")
            if services_response.status_code == 200:
                services = services_response.json()
                if isinstance(services, list) and len(services) > 0:
                    self.service_id = services[0].get("id")
            
            # Get sub-tender types
            subtender_response = self.session.get(f"{BACKEND_URL}/sub-tender-types")
            if subtender_response.status_code == 200:
                subtenders = subtender_response.json()
                if isinstance(subtenders, list) and len(subtenders) > 0:
                    self.subtender_id = subtenders[0].get("id")
            
            self.log_test("Master Data Collection", True, 
                        f"Company ID: {self.company_id}, Service ID: {self.service_id}, Sub-tender ID: {self.subtender_id}")
            
        except Exception as e:
            self.log_test("Master Data Collection", False, f"Exception: {str(e)}")
    
    def test_master_data_apis(self):
        """Test all master data APIs required for lead creation"""
        master_data_tests = [
            ("Company Types", "/company-types"),
            ("Companies", "/companies"),
            ("Sub-Tender Types", "/sub-tender-types"),
            ("Product Services", "/product-services"),
            ("Users", "/users")
        ]
        
        for test_name, endpoint in master_data_tests:
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else len(data.get('data', []))
                    self.log_test(f"GET {endpoint}", True, f"Retrieved {count} records")
                else:
                    self.log_test(f"GET {endpoint}", False, 
                                f"Status {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"GET {endpoint}", False, f"Exception: {str(e)}")
    
    def test_lead_creation_without_checklist(self):
        """Test lead creation without checklist_completed field - using correct data structure"""
        
        # Correct lead data structure based on backend validation
        lead_data = {
            "tender_type": "Tender",
            "billing_type": "prepaid",  # lowercase as per pattern
            "sub_tender_type_id": self.subtender_id,
            "project_title": "Test Company Lead Project",
            "company_id": self.company_id,
            "state": "Maharashtra",
            "lead_subtype": "Direct",
            "source": "Website",
            "product_service_id": self.service_id,
            "expected_orc": 500000.0,
            "revenue": 750000.0,
            "competitors": "CompetitorA, CompetitorB",
            "status": "New",
            "lead_owner": "admin",
            "approval_status": "Pending"
            # Note: No checklist_completed field
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
            
            if response.status_code == 201:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                self.log_test("Lead Creation (without checklist)", True, 
                            f"Lead created successfully with ID: {lead_id}")
                return lead_id
            else:
                self.log_test("Lead Creation (without checklist)", False, 
                            f"Status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Lead Creation (without checklist)", False, f"Exception: {str(e)}")
            return None
    
    def test_lead_creation_with_complete_data(self):
        """Test lead creation with complete lead data structure"""
        
        # Complete lead data structure with all required fields
        lead_data = {
            "tender_type": "Tender",
            "billing_type": "prepaid", 
            "sub_tender_type_id": self.subtender_id,
            "project_title": "Complete Test Project Implementation",
            "company_id": self.company_id,
            "state": "Karnataka",
            "lead_subtype": "Direct",
            "source": "Email Campaign",
            "product_service_id": self.service_id,
            "expected_orc": 750000.0,
            "revenue": 1000000.0,
            "competitors": "TechCorp, InnovateSoft",
            "status": "New",
            "lead_owner": "admin",
            "approval_status": "Pending"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
            
            if response.status_code == 201:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                self.log_test("Lead Creation (complete data)", True, 
                            f"Lead created with ID: {lead_id}")
                return lead_id
            else:
                self.log_test("Lead Creation (complete data)", False, 
                            f"Status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Lead Creation (complete data)", False, f"Exception: {str(e)}")
            return None
    
    def test_billing_type_logic(self):
        """Test billing type logic based on tender type"""
        
        test_cases = [
            {
                "name": "Tender + prepaid",
                "tender_type": "Tender",
                "billing_type": "prepaid",
                "should_work": True
            },
            {
                "name": "Pre-Tender + postpaid", 
                "tender_type": "Pre-Tender",
                "billing_type": "postpaid",
                "should_work": True
            },
            {
                "name": "Non-Tender (no billing type)",
                "tender_type": "Non-Tender", 
                "billing_type": None,
                "should_work": True
            }
        ]
        
        for test_case in test_cases:
            lead_data = {
                "tender_type": test_case["tender_type"],
                "project_title": f"Test {test_case['name']} Project",
                "company_id": self.company_id,
                "state": "Gujarat",
                "lead_subtype": "Direct",
                "source": "Website",
                "product_service_id": self.service_id,
                "status": "New",
                "lead_owner": "admin"
            }
            
            if test_case["billing_type"]:
                lead_data["billing_type"] = test_case["billing_type"]
            
            # Add sub_tender_type_id for Tender types
            if test_case["tender_type"] in ["Tender", "Pre-Tender"]:
                lead_data["sub_tender_type_id"] = self.subtender_id
                lead_data["expected_orc"] = 300000.0
            
            try:
                response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
                
                if test_case["should_work"]:
                    if response.status_code == 201:
                        data = response.json()
                        lead_id = data.get("lead_id") or data.get("id")
                        self.log_test(f"Billing Logic: {test_case['name']}", True, 
                                    f"Created lead {lead_id}")
                    else:
                        self.log_test(f"Billing Logic: {test_case['name']}", False, 
                                    f"Expected success but got {response.status_code}: {response.text}")
                else:
                    if response.status_code != 201:
                        self.log_test(f"Billing Logic: {test_case['name']}", True, 
                                    f"Correctly rejected with {response.status_code}")
                    else:
                        self.log_test(f"Billing Logic: {test_case['name']}", False, 
                                    "Expected rejection but creation succeeded")
                        
            except Exception as e:
                self.log_test(f"Billing Logic: {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_lead_retrieval(self):
        """Test lead retrieval APIs"""
        
        # Test GET /api/leads (list all leads)
        try:
            response = self.session.get(f"{BACKEND_URL}/leads")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    leads = data.get("leads", data.get("data", []))
                    total = data.get("total", len(leads))
                else:
                    leads = data
                    total = len(leads)
                
                self.log_test("GET /api/leads (list)", True, 
                            f"Retrieved {total} leads")
                
                # Test individual lead retrieval if we have leads
                if leads and len(leads) > 0:
                    lead_id = leads[0].get("id") or leads[0].get("lead_id")
                    if lead_id:
                        detail_response = self.session.get(f"{BACKEND_URL}/leads/{lead_id}")
                        
                        if detail_response.status_code == 200:
                            lead_detail = detail_response.json()
                            project_title = lead_detail.get("project_title", "Unknown")
                            self.log_test("GET /api/leads/{id} (detail)", True, 
                                        f"Retrieved lead details for {lead_id}: {project_title}")
                        else:
                            self.log_test("GET /api/leads/{id} (detail)", False, 
                                        f"Status {detail_response.status_code}: {detail_response.text}")
                else:
                    self.log_test("GET /api/leads/{id} (detail)", False, 
                                "No leads available to test individual retrieval")
            else:
                self.log_test("GET /api/leads (list)", False, 
                            f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/leads (list)", False, f"Exception: {str(e)}")
    
    def test_lead_id_generation(self):
        """Test that lead ID generation works in LEAD-XXXXXXX format"""
        
        lead_data = {
            "tender_type": "Non-Tender",
            "project_title": "Lead ID Generation Test Project",
            "company_id": self.company_id,
            "state": "Tamil Nadu",
            "lead_subtype": "Direct",
            "source": "Email",
            "product_service_id": self.service_id,
            "status": "New",
            "lead_owner": "admin"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
            
            if response.status_code == 201:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                
                # Check if lead ID follows LEAD-XXXXXXX format
                if lead_id and lead_id.startswith("LEAD-") and len(lead_id) == 12:
                    self.log_test("Lead ID Generation", True, 
                                f"Generated proper lead ID: {lead_id}")
                else:
                    self.log_test("Lead ID Generation", False, 
                                f"Invalid lead ID format: {lead_id}")
            else:
                self.log_test("Lead ID Generation", False, 
                            f"Lead creation failed: {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Lead ID Generation", False, f"Exception: {str(e)}")
    
    def test_checklist_requirement_removed(self):
        """Test that checklist_completed field is no longer required"""
        
        # Test 1: Lead creation without checklist_completed field
        lead_data_no_checklist = {
            "tender_type": "Non-Tender",
            "project_title": "No Checklist Test Project",
            "company_id": self.company_id,
            "state": "Rajasthan",
            "lead_subtype": "Direct",
            "source": "Social Media",
            "product_service_id": self.service_id,
            "status": "New",
            "lead_owner": "admin"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data_no_checklist)
            
            if response.status_code == 201:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                self.log_test("Checklist Not Required", True, 
                            f"Lead created without checklist field: {lead_id}")
            else:
                self.log_test("Checklist Not Required", False, 
                            f"Lead creation failed: {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Checklist Not Required", False, f"Exception: {str(e)}")
        
        # Test 2: Lead creation with checklist_completed=false (should still work)
        lead_data_with_checklist = {
            "tender_type": "Non-Tender",
            "project_title": "With Checklist False Test Project",
            "company_id": self.company_id,
            "state": "Punjab",
            "lead_subtype": "Direct",
            "source": "Referral",
            "product_service_id": self.service_id,
            "status": "New",
            "lead_owner": "admin",
            "checklist_completed": False
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data_with_checklist)
            
            if response.status_code == 201:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                self.log_test("Checklist False Allowed", True, 
                            f"Lead created with checklist_completed=false: {lead_id}")
            else:
                self.log_test("Checklist False Allowed", False, 
                            f"Lead creation failed: {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Checklist False Allowed", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all lead creation tests"""
        print("🚀 STARTING LEAD CREATION FUNCTIONALITY TESTING (FIXED VERSION)")
        print("=" * 70)
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Step 2: Get Master Data
        print("🔍 COLLECTING MASTER DATA")
        print("-" * 30)
        self.get_master_data()
        
        # Step 3: Master Data APIs
        print("📊 TESTING MASTER DATA APIs")
        print("-" * 30)
        self.test_master_data_apis()
        
        # Step 4: Lead Creation Tests
        print("🎯 TESTING LEAD CREATION")
        print("-" * 30)
        self.test_lead_creation_without_checklist()
        self.test_lead_creation_with_complete_data()
        
        # Step 5: Checklist Requirement Removal
        print("✅ TESTING CHECKLIST REQUIREMENT REMOVAL")
        print("-" * 30)
        self.test_checklist_requirement_removed()
        
        # Step 6: Billing Type Logic
        print("💰 TESTING BILLING TYPE LOGIC")
        print("-" * 30)
        self.test_billing_type_logic()
        
        # Step 7: Lead Retrieval
        print("📋 TESTING LEAD RETRIEVAL")
        print("-" * 30)
        self.test_lead_retrieval()
        
        # Step 8: Lead ID Generation
        print("🔢 TESTING LEAD ID GENERATION")
        print("-" * 30)
        self.test_lead_id_generation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print("\n✅ CRITICAL SUCCESS CRITERIA:")
        
        # Check critical criteria
        auth_success = any(r["test"] == "Admin Authentication" and r["success"] for r in self.test_results)
        lead_creation_success = any("Lead Creation" in r["test"] and r["success"] for r in self.test_results)
        master_data_success = any("GET /" in r["test"] and r["success"] for r in self.test_results)
        checklist_removed = any("Checklist" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"  • Admin Authentication: {'✅ PASS' if auth_success else '❌ FAIL'}")
        print(f"  • Lead Creation Working: {'✅ PASS' if lead_creation_success else '❌ FAIL'}")
        print(f"  • Master Data APIs: {'✅ PASS' if master_data_success else '❌ FAIL'}")
        print(f"  • Checklist Requirement Removed: {'✅ PASS' if checklist_removed else '❌ FAIL'}")
        
        # Overall assessment
        if passed_tests >= total_tests * 0.8:  # 80% success rate
            print(f"\n🎉 OVERALL ASSESSMENT: EXCELLENT - Lead Creation functionality is working well!")
        elif passed_tests >= total_tests * 0.6:  # 60% success rate
            print(f"\n⚠️ OVERALL ASSESSMENT: GOOD - Most functionality working, some issues to address")
        else:
            print(f"\n❌ OVERALL ASSESSMENT: NEEDS ATTENTION - Multiple critical issues found")

if __name__ == "__main__":
    tester = LeadCreationTester()
    tester.run_all_tests()