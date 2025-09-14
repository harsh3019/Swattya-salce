#!/usr/bin/env python3
"""
COMPREHENSIVE Stage Validation Logic Testing
Testing the FIXED stage validation logic with detailed analysis
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://service-delivery.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class ComprehensiveStageValidationTester:
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
    
    def test_l1_to_l2_validation_comprehensive(self):
        """Comprehensive test of L1→L2 validation logic"""
        print("\n🎯 COMPREHENSIVE L1→L2 VALIDATION TESTING")
        print("=" * 60)
        
        # Get L1 opportunities
        l1_opportunities = self.get_opportunities_by_stage(1)
        if not l1_opportunities:
            self.log_test("L1→L2 Setup", False, "No L1 opportunities found for testing")
            return
        
        opportunity_id = l1_opportunities[0]['id']
        self.log_test("L1→L2 Setup", True, f"Using opportunity {opportunity_id} in L1 stage")
        
        # Test 1: Completely empty stage_data (should fail with L1 errors)
        self.test_l1_to_l2_empty_data(opportunity_id)
        
        # Test 2: Valid L1 data (should succeed)
        self.test_l1_to_l2_valid_l1_data(opportunity_id)
        
        # Test 3: L2 data without L1 data (should fail with L1 errors)
        self.test_l1_to_l2_l2_data_only(opportunity_id)
        
        # Test 4: Partial L1 data (should fail with missing L1 field errors)
        self.test_l1_to_l2_partial_l1_data(opportunity_id)
    
    def test_l1_to_l2_empty_data(self, opportunity_id):
        """Test L1→L2 with completely empty stage_data"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {},
                "notes": "Testing with empty data"
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
                
                # Should have L1 validation errors
                l1_errors = [err for err in validation_errors if any(field in err.lower() for field in ['region', 'product interest', 'assigned representative', 'lead owner'])]
                
                if len(l1_errors) == 4:  # All 4 L1 fields should be missing
                    self.log_test("L1→L2 Empty Data", True, f"Correctly failed with all 4 L1 validation errors: {l1_errors}")
                else:
                    self.log_test("L1→L2 Empty Data", False, f"Expected 4 L1 errors, got: {validation_errors}")
            else:
                self.log_test("L1→L2 Empty Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 Empty Data", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_valid_l1_data(self, opportunity_id):
        """Test L1→L2 with valid L1 data"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    "region_id": "faacaad8-1143-4e6a-8b1a-868bd0ec9756",
                    "product_interest": "CRM Software Implementation",
                    "assigned_representatives": ["58767dce-a766-4287-87ab-ba59d9315327"],
                    "lead_owner_id": "58767dce-a766-4287-87ab-ba59d9315327"
                },
                "notes": "Testing with valid L1 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L1→L2 Valid L1 Data", True, "Successfully transitioned with valid L1 data")
                
                # Verify the opportunity is now in L2
                opp_response = requests.get(f"{self.base_url}/opportunities/{opportunity_id}", headers=self.headers)
                if opp_response.status_code == 200:
                    opp_data = opp_response.json()
                    current_stage = opp_data.get('current_stage')
                    if current_stage == 2:
                        self.log_test("L1→L2 Stage Verification", True, f"Opportunity is now in stage {current_stage}")
                    else:
                        self.log_test("L1→L2 Stage Verification", False, f"Expected stage 2, got {current_stage}")
            else:
                error_detail = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("L1→L2 Valid L1 Data", False, f"Status: {response.status_code}, Error: {error_detail}")
                
        except Exception as e:
            self.log_test("L1→L2 Valid L1 Data", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_l2_data_only(self, opportunity_id):
        """Test L1→L2 with only L2 data (should fail with L1 errors)"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    # Only L2 fields, no L1 fields
                    "scorecard": "BANT",
                    "budget": "500000",
                    "authority": "CTO",
                    "need": "High Priority",
                    "timeline": "Q2 2025",
                    "qualification_status": "Qualified"
                },
                "notes": "Testing with only L2 data"
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
                
                # Should have L1 validation errors, not L2
                l1_errors = [err for err in validation_errors if any(field in err.lower() for field in ['region', 'product interest', 'assigned representative', 'lead owner'])]
                l2_errors = [err for err in validation_errors if any(field in err.lower() for field in ['scorecard', 'budget', 'authority', 'need', 'timeline'])]
                
                if l1_errors and not l2_errors:
                    self.log_test("L1→L2 L2 Data Only", True, f"✅ CORRECTLY failed with L1 validation errors: {l1_errors}")
                elif l2_errors:
                    self.log_test("L1→L2 L2 Data Only", False, f"❌ INCORRECTLY failed with L2 validation errors: {l2_errors}")
                else:
                    self.log_test("L1→L2 L2 Data Only", False, f"Unexpected validation errors: {validation_errors}")
            else:
                self.log_test("L1→L2 L2 Data Only", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 L2 Data Only", False, f"Exception: {str(e)}")
    
    def test_l1_to_l2_partial_l1_data(self, opportunity_id):
        """Test L1→L2 with partial L1 data"""
        try:
            stage_transition_data = {
                "target_stage": 2,
                "stage_data": {
                    # Only 2 out of 4 required L1 fields
                    "region_id": "faacaad8-1143-4e6a-8b1a-868bd0ec9756",
                    "product_interest": "CRM Software Implementation"
                    # Missing: assigned_representatives, lead_owner_id
                },
                "notes": "Testing with partial L1 data"
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
                
                # Should have errors for the 2 missing L1 fields
                missing_rep_error = any('assigned representative' in err.lower() for err in validation_errors)
                missing_owner_error = any('lead owner' in err.lower() for err in validation_errors)
                
                if missing_rep_error and missing_owner_error:
                    self.log_test("L1→L2 Partial L1 Data", True, f"Correctly failed with missing L1 field errors: {validation_errors}")
                else:
                    self.log_test("L1→L2 Partial L1 Data", False, f"Expected missing rep and owner errors, got: {validation_errors}")
            else:
                self.log_test("L1→L2 Partial L1 Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L1→L2 Partial L1 Data", False, f"Exception: {str(e)}")
    
    def create_l5_opportunity_for_testing(self):
        """Create an L5 opportunity by moving an L4 opportunity"""
        try:
            # Get L4 opportunities
            l4_opportunities = self.get_opportunities_by_stage(4)
            if not l4_opportunities:
                return None
            
            opportunity_id = l4_opportunities[0]['id']
            
            # First, get quotations for this opportunity
            quotations_response = requests.get(
                f"{self.base_url}/opportunities/{opportunity_id}/quotations",
                headers=self.headers,
                timeout=10
            )
            
            if quotations_response.status_code == 200:
                quotations = quotations_response.json()
                if quotations:
                    quotation_id = quotations[0]['id']
                    
                    # Move L4 to L5 with valid L4 data
                    stage_data = {
                        'target_stage': 5,
                        'stage_data': {
                            'selected_quotation_id': quotation_id
                        },
                        'notes': 'Creating L5 opportunity for testing'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                        headers=self.headers,
                        json=stage_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        self.log_test("L5 Opportunity Creation", True, f"Successfully created L5 opportunity {opportunity_id}")
                        return opportunity_id
                    else:
                        self.log_test("L5 Opportunity Creation", False, f"Failed to move to L5: {response.text}")
                        return None
                else:
                    self.log_test("L5 Opportunity Creation", False, "No quotations found for L4 opportunity")
                    return None
            else:
                self.log_test("L5 Opportunity Creation", False, "Could not get quotations for L4 opportunity")
                return None
                
        except Exception as e:
            self.log_test("L5 Opportunity Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_l5_to_l6_validation_comprehensive(self):
        """Comprehensive test of L5→L6 validation logic"""
        print("\n🏆 COMPREHENSIVE L5→L6 VALIDATION TESTING")
        print("=" * 60)
        
        # Try to get existing L5 opportunities first
        l5_opportunities = self.get_opportunities_by_stage(5)
        
        if not l5_opportunities:
            # Try to create one
            opportunity_id = self.create_l5_opportunity_for_testing()
            if not opportunity_id:
                self.log_test("L5→L6 Setup", False, "Could not find or create L5 opportunity for testing")
                return
        else:
            opportunity_id = l5_opportunities[0]['id']
            self.log_test("L5→L6 Setup", True, f"Using existing L5 opportunity {opportunity_id}")
        
        # Test 1: Empty L6 data (should fail with L6 errors)
        self.test_l5_to_l6_empty_data(opportunity_id)
        
        # Test 2: Valid L6 data (should succeed)
        self.test_l5_to_l6_valid_l6_data(opportunity_id)
        
        # Test 3: L5 data without L6 data (should fail with L6 errors)
        self.test_l5_to_l6_l5_data_only(opportunity_id)
    
    def test_l5_to_l6_empty_data(self, opportunity_id):
        """Test L5→L6 with empty data"""
        try:
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {},
                "notes": "Testing L5→L6 with empty data"
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
                
                # Should have L6 validation errors
                l6_errors = [err for err in validation_errors if any(field in err.lower() for field in ['final value', 'client poc', 'delivery team'])]
                
                if len(l6_errors) == 3:  # All 3 L6 fields should be missing
                    self.log_test("L5→L6 Empty Data", True, f"✅ CORRECTLY failed with all 3 L6 validation errors: {l6_errors}")
                else:
                    self.log_test("L5→L6 Empty Data", False, f"Expected 3 L6 errors, got: {validation_errors}")
            else:
                self.log_test("L5→L6 Empty Data", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L5→L6 Empty Data", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_valid_l6_data(self, opportunity_id):
        """Test L5→L6 with valid L6 data"""
        try:
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000,
                    "client_poc": "John Smith - CTO",
                    "delivery_team": ["58767dce-a766-4287-87ab-ba59d9315327"]
                },
                "notes": "Testing L5→L6 with valid L6 data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=stage_transition_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("L5→L6 Valid L6 Data", True, "✅ Successfully transitioned with valid L6 data")
                
                # Verify upcoming project creation
                self.verify_upcoming_project_creation(opportunity_id)
            else:
                error_detail = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("L5→L6 Valid L6 Data", False, f"Status: {response.status_code}, Error: {error_detail}")
                
        except Exception as e:
            self.log_test("L5→L6 Valid L6 Data", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_l5_data_only(self, opportunity_id):
        """Test L5→L6 with only L5 data (should fail with L6 errors)"""
        try:
            stage_transition_data = {
                "target_stage": 6,
                "stage_data": {
                    # Only L5 fields, no L6 fields
                    "updated_price": 600000,
                    "po_number": "PO-2025-001",
                    "po_date": "2025-01-15"
                },
                "notes": "Testing L5→L6 with only L5 data"
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
                
                # Should have L6 validation errors, not L5
                l6_errors = [err for err in validation_errors if any(field in err.lower() for field in ['final value', 'client poc', 'delivery team'])]
                l5_errors = [err for err in validation_errors if any(field in err.lower() for field in ['updated price', 'po number', 'po date'])]
                
                if l6_errors and not l5_errors:
                    self.log_test("L5→L6 L5 Data Only", True, f"✅ CORRECTLY failed with L6 validation errors: {l6_errors}")
                elif l5_errors:
                    self.log_test("L5→L6 L5 Data Only", False, f"❌ INCORRECTLY failed with L5 validation errors: {l5_errors}")
                else:
                    self.log_test("L5→L6 L5 Data Only", False, f"Unexpected validation errors: {validation_errors}")
            else:
                self.log_test("L5→L6 L5 Data Only", False, f"Expected 400 validation error, got: {response.status_code}")
                
        except Exception as e:
            self.log_test("L5→L6 L5 Data Only", False, f"Exception: {str(e)}")
    
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
        """Run all comprehensive stage validation tests"""
        print("🚀 STARTING COMPREHENSIVE STAGE VALIDATION TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return False
        
        # Run test suites
        self.test_l1_to_l2_validation_comprehensive()
        self.test_l5_to_l6_validation_comprehensive()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE STAGE VALIDATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL COMPREHENSIVE STAGE VALIDATION TESTS PASSED!")
            print("✅ L1→L2 validation logic is working correctly")
            print("✅ L5→L6 validation logic is working correctly")
            print("✅ Stage validation fix is confirmed working")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ Some stage validation logic needs attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = ComprehensiveStageValidationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()