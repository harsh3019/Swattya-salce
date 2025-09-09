#!/usr/bin/env python3
"""
Lead Creation Functionality Testing - Fixed Lead Creation after removing checklist requirement
Testing comprehensive lead creation APIs with correct data structure
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://lead-opp-crm.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class LeadCreationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
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
        """Test lead creation without checklist_completed field"""
        
        # Get required master data first
        companies_response = self.session.get(f"{BACKEND_URL}/companies")
        company_id = None
        if companies_response.status_code == 200:
            companies = companies_response.json()
            if isinstance(companies, list) and len(companies) > 0:
                company_id = companies[0].get("id")
            elif isinstance(companies, dict) and companies.get("data"):
                company_id = companies["data"][0].get("id")
        
        services_response = self.session.get(f"{BACKEND_URL}/product-services")
        service_id = None
        if services_response.status_code == 200:
            services = services_response.json()
            if isinstance(services, list) and len(services) > 0:
                service_id = services[0].get("id")
        
        # Correct lead data structure without checklist_completed field
        lead_data = {
            "tender_type": "Non-Tender",  # Use Non-Tender to avoid billing_type requirement
            "project_title": "Test Company Lead",
            "company_id": company_id,
            "state": "Maharashtra",
            "lead_subtype": "Direct",
            "source": "Website",
            "product_service_id": service_id,
            "lead_owner": "admin"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                self.log_test("Lead Creation (without checklist)", True, 
                            f"Lead created successfully with ID: {lead_id} - NO checklist validation error!")
                return lead_id
            else:
                error_msg = response.text
                if "checklist" in error_msg.lower():
                    self.log_test("Lead Creation (without checklist)", False, 
                                f"CRITICAL: Still getting checklist validation error: {error_msg}")
                else:
                    self.log_test("Lead Creation (without checklist)", False, 
                                f"Status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Lead Creation (without checklist)", False, f"Exception: {str(e)}")
            return None
    
    def test_lead_creation_with_complete_data(self):
        """Test lead creation with complete lead data structure"""
        
        # Get a company ID first
        companies_response = self.session.get(f"{BACKEND_URL}/companies")
        company_id = None
        if companies_response.status_code == 200:
            companies = companies_response.json()
            if isinstance(companies, list) and len(companies) > 0:
                company_id = companies[0].get("id")
            elif isinstance(companies, dict) and companies.get("data"):
                company_id = companies["data"][0].get("id")
        
        # Get a product service ID
        services_response = self.session.get(f"{BACKEND_URL}/product-services")
        service_id = None
        if services_response.status_code == 200:
            services = services_response.json()
            if isinstance(services, list) and len(services) > 0:
                service_id = services[0].get("id")
        
        # Get a sub-tender type ID
        subtender_response = self.session.get(f"{BACKEND_URL}/sub-tender-types")
        subtender_id = None
        if subtender_response.status_code == 200:
            subtenders = subtender_response.json()
            if isinstance(subtenders, list) and len(subtenders) > 0:
                subtender_id = subtenders[0].get("id")
        
        # Complete lead data structure
        lead_data = {
            "tender_type": "Tender",
            "billing_type": "prepaid",  # lowercase as required by API
            "sub_tender_type_id": subtender_id,
            "project_title": "Test Project Implementation",
            "company_id": company_id,
            "state": "Maharashtra",
            "lead_subtype": "Direct",
            "source": "Website",
            "product_service_id": service_id,
            "expected_orc": 500000.0,
            "revenue": 750000.0,
            "competitors": "CompetitorA, CompetitorB",
            "status": "New",
            "lead_owner": "admin",
            "approval_status": "Pending"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/leads", json=lead_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                lead_id = data.get("lead_id") or data.get("id")
                self.log_test("Lead Creation (complete data)", True, 
                            f"Complete lead created with ID: {lead_id}")
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
                "name": "Tender + Prepaid",
                "tender_type": "Tender",
                "billing_type": "Prepaid",
                "should_work": True
            },
            {
                "name": "Pre-Tender + Postpaid", 
                "tender_type": "Pre-Tender",
                "billing_type": "Postpaid",
                "should_work": True
            },
            {
                "name": "RFP (no billing type)",
                "tender_type": "RFP", 
                "billing_type": None,
                "should_work": True
            }
        ]
        
        # Get required IDs
        companies_response = self.session.get(f"{BACKEND_URL}/companies")
        company_id = None
        if companies_response.status_code == 200:
            companies = companies_response.json()
            if isinstance(companies, list) and len(companies) > 0:
                company_id = companies[0].get("id")
            elif isinstance(companies, dict) and companies.get("data"):
                company_id = companies["data"][0].get("id")
        
        for test_case in test_cases:
            lead_data = {
                "tender_type": test_case["tender_type"],
                "project_title": f"Test {test_case['name']} Project",
                "company_id": company_id,
                "state": "Maharashtra",
                "lead_subtype": "Direct",
                "source": "Website",
                "status": "New",
                "lead_owner": "admin"
            }
            
            if test_case["billing_type"]:
                lead_data["billing_type"] = test_case["billing_type"]
            
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
                            self.log_test("GET /api/leads/{id} (detail)", True, 
                                        f"Retrieved lead details for {lead_id}")
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
        
        # Get required data
        companies_response = self.session.get(f"{BACKEND_URL}/companies")
        company_id = None
        if companies_response.status_code == 200:
            companies = companies_response.json()
            if isinstance(companies, list) and len(companies) > 0:
                company_id = companies[0].get("id")
            elif isinstance(companies, dict) and companies.get("data"):
                company_id = companies["data"][0].get("id")
        
        lead_data = {
            "tender_type": "Non-Tender",
            "project_title": "Lead ID Generation Test",
            "company_id": company_id,
            "state": "Karnataka",
            "lead_subtype": "Direct",
            "source": "Email",
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
    
    def run_all_tests(self):
        """Run all lead creation tests"""
        print("🚀 STARTING LEAD CREATION FUNCTIONALITY TESTING")
        print("=" * 60)
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Step 2: Master Data APIs
        print("📊 TESTING MASTER DATA APIs")
        print("-" * 30)
        self.test_master_data_apis()
        
        # Step 3: Lead Creation Tests
        print("🎯 TESTING LEAD CREATION")
        print("-" * 30)
        self.test_lead_creation_without_checklist()
        self.test_lead_creation_with_complete_data()
        
        # Step 4: Billing Type Logic
        print("💰 TESTING BILLING TYPE LOGIC")
        print("-" * 30)
        self.test_billing_type_logic()
        
        # Step 5: Lead Retrieval
        print("📋 TESTING LEAD RETRIEVAL")
        print("-" * 30)
        self.test_lead_retrieval()
        
        # Step 6: Lead ID Generation
        print("🔢 TESTING LEAD ID GENERATION")
        print("-" * 30)
        self.test_lead_id_generation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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
        
        print(f"  • Admin Authentication: {'✅ PASS' if auth_success else '❌ FAIL'}")
        print(f"  • Lead Creation Working: {'✅ PASS' if lead_creation_success else '❌ FAIL'}")
        print(f"  • Master Data APIs: {'✅ PASS' if master_data_success else '❌ FAIL'}")
        
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