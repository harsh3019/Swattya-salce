#!/usr/bin/env python3
"""
FOCUSED Stage Validation Logic Testing for L1→L2 and L5→L6 Transitions
Testing the FIXED stage validation logic using existing opportunities
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

class FocusedStageValidationTester:
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
    
    def get_opportunities_by_stage(self, target_stage):
        """Get opportunities in a specific stage"""
        try:
            response = requests.get(f"{self.base_url}/opportunities", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', [])
                
                # Filter by stage
                stage_opportunities = [opp for opp in opportunities if opp.get('current_stage') == target_stage]
                return stage_opportunities
            return []
        except Exception as e:
            print(f"Error getting opportunities: {e}")
            return []
    
    def test_l1_to_l2_validation_logic(self):
        """Test L1→L2 transition validation logic"""
        print("\n🎯 TESTING L1→L2 VALIDATION LOGIC")
        print("=" * 60)
        
        # Get L1 opportunities
        l1_opportunities = self.get_opportunities_by_stage(1)
        if not l1_opportunities:
            self.log_test("L1→L2 Setup", False, "No L1 opportunities found for testing")
            return
        
        opportunity_id = l1_opportunities[0]['id']
        self.log_test("L1→L2 Setup", True, f"Using opportunity {opportunity_id} in L1 stage")
        
        # Test 1: L1→L2 with VALID L1 data (should succeed)
        self.test_l1_to_l2_with_valid_l1_data(opportunity_id)
        
        # Test 2: L1→L2 with MISSING L1 data (should fail with L1 validation errors)
        self.test_l1_to_l2_with_missing_l1_data(opportunity_id)
        
        # Test 3: L1→L2 with L2 data but missing L1 data (should fail with L1 validation errors)
        self.test_l1_to_l2_with_l2_data_missing_l1(opportunity_id)
    
    def test_l1_to_l2_with_valid_l1_data(self, opportunity_id):
        """Test L1→L2 with valid L1 completion data"""
        try:
            # L1 completion data (what should be validated)
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    "region_id": "faacaad8-1143-4e6a-8b1a-868bd0ec9756",  # Using existing region ID
                    "product_interest": "CRM Software Implementation - L1 to L2 Test",
                    "assigned_representatives": ["58767dce-a766-4287-87ab-ba59d9315327"],  # Using existing user ID
                    "lead_owner_id": "58767dce-a766-4287-87ab-ba59d9315327"
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
                    self.log_test("L1→L2 with Missing L1 Data", True, f"✅ CORRECTLY failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 with Missing L1 Data", False, f"❌ INCORRECTLY failed with L2 validation errors: {l2_errors}")
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
                    self.log_test("L1→L2 with L2 Data Missing L1", True, f"✅ CORRECTLY failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 with L2 Data Missing L1", False, f"❌ INCORRECTLY failed with L2 validation errors: {l2_errors}")
                else:
                    self.log_test("L1→L2 with L2 Data Missing L1", False, f"Failed but with unexpected errors: {validation_errors}")
            else:
                self.log_test("L1→L2 with L2 Data Missing L1", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 with L2 Data Missing L1", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_validation_logic(self):
        """Test L5→L6 transition validation logic"""
        print("\n🏆 TESTING L5→L6 VALIDATION LOGIC")
        print("=" * 60)
        
        # Get L5 opportunities
        l5_opportunities = self.get_opportunities_by_stage(5)
        if not l5_opportunities:
            self.log_test("L5→L6 Setup", False, "No L5 opportunities found for testing")
            return
        
        opportunity_id = l5_opportunities[0]['id']
        self.log_test("L5→L6 Setup", True, f"Using opportunity {opportunity_id} in L5 stage")
        
        # Test 1: L5→L6 with VALID L6 data (should succeed)
        self.test_l5_to_l6_with_valid_l6_data(opportunity_id)
        
        # Test 2: L5→L6 with MISSING L6 data (should fail with L6 validation errors)
        self.test_l5_to_l6_with_missing_l6_data(opportunity_id)
        
        # Test 3: L5→L6 with L5 data but missing L6 data (should fail with L6 validation errors)
        self.test_l5_to_l6_with_l5_data_missing_l6(opportunity_id)
    
    def test_l5_to_l6_with_valid_l6_data(self, opportunity_id):
        """Test L5→L6 with valid L6 completion data"""
        try:
            # L6 completion data (what should be validated for L5→L6)
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000,
                    "client_poc": "John Smith - CTO",
                    "delivery_team": ["58767dce-a766-4287-87ab-ba59d9315327"]  # Using existing user ID
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
                    self.log_test("L5→L6 with Missing L6 Data", True, f"✅ CORRECTLY failed with L6 validation errors: {l6_errors}")
                elif l5_errors:
                    self.log_test("L5→L6 with Missing L6 Data", False, f"❌ INCORRECTLY failed with L5 validation errors: {l5_errors}")
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
                    self.log_test("L5→L6 with L5 Data Missing L6", True, f"✅ CORRECTLY failed with L6 validation errors: {l6_errors}")
                elif l5_errors:
                    self.log_test("L5→L6 with L5 Data Missing L6", False, f"❌ INCORRECTLY failed with L5 validation errors: {l5_errors}")
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
    
    def run_all_tests(self):
        """Run all stage validation tests"""
        print("🚀 STARTING FOCUSED STAGE VALIDATION LOGIC TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return False
        
        # Run test suites
        self.test_l1_to_l2_validation_logic()
        self.test_l5_to_l6_validation_logic()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 FOCUSED STAGE VALIDATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL STAGE VALIDATION TESTS PASSED!")
            print("✅ L1→L2 validation logic is working correctly")
            print("✅ L5→L6 validation logic is working correctly")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ Stage validation logic needs attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = FocusedStageValidationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()