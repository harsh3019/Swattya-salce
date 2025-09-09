#!/usr/bin/env python3
"""
Lead-to-Opportunity Conversion Workflow Testing
Testing the complete workflow: Lead Creation → Lead Approval → Lead-to-Opportunity Conversion → Opportunity Management
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://lead-opp-crm.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class LeadOpportunityConversionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.created_lead_id = None
        self.created_opportunity_id = None
        self.company_id = None
        self.service_id = None
        self.sub_tender_id = None
        
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
        """Test admin authentication"""
        print("\n🔐 TESTING AUTHENTICATION")
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
                    "Admin Authentication", 
                    True, 
                    f"Token received, User: {user_data.get('username')}, Role ID: {user_data.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_master_data(self):
        """Get required master data for lead creation"""
        print("\n📊 GETTING MASTER DATA")
        print("=" * 50)
        
        try:
            # Get companies
            companies_response = requests.get(f"{self.base_url}/companies", headers=self.headers, timeout=10)
            if companies_response.status_code == 200:
                companies = companies_response.json()
                if companies and len(companies) > 0:
                    self.company_id = companies[0].get('id')
                    self.log_test("Get Company ID", True, f"Using company ID: {self.company_id}")
                else:
                    self.log_test("Get Company ID", False, "No companies found")
                    return False
            else:
                self.log_test("Get Company ID", False, f"Status: {companies_response.status_code}")
                return False
            
            # Get product services
            services_response = requests.get(f"{self.base_url}/product-services", headers=self.headers, timeout=10)
            if services_response.status_code == 200:
                services = services_response.json()
                if services and len(services) > 0:
                    self.service_id = services[0].get('id')
                    self.log_test("Get Product Service ID", True, f"Using service ID: {self.service_id}")
                else:
                    self.log_test("Get Product Service ID", False, "No product services found")
                    return False
            else:
                self.log_test("Get Product Service ID", False, f"Status: {services_response.status_code}")
                return False
            
            # Get sub-tender types
            sub_tender_response = requests.get(f"{self.base_url}/sub-tender-types", headers=self.headers, timeout=10)
            if sub_tender_response.status_code == 200:
                sub_tenders = sub_tender_response.json()
                if sub_tenders and len(sub_tenders) > 0:
                    self.sub_tender_id = sub_tenders[0].get('id')
                    self.log_test("Get Sub-Tender Type ID", True, f"Using sub-tender ID: {self.sub_tender_id}")
                else:
                    self.log_test("Get Sub-Tender Type ID", False, "No sub-tender types found")
                    return False
            else:
                self.log_test("Get Sub-Tender Type ID", False, f"Status: {sub_tender_response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Get Master Data", False, f"Exception: {str(e)}")
            return False
    
    def create_lead(self):
        """Test lead creation with complete data"""
        print("\n📝 TESTING LEAD CREATION")
        print("=" * 50)
        
        if not self.company_id or not self.service_id or not self.sub_tender_id:
            self.log_test("Create Lead", False, "Missing required master data")
            return False
        
        try:
            lead_data = {
                "tender_type": "Tender",
                "billing_type": "prepaid",
                "sub_tender_type_id": self.sub_tender_id,
                "project_title": "Test Lead for Conversion",
                "company_id": self.company_id,
                "state": "Maharashtra",
                "lead_subtype": "Direct",
                "source": "Website",
                "product_service_id": self.service_id,
                "expected_orc": 500000.0,
                "revenue": 750000.0,
                "lead_owner": "admin"
            }
            
            response = requests.post(
                f"{self.base_url}/leads",
                headers=self.headers,
                json=lead_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                lead_id = data.get('lead_id')
                self.created_lead_id = data.get('id')  # Store the UUID for API calls
                
                # Check if lead ID follows LEAD-XXXXXXX format
                if lead_id and lead_id.startswith('LEAD-') and len(lead_id) >= 9:
                    self.log_test(
                        "Create Lead", 
                        True, 
                        f"Lead created with ID: {lead_id}, UUID: {self.created_lead_id}"
                    )
                    return True
                else:
                    self.log_test(
                        "Create Lead", 
                        False, 
                        f"Invalid lead ID format: {lead_id}"
                    )
                    return False
            else:
                self.log_test(
                    "Create Lead", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Create Lead", False, f"Exception: {str(e)}")
            return False
    
    def approve_lead(self):
        """Test lead approval"""
        print("\n✅ TESTING LEAD APPROVAL")
        print("=" * 50)
        
        if not self.created_lead_id:
            self.log_test("Approve Lead", False, "No lead ID available")
            return False
        
        try:
            approval_data = {
                "status": "approved"
            }
            
            response = requests.post(
                f"{self.base_url}/leads/{self.created_lead_id}/status",
                headers=self.headers,
                json=approval_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log_test(
                    "Approve Lead", 
                    True, 
                    "Lead status updated to Approved"
                )
                return True
            else:
                self.log_test(
                    "Approve Lead", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Approve Lead", False, f"Exception: {str(e)}")
            return False
    
    def convert_lead_to_opportunity(self):
        """Test lead to opportunity conversion"""
        print("\n🔄 TESTING LEAD-TO-OPPORTUNITY CONVERSION")
        print("=" * 50)
        
        if not self.created_lead_id:
            self.log_test("Convert Lead to Opportunity", False, "No lead ID available")
            return False
        
        try:
            conversion_data = {
                "opportunity_date": "2024-01-15T10:00:00Z"
            }
            
            response = requests.post(
                f"{self.base_url}/leads/{self.created_lead_id}/convert",
                headers=self.headers,
                json=conversion_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                opportunity_id = data.get('opportunity_id')
                
                # Check if opportunity ID follows OPP-XXXXXX format (not POT-)
                if opportunity_id and opportunity_id.startswith('OPP-') and len(opportunity_id) >= 7:
                    self.created_opportunity_id = data.get('opportunity_uuid')
                    self.log_test(
                        "Convert Lead to Opportunity", 
                        True, 
                        f"Lead converted to opportunity with ID: {opportunity_id}, UUID: {self.created_opportunity_id}"
                    )
                    return True
                else:
                    self.log_test(
                        "Convert Lead to Opportunity", 
                        False, 
                        f"Invalid opportunity ID format: {opportunity_id} (should be OPP-XXXXXX, not POT-)"
                    )
                    return False
            else:
                self.log_test(
                    "Convert Lead to Opportunity", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Convert Lead to Opportunity", False, f"Exception: {str(e)}")
            return False
    
    def verify_opportunity_creation(self):
        """Verify opportunity was created correctly"""
        print("\n🎯 VERIFYING OPPORTUNITY CREATION")
        print("=" * 50)
        
        try:
            # Test GET /api/opportunities to verify new opportunity appears in listing
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', []) if isinstance(data, dict) else data
                
                # Look for our created opportunity
                found_opportunity = None
                for opp in opportunities:
                    if opp.get('lead_id') == self.created_lead_id:
                        found_opportunity = opp
                        break
                
                if found_opportunity:
                    self.log_test(
                        "Verify Opportunity in Listing", 
                        True, 
                        f"Opportunity found in listing with ID: {found_opportunity.get('opportunity_id')}"
                    )
                else:
                    self.log_test(
                        "Verify Opportunity in Listing", 
                        False, 
                        "Created opportunity not found in opportunities listing"
                    )
            else:
                self.log_test(
                    "Verify Opportunity in Listing", 
                    False, 
                    f"Status: {response.status_code}"
                )
            
            # Test GET /api/opportunities/{opportunity_id} to verify opportunity details
            if self.created_opportunity_id:
                detail_response = requests.get(
                    f"{self.base_url}/opportunities/{self.created_opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if detail_response.status_code == 200:
                    opp_data = detail_response.json()
                    
                    # Verify required fields
                    checks = [
                        ("opportunity_id format", opp_data.get('opportunity_id', '').startswith('OPP-')),
                        ("current_stage = 1 (L1)", opp_data.get('current_stage') == 1),
                        ("status = Active", opp_data.get('status') == 'Active'),
                        ("expected_revenue transferred", opp_data.get('expected_revenue') > 0),
                        ("currency_id set to INR", opp_data.get('currency_id') is not None),
                        ("win_probability = 25.0", opp_data.get('win_probability') == 25.0),
                        ("weighted_revenue calculated", opp_data.get('weighted_revenue') is not None),
                        ("lead_id reference", opp_data.get('lead_id') == self.created_lead_id)
                    ]
                    
                    passed_checks = sum(1 for _, check in checks if check)
                    total_checks = len(checks)
                    
                    if passed_checks == total_checks:
                        self.log_test(
                            "Verify Opportunity Details", 
                            True, 
                            f"All {total_checks} required fields verified correctly"
                        )
                    else:
                        failed_checks = [name for name, check in checks if not check]
                        self.log_test(
                            "Verify Opportunity Details", 
                            False, 
                            f"Failed checks: {', '.join(failed_checks)}"
                        )
                else:
                    self.log_test(
                        "Verify Opportunity Details", 
                        False, 
                        f"Status: {detail_response.status_code}"
                    )
                    
        except Exception as e:
            self.log_test("Verify Opportunity Creation", False, f"Exception: {str(e)}")
    
    def verify_lead_update(self):
        """Verify lead was updated after conversion"""
        print("\n📋 VERIFYING LEAD UPDATE AFTER CONVERSION")
        print("=" * 50)
        
        if not self.created_lead_id:
            self.log_test("Verify Lead Update", False, "No lead ID available")
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/leads/{self.created_lead_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                lead_data = response.json()
                
                # Verify lead shows conversion status
                checks = [
                    ("status = Converted", lead_data.get('status') == 'Converted'),
                    ("converted_to_opportunity = true", lead_data.get('converted_to_opportunity') == True),
                    ("opportunity_date set", lead_data.get('opportunity_date') is not None),
                    ("opportunity_id reference", lead_data.get('opportunity_id') is not None)
                ]
                
                passed_checks = sum(1 for _, check in checks if check)
                total_checks = len(checks)
                
                if passed_checks == total_checks:
                    self.log_test(
                        "Verify Lead Update", 
                        True, 
                        f"Lead properly updated with conversion status and opportunity reference"
                    )
                else:
                    failed_checks = [name for name, check in checks if not check]
                    self.log_test(
                        "Verify Lead Update", 
                        False, 
                        f"Failed checks: {', '.join(failed_checks)}"
                    )
            else:
                self.log_test(
                    "Verify Lead Update", 
                    False, 
                    f"Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Verify Lead Update", False, f"Exception: {str(e)}")
    
    def test_duplicate_conversion_prevention(self):
        """Test that duplicate conversion is prevented"""
        print("\n🚫 TESTING DUPLICATE CONVERSION PREVENTION")
        print("=" * 50)
        
        if not self.created_lead_id:
            self.log_test("Test Duplicate Conversion Prevention", False, "No lead ID available")
            return
        
        try:
            conversion_data = {
                "opportunity_date": "2024-01-16T10:00:00Z"
            }
            
            response = requests.post(
                f"{self.base_url}/leads/{self.created_lead_id}/convert",
                headers=self.headers,
                json=conversion_data,
                timeout=10
            )
            
            # Should return error for duplicate conversion
            if response.status_code == 400:
                error_message = response.json().get('detail', '')
                if 'already converted' in error_message.lower():
                    self.log_test(
                        "Test Duplicate Conversion Prevention", 
                        True, 
                        f"Correctly prevented duplicate conversion: {error_message}"
                    )
                else:
                    self.log_test(
                        "Test Duplicate Conversion Prevention", 
                        False, 
                        f"Wrong error message: {error_message}"
                    )
            else:
                self.log_test(
                    "Test Duplicate Conversion Prevention", 
                    False, 
                    f"Expected 400 error, got status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Test Duplicate Conversion Prevention", False, f"Exception: {str(e)}")
    
    def run_complete_workflow_test(self):
        """Run the complete Lead-to-Opportunity conversion workflow test"""
        print("🚀 STARTING COMPLETE LEAD-TO-OPPORTUNITY CONVERSION WORKFLOW TESTING")
        print("=" * 70)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with workflow tests")
            return False
        
        # Step 2: Get master data
        if not self.get_master_data():
            print("\n❌ MASTER DATA RETRIEVAL FAILED - Cannot proceed with workflow tests")
            return False
        
        # Step 3: Create a new lead
        if not self.create_lead():
            print("\n❌ LEAD CREATION FAILED - Cannot proceed with workflow tests")
            return False
        
        # Step 4: Approve the lead
        if not self.approve_lead():
            print("\n❌ LEAD APPROVAL FAILED - Cannot proceed with conversion")
            return False
        
        # Step 5: Convert lead to opportunity
        if not self.convert_lead_to_opportunity():
            print("\n❌ LEAD CONVERSION FAILED - Cannot proceed with verification")
            return False
        
        # Step 6: Verify opportunity creation
        self.verify_opportunity_creation()
        
        # Step 7: Verify lead update
        self.verify_lead_update()
        
        # Step 8: Test duplicate conversion prevention
        self.test_duplicate_conversion_prevention()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 LEAD-TO-OPPORTUNITY CONVERSION WORKFLOW TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL WORKFLOW TESTS PASSED!")
            print("✅ Complete Lead-to-Opportunity Conversion workflow is FUNCTIONAL and PRODUCTION-READY")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} WORKFLOW TESTS FAILED")
            print("❌ Lead-to-Opportunity Conversion workflow has ISSUES that need attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 50)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = LeadOpportunityConversionTester()
    success = tester.run_complete_workflow_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()