#!/usr/bin/env python3
"""
FINAL Stage Validation Logic Testing - L1→L2 and L5→L6 Transitions
Comprehensive verification of the FIXED stage validation logic
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

class FinalStageValidationTester:
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
        print("\n🔐 AUTHENTICATION")
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
    
    def get_fresh_l1_opportunity(self):
        """Get a fresh L1 opportunity for testing"""
        try:
            response = requests.get(f"{self.base_url}/opportunities", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', [])
                
                # Filter by L1 stage
                l1_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 1]
                return l1_opportunities[0]['id'] if l1_opportunities else None
            return None
        except Exception as e:
            print(f"Error getting L1 opportunity: {e}")
            return None
    
    def test_l1_to_l2_validation_logic(self):
        """Test L1→L2 transition validation logic"""
        print("\n🎯 L1→L2 VALIDATION LOGIC TESTING")
        print("=" * 60)
        
        # Test 1: L1→L2 with valid L1 data (should succeed)
        opportunity_id = self.get_fresh_l1_opportunity()
        if not opportunity_id:
            self.log_test("L1→L2 Valid L1 Data", False, "No L1 opportunities available")
        else:
            self.test_l1_to_l2_with_valid_l1_data(opportunity_id)
        
        # Test 2: L1→L2 with missing L1 data (should fail with L1 errors)
        opportunity_id = self.get_fresh_l1_opportunity()
        if not opportunity_id:
            self.log_test("L1→L2 Missing L1 Data", False, "No L1 opportunities available")
        else:
            self.test_l1_to_l2_with_missing_l1_data(opportunity_id)
        
        # Test 3: L1→L2 with L2 data but missing L1 data (should fail with L1 errors)
        opportunity_id = self.get_fresh_l1_opportunity()
        if not opportunity_id:
            self.log_test("L1→L2 L2 Data Missing L1", False, "No L1 opportunities available")
        else:
            self.test_l1_to_l2_with_l2_data_missing_l1(opportunity_id)
    
    def test_l1_to_l2_with_valid_l1_data(self, opportunity_id):
        """Test L1→L2 with valid L1 completion data"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    "region_id": "faacaad8-1143-4e6a-8b1a-868bd0ec9756",
                    "product_interest": "CRM Software Implementation - Final Test",
                    "assigned_representatives": ["58767dce-a766-4287-87ab-ba59d9315327"],
                    "lead_owner_id": "58767dce-a766-4287-87ab-ba59d9315327"
                },
                "notes": "L1→L2 transition with valid L1 data - Final Test"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L1→L2 Valid L1 Data", True, "✅ Transition succeeded with valid L1 completion data")
            else:
                error_detail = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("L1→L2 Valid L1 Data", False, f"Status: {response.status_code}, Error: {error_detail}")
                
        except Exception as e:
            self.log_test("L1→L2 Valid L1 Data", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_with_missing_l1_data(self, opportunity_id):
        """Test L1→L2 with missing L1 completion data (should fail)"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {},
                "notes": "L1→L2 transition with missing L1 data - Final Test"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', [])
                
                # Check if validation errors are for L1 fields
                l1_errors = [err for err in validation_errors if any(field in err.lower() for field in ['region', 'product interest', 'assigned representative', 'lead owner'])]
                l2_errors = [err for err in validation_errors if any(field in err.lower() for field in ['scorecard', 'budget', 'authority', 'need', 'timeline'])]
                
                if len(l1_errors) == 4 and not l2_errors:
                    self.log_test("L1→L2 Missing L1 Data", True, f"✅ CORRECTLY failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 Missing L1 Data", False, f"❌ INCORRECTLY failed with L2 validation errors: {l2_errors}")
                else:
                    self.log_test("L1→L2 Missing L1 Data", False, f"Unexpected validation errors: {validation_errors}")
            else:
                self.log_test("L1→L2 Missing L1 Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 Missing L1 Data", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_with_l2_data_missing_l1(self, opportunity_id):
        """Test L1→L2 with L2 data but missing L1 data (should fail with L1 errors)"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    # L2 fields (should NOT be validated for L1→L2 transition)
                    "scorecard": "BANT",
                    "budget": "500000",
                    "authority": "CTO",
                    "need": "High Priority",
                    "timeline": "Q2 2025",
                    "qualification_status": "Qualified"
                    # Missing L1 fields: region_id, product_interest, assigned_representatives, lead_owner_id
                },
                "notes": "L1→L2 transition with L2 data but missing L1 data - Final Test"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', [])
                
                # Check if validation errors are for L1 fields (not L2 fields)
                l1_errors = [err for err in validation_errors if any(field in err.lower() for field in ['region', 'product interest', 'assigned representative', 'lead owner'])]
                l2_errors = [err for err in validation_errors if any(field in err.lower() for field in ['scorecard', 'budget', 'authority', 'need', 'timeline'])]
                
                if len(l1_errors) == 4 and not l2_errors:
                    self.log_test("L1→L2 L2 Data Missing L1", True, f"✅ CORRECTLY failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 L2 Data Missing L1", False, f"❌ INCORRECTLY failed with L2 validation errors: {l2_errors}")
                else:
                    self.log_test("L1→L2 L2 Data Missing L1", False, f"Unexpected validation errors: {validation_errors}")
            else:
                self.log_test("L1→L2 L2 Data Missing L1", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 L2 Data Missing L1", False, f"Exception: {str(e)}")
    
    def create_l5_opportunity_for_testing(self):
        """Create an L5 opportunity by moving an L4 opportunity"""
        try:
            # Get L4 opportunities
            response = requests.get(f"{self.base_url}/opportunities", headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None
            
            opportunities = response.json().get('opportunities', [])
            l4_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 4]
            
            if not l4_opportunities:
                return None
            
            opportunity_id = l4_opportunities[0]['id']
            
            # Create a quotation for this opportunity first
            quotation_data = {
                "quotation_name": "Test Quotation for L5 Testing",
                "rate_card_id": "test-rate-card",
                "validity_date": "2025-06-30T00:00:00Z",
                "items": []
            }
            
            quotation_response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/quotations",
                headers=self.headers,
                json=quotation_data,
                timeout=10
            )
            
            if quotation_response.status_code in [200, 201]:
                quotation = quotation_response.json()
                quotation_id = quotation.get('id')
                
                # Move L4 to L5 with valid L4 data
                stage_data = {
                    'target_stage': 5,
                    'stage_data': {
                        'selected_quotation_id': quotation_id
                    },
                    'notes': 'Creating L5 opportunity for final testing'
                }
                
                stage_response = requests.post(
                    f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                    headers=self.headers,
                    json=stage_data,
                    timeout=10
                )
                
                if stage_response.status_code == 200:
                    self.log_test("L5 Opportunity Creation", True, f"Successfully created L5 opportunity {opportunity_id}")
                    return opportunity_id
                else:
                    self.log_test("L5 Opportunity Creation", False, f"Failed to move to L5: {stage_response.text}")
                    return None
            else:
                self.log_test("L5 Opportunity Creation", False, f"Failed to create quotation: {quotation_response.text}")
                return None
                
        except Exception as e:
            self.log_test("L5 Opportunity Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_l5_to_l6_validation_logic(self):
        """Test L5→L6 transition validation logic"""
        print("\n🏆 L5→L6 VALIDATION LOGIC TESTING")
        print("=" * 60)
        
        # Try to get existing L5 opportunities first
        response = requests.get(f"{self.base_url}/opportunities", headers=self.headers, timeout=10)
        if response.status_code == 200:
            opportunities = response.json().get('opportunities', [])
            l5_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 5]
        else:
            l5_opportunities = []
        
        if not l5_opportunities:
            # Try to create one
            opportunity_id = self.create_l5_opportunity_for_testing()
            if not opportunity_id:
                self.log_test("L5→L6 Setup", False, "Could not find or create L5 opportunity for testing")
                return
        else:
            opportunity_id = l5_opportunities[0]['id']
            self.log_test("L5→L6 Setup", True, f"Using existing L5 opportunity {opportunity_id}")
        
        # Test 1: L5→L6 with valid L6 data (should succeed)
        self.test_l5_to_l6_with_valid_l6_data(opportunity_id)
        
        # Test 2: L5→L6 with missing L6 data (should fail with L6 errors)
        # Need a fresh L5 opportunity for this test
        if len(l5_opportunities) > 1:
            opportunity_id2 = l5_opportunities[1]['id']
            self.test_l5_to_l6_with_missing_l6_data(opportunity_id2)
        else:
            self.log_test("L5→L6 Missing L6 Data", False, "Need additional L5 opportunity for this test")
    
    def test_l5_to_l6_with_valid_l6_data(self, opportunity_id):
        """Test L5→L6 with valid L6 completion data"""
        try:
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000,
                    "client_poc": "John Smith - CTO - Final Test",
                    "delivery_team": ["58767dce-a766-4287-87ab-ba59d9315327"]
                },
                "notes": "L5→L6 transition with valid L6 data - Final Test"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L5→L6 Valid L6 Data", True, "✅ Transition succeeded with valid L6 completion data")
                
                # Verify upcoming project was created
                self.verify_upcoming_project_creation(opportunity_id)
            else:
                error_detail = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("L5→L6 Valid L6 Data", False, f"Status: {response.status_code}, Error: {error_detail}")
                
        except Exception as e:
            self.log_test("L5→L6 Valid L6 Data", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_with_missing_l6_data(self, opportunity_id):
        """Test L5→L6 with missing L6 completion data (should fail)"""
        try:
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    # L5 fields provided but L6 fields missing
                    "updated_price": 600000,
                    "po_number": "PO-2025-FINAL-TEST",
                    "po_date": "2025-01-15"
                    # Missing L6 fields: final_value, client_poc, delivery_team
                },
                "notes": "L5→L6 transition with missing L6 data - Final Test"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', {})
                validation_errors = error_detail.get('validation_errors', [])
                
                # Check if validation errors are for L6 fields
                l6_errors = [err for err in validation_errors if any(field in err.lower() for field in ['final value', 'client poc', 'delivery team'])]
                l5_errors = [err for err in validation_errors if any(field in err.lower() for field in ['updated price', 'po number', 'po date'])]
                
                if len(l6_errors) == 3 and not l5_errors:
                    self.log_test("L5→L6 Missing L6 Data", True, f"✅ CORRECTLY failed with L6 validation errors: {l6_errors}")
                elif l5_errors:
                    self.log_test("L5→L6 Missing L6 Data", False, f"❌ INCORRECTLY failed with L5 validation errors: {l5_errors}")
                else:
                    self.log_test("L5→L6 Missing L6 Data", False, f"Unexpected validation errors: {validation_errors}")
            else:
                self.log_test("L5→L6 Missing L6 Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L5→L6 Missing L6 Data", False, f"Exception: {str(e)}")
    
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
                    self.log_test("Upcoming Project Creation", True, f"✅ Upcoming project created with ID: {matching_project.get('id')}")
                else:
                    self.log_test("Upcoming Project Creation", False, f"No upcoming project found for opportunity {opportunity_code}")
            else:
                self.log_test("Upcoming Project Creation", False, f"Could not retrieve upcoming projects: {projects_response.status_code}")
                
        except Exception as e:
            self.log_test("Upcoming Project Creation", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all final stage validation tests"""
        print("🚀 FINAL STAGE VALIDATION LOGIC TESTING")
        print("Testing the FIXED stage validation logic for L1→L2 and L5→L6 transitions")
        print("=" * 80)
        
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
        print("\n" + "=" * 80)
        print("📊 FINAL STAGE VALIDATION TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL STAGE VALIDATION TESTS PASSED!")
            print("✅ L1→L2 validation logic is working correctly")
            print("✅ L5→L6 validation logic is working correctly")
            print("✅ Stage validation fix is CONFIRMED WORKING")
            print("\n🔧 VALIDATION LOGIC CONFIRMED:")
            print("   • L1→L2 transition validates L1 completion data (not L2 data)")
            print("   • L5→L6 transition validates L6 completion data (special case)")
            print("   • Normal stage progression validates current stage completion")
            print("   • L6 Won transition validates target stage (L6) requirements")
            print("   • Upcoming project integration works for L6 transitions")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ Stage validation logic needs attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = FinalStageValidationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()