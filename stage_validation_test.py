#!/usr/bin/env python3
"""
Stage Validation Logic Testing for L1→L2 and L5→L6 Transitions
Testing the FIXED stage validation logic as requested in review
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://sawayatta-sd.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class StageValidationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
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
                    f"Token received, User: {user_data.get('username')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_master_data(self):
        """Get required master data for testing"""
        try:
            # Get stages
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            regions_response = requests.get(f"{self.base_url}/regions", headers=self.headers, timeout=10)
            users_response = requests.get(f"{self.base_url}/users", headers=self.headers, timeout=10)
            
            if all(r.status_code == 200 for r in [stages_response, currencies_response, regions_response, users_response]):
                self.stages = stages_response.json()
                self.currencies = currencies_response.json()
                self.regions = regions_response.json()
                self.users = users_response.json()
                
                self.log_test("Master Data Retrieval", True, "All master data retrieved successfully")
                return True
            else:
                self.log_test("Master Data Retrieval", False, "Failed to get master data")
                return False
                
        except Exception as e:
            self.log_test("Master Data Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def create_opportunity_in_stage(self, stage_code, title_suffix=""):
        """Create an opportunity in a specific stage"""
        try:
            # Find the stage
            stage = next((s for s in self.stages if s.get('stage_code') == stage_code), None)
            if not stage:
                self.log_test(f"Create {stage_code} Opportunity", False, f"Stage {stage_code} not found")
                return None
            
            # Find INR currency
            inr_currency = next((c for c in self.currencies if c.get('code') == 'INR'), None)
            if not inr_currency:
                self.log_test(f"Create {stage_code} Opportunity", False, "INR currency not found")
                return None
            
            # Create opportunity data
            opportunity_data = {
                "project_title": f"Stage Validation Test {stage_code} {title_suffix}",
                "company_id": "test-company-stage-validation",
                "stage_id": stage['id'],
                "expected_revenue": 250000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-stage-validation",
                "win_probability": 50
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                opportunity_id = data.get('id')
                self.log_test(f"Create {stage_code} Opportunity", True, f"Created opportunity ID: {opportunity_id}")
                return opportunity_id
            else:
                self.log_test(f"Create {stage_code} Opportunity", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test(f"Create {stage_code} Opportunity", False, f"Exception: {str(e)}")
            return None
    
    def test_l1_to_l2_transition(self):
        """Test L1→L2 transition with L1 completion data"""
        print("\n🎯 TESTING L1→L2 TRANSITION (Normal Stage Progression)")
        print("=" * 60)
        
        # Create opportunity in L1 stage
        opportunity_id = self.create_opportunity_in_stage("L1", "L1→L2 Test")
        if not opportunity_id:
            return
        
        # Test L1→L2 transition with VALID L1 data (should succeed)
        self.test_l1_to_l2_with_valid_l1_data(opportunity_id)
        
        # Test L1→L2 transition with MISSING L1 data (should fail with L1 validation errors)
        self.test_l1_to_l2_with_missing_l1_data(opportunity_id)
        
        # Test L1→L2 transition with L2 data but missing L1 data (should fail with L1 validation errors)
        self.test_l1_to_l2_with_l2_data_missing_l1(opportunity_id)
    
    def test_l1_to_l2_with_valid_l1_data(self, opportunity_id):
        """Test L1→L2 with valid L1 completion data"""
        try:
            # Get region and user IDs
            region = self.regions[0] if self.regions else None
            user = self.users[0] if self.users else None
            
            if not region or not user:
                self.log_test("L1→L2 with Valid L1 Data", False, "Missing region or user data")
                return
            
            # L1 completion data (what should be validated)
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    "region_id": region['id'],
                    "product_interest": "CRM Software Implementation",
                    "assigned_representatives": [user['id']],
                    "lead_owner_id": user['id']
                },
                "notes": "L1→L2 transition with valid L1 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L1→L2 with Valid L1 Data", True, "Transition succeeded with valid L1 completion data")
            else:
                error_detail = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("L1→L2 with Valid L1 Data", False, f"Status: {response.status_code}, Error: {error_detail}")
                
        except Exception as e:
            self.log_test("L1→L2 with Valid L1 Data", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_with_missing_l1_data(self, opportunity_id):
        """Test L1→L2 with missing L1 completion data (should fail)"""
        try:
            # Missing L1 required fields
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    # Missing: region_id, product_interest, assigned_representatives, lead_owner_id
                },
                "notes": "L1→L2 transition with missing L1 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', []) if isinstance(error_detail, dict) else []
                
                # Check if validation errors are for L1 fields (not L2 fields)
                l1_errors = [err for err in validation_errors if any(field in err.lower() for field in ['region', 'product interest', 'assigned representative', 'lead owner'])]
                l2_errors = [err for err in validation_errors if any(field in err.lower() for field in ['scorecard', 'budget', 'authority', 'need', 'timeline'])]
                
                if l1_errors and not l2_errors:
                    self.log_test("L1→L2 with Missing L1 Data", True, f"Correctly failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 with Missing L1 Data", False, f"INCORRECT: Failed with L2 validation errors: {l2_errors}")
                else:
                    self.log_test("L1→L2 with Missing L1 Data", False, f"Failed but with unexpected errors: {validation_errors}")
            else:
                self.log_test("L1→L2 with Missing L1 Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 with Missing L1 Data", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_with_l2_data_missing_l1(self, opportunity_id):
        """Test L1→L2 with L2 data but missing L1 data (should fail with L1 errors)"""
        try:
            # L2 data provided but L1 data missing
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    # L2 fields (should NOT be validated for L1→L2 transition)
                    "scorecard": "BANT",
                    "budget": "500000",
                    "authority": "CTO",
                    "need": "High",
                    "timeline": "Q2 2025",
                    "qualification_status": "Qualified"
                    # Missing L1 fields: region_id, product_interest, assigned_representatives, lead_owner_id
                },
                "notes": "L1→L2 transition with L2 data but missing L1 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', []) if isinstance(error_detail, dict) else []
                
                # Check if validation errors are for L1 fields (not L2 fields)
                l1_errors = [err for err in validation_errors if any(field in err.lower() for field in ['region', 'product interest', 'assigned representative', 'lead owner'])]
                l2_errors = [err for err in validation_errors if any(field in err.lower() for field in ['scorecard', 'budget', 'authority', 'need', 'timeline'])]
                
                if l1_errors and not l2_errors:
                    self.log_test("L1→L2 with L2 Data Missing L1", True, f"Correctly failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 with L2 Data Missing L1", False, f"INCORRECT: Failed with L2 validation errors: {l2_errors}")
                else:
                    self.log_test("L1→L2 with L2 Data Missing L1", False, f"Failed but with unexpected errors: {validation_errors}")
            else:
                self.log_test("L1→L2 with L2 Data Missing L1", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 with L2 Data Missing L1", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_transition(self):
        """Test L5→L6 transition with L6 completion data"""
        print("\n🏆 TESTING L5→L6 TRANSITION (Special Case)")
        print("=" * 60)
        
        # Create opportunity in L5 stage
        opportunity_id = self.create_opportunity_in_stage("L5", "L5→L6 Test")
        if not opportunity_id:
            return
        
        # Test L5→L6 transition with VALID L6 data (should succeed)
        self.test_l5_to_l6_with_valid_l6_data(opportunity_id)
        
        # Test L5→L6 transition with MISSING L6 data (should fail with L6 validation errors)
        self.test_l5_to_l6_with_missing_l6_data(opportunity_id)
        
        # Test L5→L6 transition with L5 data but missing L6 data (should fail with L6 validation errors)
        self.test_l5_to_l6_with_l5_data_missing_l6(opportunity_id)
    
    def test_l5_to_l6_with_valid_l6_data(self, opportunity_id):
        """Test L5→L6 with valid L6 completion data"""
        try:
            user = self.users[0] if self.users else None
            if not user:
                self.log_test("L5→L6 with Valid L6 Data", False, "Missing user data")
                return
            
            # L6 completion data (what should be validated for L5→L6)
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000,
                    "client_poc": "John Smith - CTO",
                    "delivery_team": [user['id']]
                },
                "notes": "L5→L6 transition with valid L6 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L5→L6 with Valid L6 Data", True, "Transition succeeded with valid L6 completion data")
                
                # Verify upcoming project was created
                self.verify_upcoming_project_creation(opportunity_id)
            else:
                error_detail = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("L5→L6 with Valid L6 Data", False, f"Status: {response.status_code}, Error: {error_detail}")
                
        except Exception as e:
            self.log_test("L5→L6 with Valid L6 Data", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_with_missing_l6_data(self, opportunity_id):
        """Test L5→L6 with missing L6 completion data (should fail)"""
        try:
            # Missing L6 required fields
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    # Missing: final_value, client_poc, delivery_team
                },
                "notes": "L5→L6 transition with missing L6 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', []) if isinstance(error_detail, dict) else []
                
                # Check if validation errors are for L6 fields
                l6_errors = [err for err in validation_errors if any(field in err.lower() for field in ['final value', 'client poc', 'delivery team'])]
                l5_errors = [err for err in validation_errors if any(field in err.lower() for field in ['updated price', 'po number', 'po date'])]
                
                if l6_errors and not l5_errors:
                    self.log_test("L5→L6 with Missing L6 Data", True, f"Correctly failed with L6 validation errors: {l6_errors}")
                elif l5_errors:
                    self.log_test("L5→L6 with Missing L6 Data", False, f"INCORRECT: Failed with L5 validation errors: {l5_errors}")
                else:
                    self.log_test("L5→L6 with Missing L6 Data", False, f"Failed but with unexpected errors: {validation_errors}")
            else:
                self.log_test("L5→L6 with Missing L6 Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L5→L6 with Missing L6 Data", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_with_l5_data_missing_l6(self, opportunity_id):
        """Test L5→L6 with L5 data but missing L6 data (should fail with L6 errors)"""
        try:
            # L5 data provided but L6 data missing
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    # L5 fields (should NOT be validated for L5→L6 transition)
                    "updated_price": 600000,
                    "po_number": "PO-2025-001",
                    "po_date": "2025-01-15"
                    # Missing L6 fields: final_value, client_poc, delivery_team
                },
                "notes": "L5→L6 transition with L5 data but missing L6 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', []) if isinstance(error_detail, dict) else []
                
                # Check if validation errors are for L6 fields (not L5 fields)
                l6_errors = [err for err in validation_errors if any(field in err.lower() for field in ['final value', 'client poc', 'delivery team'])]
                l5_errors = [err for err in validation_errors if any(field in err.lower() for field in ['updated price', 'po number', 'po date'])]
                
                if l6_errors and not l5_errors:
                    self.log_test("L5→L6 with L5 Data Missing L6", True, f"Correctly failed with L6 validation errors: {l6_errors}")
                elif l5_errors:
                    self.log_test("L5→L6 with L5 Data Missing L6", False, f"INCORRECT: Failed with L5 validation errors: {l5_errors}")
                else:
                    self.log_test("L5→L6 with L5 Data Missing L6", False, f"Failed but with unexpected errors: {validation_errors}")
            else:
                self.log_test("L5→L6 with L5 Data Missing L6", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L5→L6 with L5 Data Missing L6", False, f"Exception: {str(e)}")
    
    def verify_upcoming_project_creation(self, opportunity_id):
        """Verify that upcoming project was created for won opportunity"""
        try:
            # Get the opportunity to find its opportunity_id
            opp_response = requests.get(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if opp_response.status_code != 200:
                self.log_test("Upcoming Project Creation", False, "Could not retrieve opportunity data")
                return
            
            opportunity = opp_response.json()
            opportunity_code = opportunity.get('opportunity_id')  # The OPP-XXXXXXX format
            
            # Check upcoming projects
            projects_response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                
                # Look for project with matching opp_id
                matching_project = next((p for p in projects if p.get('opp_id') == opportunity_code), None)
                
                if matching_project:
                    self.log_test("Upcoming Project Creation", True, f"Upcoming project created with ID: {matching_project.get('id')}")
                else:
                    self.log_test("Upcoming Project Creation", False, f"No upcoming project found for opportunity {opportunity_code}")
            else:
                self.log_test("Upcoming Project Creation", False, f"Could not retrieve upcoming projects: {projects_response.status_code}")
                
        except Exception as e:
            self.log_test("Upcoming Project Creation", False, f"Exception: {str(e)}")
    
    def test_end_to_end_workflow(self):
        """Test complete opportunity progression through multiple stages"""
        print("\n🔄 TESTING END-TO-END WORKFLOW")
        print("=" * 60)
        
        # Create opportunity in L1
        opportunity_id = self.create_opportunity_in_stage("L1", "End-to-End Test")
        if not opportunity_id:
            return
        
        # Test L1→L2→L3→L4→L5→L6 progression
        self.test_complete_stage_progression(opportunity_id)
    
    def test_complete_stage_progression(self, opportunity_id):
        """Test complete stage progression with proper validation"""
        try:
            region = self.regions[0] if self.regions else None
            user = self.users[0] if self.users else None
            
            if not region or not user:
                self.log_test("Complete Stage Progression", False, "Missing master data")
                return
            
            # L1→L2 with L1 data
            l1_to_l2_data = {
                "target_stage": 2,
                "stage_data": {
                    "region_id": region['id'],
                    "product_interest": "End-to-End CRM Implementation",
                    "assigned_representatives": [user['id']],
                    "lead_owner_id": user['id']
                },
                "notes": "L1→L2 progression"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=l1_to_l2_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L1→L2 Progression", True, "Successfully moved from L1 to L2")
                
                # L2→L3 with L2 data
                l2_to_l3_data = {
                    "target_stage": 3,
                    "stage_data": {
                        "scorecard": "BANT",
                        "budget": "1000000",
                        "authority": "CTO",
                        "need": "High",
                        "timeline": "Q2 2025",
                        "qualification_status": "Qualified"
                    },
                    "notes": "L2→L3 progression"
                }
                
                l2_response = requests.post(
                    f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                    headers=self.headers,
                    json=l2_to_l3_data,
                    timeout=10
                )
                
                if l2_response.status_code == 200:
                    self.log_test("L2→L3 Progression", True, "Successfully moved from L2 to L3")
                else:
                    self.log_test("L2→L3 Progression", False, f"Failed: {l2_response.status_code}")
            else:
                self.log_test("L1→L2 Progression", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Complete Stage Progression", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all stage validation tests"""
        print("🚀 STARTING STAGE VALIDATION LOGIC TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return False
        
        # Get master data
        if not self.get_master_data():
            print("\n❌ MASTER DATA RETRIEVAL FAILED - Cannot proceed with tests")
            return False
        
        # Run test suites
        self.test_l1_to_l2_transition()
        self.test_l5_to_l6_transition()
        self.test_end_to_end_workflow()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 STAGE VALIDATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL STAGE VALIDATION TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = StageValidationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()