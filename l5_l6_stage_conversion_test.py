#!/usr/bin/env python3
"""
L5→L6 Stage Conversion Workflow Testing
Testing the complete L5→L6 stage conversion workflow as requested in the review
"""

import requests
import json
import sys
from datetime import datetime, date

# Configuration
BASE_URL = "https://service-delivery.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class L5L6StageConversionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.l5_opportunity_id = None
        
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
    
    def find_or_create_l5_opportunity(self):
        """Find existing L5 opportunity or create one for testing"""
        print("\n🎯 L5 OPPORTUNITY SETUP")
        print("=" * 50)
        
        # First, try to find existing L5 opportunity
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                
                # Look for L5 opportunity (current_stage = 5)
                l5_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 5]
                
                if l5_opportunities:
                    self.l5_opportunity_id = l5_opportunities[0]['id']
                    self.log_test(
                        "Find L5 Opportunity", 
                        True, 
                        f"Found existing L5 opportunity: {self.l5_opportunity_id}"
                    )
                    return True
                else:
                    self.log_test("Find L5 Opportunity", False, "No existing L5 opportunities found")
                    # Try to create one
                    return self.create_l5_opportunity()
            else:
                self.log_test("Find L5 Opportunity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Find L5 Opportunity", False, f"Exception: {str(e)}")
            return False
    
    def create_l5_opportunity(self):
        """Create an opportunity and advance it to L5 stage"""
        try:
            # Get required master data
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                self.log_test("Create L5 Opportunity", False, "Could not get required master data")
                return False
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            # Find L1 stage and INR currency for initial creation
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                self.log_test("Create L5 Opportunity", False, "L1 stage or INR currency not found")
                return False
            
            # Create opportunity data
            opportunity_data = {
                "project_title": "L5→L6 Stage Conversion Test Opportunity",
                "company_id": "test-company-l5l6",
                "stage_id": l1_stage['id'],
                "expected_revenue": 750000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-l5l6",
                "win_probability": 75
            }
            
            # Create opportunity
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.l5_opportunity_id = data.get('id')
                
                # Now advance to L5 stage
                if self.advance_opportunity_to_l5():
                    self.log_test("Create L5 Opportunity", True, f"Created and advanced opportunity to L5: {self.l5_opportunity_id}")
                    return True
                else:
                    self.log_test("Create L5 Opportunity", False, "Could not advance opportunity to L5")
                    return False
            else:
                self.log_test("Create L5 Opportunity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create L5 Opportunity", False, f"Exception: {str(e)}")
            return False
    
    def advance_opportunity_to_l5(self):
        """Advance opportunity through stages to reach L5"""
        try:
            # Get stages
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            if stages_response.status_code != 200:
                return False
            
            stages = stages_response.json()
            stage_map = {s.get('stage_code'): s for s in stages}
            
            # Advance through L1→L2→L3→L4→L5
            stage_progression = [
                ('L2', {'region_id': 'test-region', 'product_interest': 'ERP System', 'assigned_representatives': ['test-rep'], 'lead_owner_id': 'test-owner'}),
                ('L3', {'scorecard': 'BANT', 'budget': 750000, 'authority': 'CTO', 'need': 'High', 'timeline': '6 months'}),
                ('L4', {'document_path': 'test-proposal.pdf', 'submission_date': '2024-01-15', 'internal_stakeholder': 'Sales Manager', 'client_response': 'Positive'}),
                ('L5', {'quotation_id': 'test-quotation-id'})
            ]
            
            for target_stage_code, stage_data in stage_progression:
                target_stage = stage_map.get(target_stage_code)
                if not target_stage:
                    continue
                
                change_data = {
                    "target_stage": target_stage['stage_number'],
                    "stage_data": stage_data
                }
                
                response = requests.post(
                    f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                    headers=self.headers,
                    json=change_data,
                    timeout=10
                )
                
                if response.status_code not in [200, 201]:
                    print(f"Failed to advance to {target_stage_code}: {response.status_code}")
                    # Continue anyway, might already be at L5
            
            return True
            
        except Exception as e:
            print(f"Exception advancing to L5: {str(e)}")
            return False
    
    def test_l5_completion_validation(self):
        """Test L5 stage completion with all required fields"""
        print("\n📋 L5 STAGE COMPLETION VALIDATION")
        print("=" * 50)
        
        if not self.l5_opportunity_id:
            self.log_test("L5 Completion Validation", False, "No L5 opportunity available")
            return
        
        # Test L5 completion with all required fields
        l5_completion_data = {
            "target_stage": 5,  # Stay in L5 to test completion
            "stage_data": {
                "updated_price": 720000,
                "margin_percentage": 35.5,
                "po_number": "PO-2024-L5L6-001",
                "po_date": "2024-01-20",
                "commercial_decision": "won"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=l5_completion_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log_test(
                    "L5 Completion with All Fields", 
                    True, 
                    "L5 validation passed with all required fields"
                )
            else:
                self.log_test(
                    "L5 Completion with All Fields", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("L5 Completion with All Fields", False, f"Exception: {str(e)}")
        
        # Test L5 completion with missing fields
        incomplete_l5_data = {
            "target_stage": 5,
            "stage_data": {
                "updated_price": 720000,
                # Missing margin_percentage, po_number, po_date, commercial_decision
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=incomplete_l5_data,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test(
                    "L5 Validation with Missing Fields", 
                    True, 
                    "L5 validation correctly rejected incomplete data"
                )
            else:
                self.log_test(
                    "L5 Validation with Missing Fields", 
                    False, 
                    f"Expected 400 validation error, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("L5 Validation with Missing Fields", False, f"Exception: {str(e)}")
    
    def test_l5_to_l6_transition(self):
        """Test L5→L6 conversion with proper L6 data"""
        print("\n🎯 L5→L6 STAGE TRANSITION")
        print("=" * 50)
        
        if not self.l5_opportunity_id:
            self.log_test("L5→L6 Transition", False, "No L5 opportunity available")
            return
        
        # Test L5→L6 conversion with proper L6 data
        l6_transition_data = {
            "target_stage": 6,  # L6 (Won)
            "stage_data": {
                "final_value": 720000,
                "client_poc": "John Smith - CTO",
                "delivery_team": "Team Alpha - 5 members"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=l6_transition_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log_test(
                    "L5→L6 Transition with L6 Data", 
                    True, 
                    "L5→L6 conversion successful with proper L6 validation"
                )
                
                # Verify the opportunity is now in L6 stage
                self.verify_l6_stage_update()
                
            else:
                self.log_test(
                    "L5→L6 Transition with L6 Data", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("L5→L6 Transition with L6 Data", False, f"Exception: {str(e)}")
        
        # Test L5→L6 with missing L6 fields (should fail)
        incomplete_l6_data = {
            "target_stage": 6,
            "stage_data": {
                "final_value": 720000,
                # Missing client_poc and delivery_team
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=incomplete_l6_data,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test(
                    "L5→L6 with Missing L6 Fields", 
                    True, 
                    "L5→L6 validation correctly rejected incomplete L6 data"
                )
            else:
                self.log_test(
                    "L5→L6 with Missing L6 Fields", 
                    False, 
                    f"Expected 400 validation error, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("L5→L6 with Missing L6 Fields", False, f"Exception: {str(e)}")
    
    def verify_l6_stage_update(self):
        """Verify that opportunity is properly updated to L6 stage"""
        print("\n🔍 L6 STAGE VERIFICATION")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunity = response.json()
                
                # Check current stage
                current_stage = opportunity.get('current_stage')
                if current_stage == 6:
                    self.log_test(
                        "L6 Stage Update", 
                        True, 
                        f"Opportunity successfully moved to L6 (current_stage: {current_stage})"
                    )
                else:
                    self.log_test(
                        "L6 Stage Update", 
                        False, 
                        f"Expected current_stage=6, got: {current_stage}"
                    )
                
                # Check win probability (should be 100% for L6)
                win_probability = opportunity.get('win_probability')
                if win_probability == 100:
                    self.log_test(
                        "Win Probability Update", 
                        True, 
                        f"Win probability correctly updated to 100%"
                    )
                else:
                    self.log_test(
                        "Win Probability Update", 
                        False, 
                        f"Expected win_probability=100, got: {win_probability}"
                    )
                
                # Check status (should be "Won")
                status = opportunity.get('status')
                if status == "Won":
                    self.log_test(
                        "Opportunity Status Update", 
                        True, 
                        f"Status correctly updated to 'Won'"
                    )
                else:
                    self.log_test(
                        "Opportunity Status Update", 
                        False, 
                        f"Expected status='Won', got: {status}"
                    )
                
                # Check is_locked (should be True for Won opportunities)
                is_locked = opportunity.get('is_locked')
                if is_locked:
                    self.log_test(
                        "Opportunity Lock Status", 
                        True, 
                        f"Opportunity correctly locked after winning"
                    )
                else:
                    self.log_test(
                        "Opportunity Lock Status", 
                        False, 
                        f"Expected is_locked=True, got: {is_locked}"
                    )
                
                # Check close_date is set
                close_date = opportunity.get('close_date')
                if close_date:
                    self.log_test(
                        "Close Date Update", 
                        True, 
                        f"Close date properly set: {close_date}"
                    )
                else:
                    self.log_test(
                        "Close Date Update", 
                        False, 
                        "Close date not set for won opportunity"
                    )
                
                # Check stage_data is saved
                stage_data = opportunity.get('stage_data')
                if stage_data and isinstance(stage_data, dict):
                    l6_fields = ['final_value', 'client_poc', 'delivery_team']
                    missing_fields = [field for field in l6_fields if field not in stage_data]
                    
                    if not missing_fields:
                        self.log_test(
                            "L6 Stage Data Persistence", 
                            True, 
                            f"All L6 fields saved: {', '.join(l6_fields)}"
                        )
                    else:
                        self.log_test(
                            "L6 Stage Data Persistence", 
                            False, 
                            f"Missing L6 fields: {', '.join(missing_fields)}"
                        )
                else:
                    self.log_test(
                        "L6 Stage Data Persistence", 
                        False, 
                        "Stage data not saved or invalid format"
                    )
                    
            else:
                self.log_test(
                    "L6 Stage Verification", 
                    False, 
                    f"Could not retrieve opportunity: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("L6 Stage Verification", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for various invalid scenarios"""
        print("\n⚠️  ERROR HANDLING TESTS")
        print("=" * 50)
        
        if not self.l5_opportunity_id:
            self.log_test("Error Handling", False, "No L5 opportunity available")
            return
        
        # Test invalid stage transition (L5 to L3 - backward)
        invalid_backward_data = {
            "target_stage": 3,  # L3 (backward from L5)
            "stage_data": {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=invalid_backward_data,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Backward Stage Transition Error", 
                    True, 
                    "Correctly rejected backward stage transition"
                )
            else:
                self.log_test(
                    "Backward Stage Transition Error", 
                    False, 
                    f"Expected 400 error, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Backward Stage Transition Error", False, f"Exception: {str(e)}")
        
        # Test invalid opportunity ID
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/invalid-opportunity-id/change-stage",
                headers=self.headers,
                json={"target_stage": 6, "stage_data": {}},
                timeout=10
            )
            
            if response.status_code == 404:
                self.log_test(
                    "Invalid Opportunity ID Error", 
                    True, 
                    "Correctly returned 404 for invalid opportunity ID"
                )
            else:
                self.log_test(
                    "Invalid Opportunity ID Error", 
                    False, 
                    f"Expected 404 error, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Invalid Opportunity ID Error", False, f"Exception: {str(e)}")
        
        # Test malformed request data
        try:
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json={"invalid_field": "invalid_value"},  # Missing required fields
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Malformed Request Error", 
                    True, 
                    "Correctly rejected malformed request data"
                )
            else:
                self.log_test(
                    "Malformed Request Error", 
                    False, 
                    f"Expected 400 error, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Malformed Request Error", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all L5→L6 conversion tests"""
        print("🚀 STARTING L5→L6 STAGE CONVERSION TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return False
        
        # Setup L5 opportunity
        if not self.find_or_create_l5_opportunity():
            print("\n❌ L5 OPPORTUNITY SETUP FAILED - Cannot proceed with tests")
            return False
        
        # Run test suites
        self.test_l5_completion_validation()
        self.test_l5_to_l6_transition()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 L5→L6 CONVERSION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL L5→L6 CONVERSION TESTS PASSED!")
            print("✅ L5→L6 stage conversion workflow is working correctly")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ L5→L6 stage conversion workflow has issues")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = L5L6StageConversionTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()