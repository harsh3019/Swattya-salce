#!/usr/bin/env python3
"""
L6 Stage Transition and SD Integration Testing
Testing the CRITICAL FIX for L6 stage transition validation and automatic upcoming project creation
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

class L6StageTransitionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.l5_opportunity_id = None
        self.created_project_id = None
        
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

    def find_l5_opportunity(self):
        """Find an existing opportunity in L5 stage or create one from L4"""
        print("\n🔍 FINDING L5 OPPORTUNITY")
        print("=" * 50)
        
        try:
            # First, try to find existing L5 opportunity
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
                
                # Look for L5 opportunity
                l5_opportunities = [opp for opp in opportunities if opp.get("current_stage") == 5]
                
                if l5_opportunities:
                    self.l5_opportunity_id = l5_opportunities[0]["id"]
                    self.log_test(
                        "Find L5 Opportunity", 
                        True, 
                        f"Found existing L5 opportunity: {self.l5_opportunity_id}"
                    )
                    return True
                else:
                    # Look for L4 opportunity to move to L5
                    l4_opportunities = [opp for opp in opportunities if opp.get("current_stage") == 4]
                    if l4_opportunities:
                        self.l5_opportunity_id = l4_opportunities[0]["id"]
                        self.log_test(
                            "Find L4 Opportunity", 
                            True, 
                            f"Found L4 opportunity to move to L5: {self.l5_opportunity_id}"
                        )
                        # Move to L5
                        return self.move_l4_to_l5()
                    else:
                        # Look for any opportunity to move through stages
                        if opportunities:
                            self.l5_opportunity_id = opportunities[0]["id"]
                            current_stage = opportunities[0].get("current_stage", 1)
                            self.log_test(
                                "Find Any Opportunity", 
                                True, 
                                f"Found L{current_stage} opportunity to move to L5: {self.l5_opportunity_id}"
                            )
                            return self.move_opportunity_to_l5()
                        else:
                            self.log_test("Find L5 Opportunity", False, "No opportunities found in system")
                            return False
            else:
                self.log_test("Find L5 Opportunity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Find L5 Opportunity", False, f"Exception: {str(e)}")
            return False

    def move_l4_to_l5(self):
        """Move L4 opportunity to L5 stage"""
        try:
            # L5 stage data
            l5_stage_data = {
                "updated_price": 750000,
                "margin_percentage": 35.0,
                "po_number": "PO-TEST-L6-001",
                "po_date": date.today().isoformat(),
                "commercial_decision": "won"
            }
            
            transition_data = {
                "target_stage": 5,
                "stage_data": l5_stage_data,
                "notes": "Moving L4 to L5 for L6 transition testing"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=transition_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log_test("Move L4 to L5", True, "Successfully moved L4 opportunity to L5")
                return True
            else:
                self.log_test("Move L4 to L5", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Move L4 to L5", False, f"Exception: {str(e)}")
            return False

    def create_l5_opportunity(self):
        """Create an opportunity in L5 stage for testing"""
        try:
            # Get required master data
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                self.log_test("Create L5 Opportunity", False, "Could not get required master data")
                return False
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            # Find L1 stage and INR currency (create at L1 first)
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                self.log_test("Create L5 Opportunity", False, "L1 stage or INR currency not found in master data")
                return False
            
            # Create opportunity data at L1 first
            opportunity_data = {
                "project_title": "L6 Transition Test Opportunity",
                "company_id": "test-company-l6-transition",
                "stage_id": l1_stage['id'],
                "expected_revenue": 750000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-l6",
                "win_probability": 10
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.l5_opportunity_id = data.get('id')
                
                # Move to L5 stage
                if self.move_opportunity_to_l5():
                    self.log_test(
                        "Create L5 Opportunity", 
                        True, 
                        f"Created and moved opportunity to L5: {self.l5_opportunity_id}"
                    )
                    return True
                else:
                    self.log_test("Create L5 Opportunity", False, "Failed to move opportunity to L5")
                    return False
            else:
                self.log_test("Create L5 Opportunity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create L5 Opportunity", False, f"Exception: {str(e)}")
            return False

    def move_opportunity_to_l5(self):
        """Move opportunity to L5 stage with required data"""
        try:
            # Move through stages L1 -> L2 -> L3 -> L4 -> L5
            stages_to_move = [2, 3, 4, 5]
            
            for target_stage in stages_to_move:
                stage_data = self.get_stage_data_for_stage(target_stage)
                
                transition_data = {
                    "target_stage": target_stage,
                    "stage_data": stage_data,
                    "notes": f"Moving to L{target_stage} for L6 transition testing"
                }
                
                response = requests.post(
                    f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                    headers=self.headers,
                    json=transition_data,
                    timeout=10
                )
                
                if response.status_code not in [200, 201]:
                    self.log_test(f"Move to L{target_stage}", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                    return False
            
            self.log_test("Move Opportunity to L5", True, "Successfully moved opportunity to L5 stage")
            return True
            
        except Exception as e:
            self.log_test("Move Opportunity to L5", False, f"Exception: {str(e)}")
            return False

    def get_stage_data_for_stage(self, stage):
        """Get minimal required data for each stage"""
        if stage == 2:  # L2
            return {
                "scorecard": "BANT",
                "budget_confirmed": True,
                "authority_identified": True,
                "need_established": True,
                "timeline_defined": True
            }
        elif stage == 3:  # L3
            return {
                "proposal_submitted": True,
                "submission_date": date.today().isoformat(),
                "internal_stakeholder": "Test Stakeholder",
                "client_response": "Positive"
            }
        elif stage == 4:  # L4
            return {
                "selected_quotation_id": "test-quotation-id"
            }
        elif stage == 5:  # L5
            return {
                "updated_price": 750000,
                "margin_percentage": 35.0,
                "po_number": "PO-TEST-L6-001",
                "po_date": date.today().isoformat(),
                "commercial_decision": "won"
            }
        return {}

    def test_l6_validation_fix(self):
        """Test L6 stage validation fix - should check TARGET stage data, not current stage"""
        print("\n🎯 TESTING L6 STAGE VALIDATION FIX")
        print("=" * 50)
        
        if not self.l5_opportunity_id:
            self.log_test("L6 Validation Fix", False, "No L5 opportunity available for testing")
            return
        
        # Test 1: L6 transition with missing required fields (should fail)
        self.test_l6_missing_fields()
        
        # Test 2: L6 transition with valid L6 data (should succeed)
        self.test_l6_valid_transition()

    def test_l6_missing_fields(self):
        """Test L6 transition with missing required fields"""
        try:
            # Try L6 transition with incomplete data
            incomplete_l6_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000,
                    # Missing client_poc and delivery_team
                },
                "notes": "Testing L6 validation with missing fields"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=incomplete_l6_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_data = response.json()
                validation_errors = error_data.get("detail", {}).get("validation_errors", [])
                
                # Check if proper L6 validation errors are returned
                expected_errors = ["Client POC is required for L6 - Won", "Delivery Team is required for L6 - Won"]
                found_errors = [err for err in validation_errors if any(expected in err for expected in expected_errors)]
                
                if len(found_errors) >= 2:
                    self.log_test(
                        "L6 Missing Fields Validation", 
                        True, 
                        f"Correctly rejected L6 transition with validation errors: {validation_errors}"
                    )
                else:
                    self.log_test(
                        "L6 Missing Fields Validation", 
                        False, 
                        f"Expected L6 validation errors not found. Got: {validation_errors}"
                    )
            else:
                self.log_test(
                    "L6 Missing Fields Validation", 
                    False, 
                    f"Expected 400 validation error, got status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("L6 Missing Fields Validation", False, f"Exception: {str(e)}")

    def test_l6_valid_transition(self):
        """Test L6 transition with valid L6 data"""
        try:
            # L6 transition with complete valid data
            valid_l6_data = {
                "target_stage": 6,
                "stage_data": {
                    "final_value": 750000,
                    "client_poc": "John Smith - Project Manager",
                    "delivery_team": ["team-member-1", "team-member-2", "team-member-3"],
                    "kickoff_task": "Initial project kickoff meeting scheduled"
                },
                "notes": "L6 transition with complete valid data"
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}/change-stage",
                headers=self.headers,
                json=valid_l6_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log_test(
                    "L6 Valid Transition", 
                    True, 
                    "Successfully transitioned to L6 with valid data"
                )
                
                # Verify opportunity is now in Won status
                self.verify_won_status()
                
                return True
            else:
                self.log_test(
                    "L6 Valid Transition", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("L6 Valid Transition", False, f"Exception: {str(e)}")
            return False

    def verify_won_status(self):
        """Verify opportunity shows as Won status after L6 transition"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunity = response.json()
                
                current_stage = opportunity.get("current_stage")
                status = opportunity.get("status")
                is_locked = opportunity.get("is_locked")
                
                if current_stage == 6 and status == "Won" and is_locked:
                    self.log_test(
                        "Verify Won Status", 
                        True, 
                        f"Opportunity correctly shows: Stage L6, Status: {status}, Locked: {is_locked}"
                    )
                else:
                    self.log_test(
                        "Verify Won Status", 
                        False, 
                        f"Incorrect status: Stage L{current_stage}, Status: {status}, Locked: {is_locked}"
                    )
            else:
                self.log_test("Verify Won Status", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Verify Won Status", False, f"Exception: {str(e)}")

    def test_automatic_upcoming_project_creation(self):
        """Test automatic upcoming project creation after L6 transition"""
        print("\n🚀 TESTING AUTOMATIC UPCOMING PROJECT CREATION")
        print("=" * 50)
        
        # Test SD upcoming projects API
        self.test_sd_upcoming_projects_api()
        
        # Verify project was created for our won opportunity
        self.verify_project_creation()

    def test_sd_upcoming_projects_api(self):
        """Test SD upcoming projects API endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                project_count = len(projects) if isinstance(projects, list) else 0
                
                self.log_test(
                    "SD Upcoming Projects API", 
                    True, 
                    f"Retrieved {project_count} upcoming projects"
                )
                
                # Store projects for verification
                self.upcoming_projects = projects
                return True
            else:
                self.log_test(
                    "SD Upcoming Projects API", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("SD Upcoming Projects API", False, f"Exception: {str(e)}")
            return False

    def verify_project_creation(self):
        """Verify that upcoming project was created for our won opportunity"""
        try:
            if not hasattr(self, 'upcoming_projects'):
                self.log_test("Verify Project Creation", False, "No upcoming projects data available")
                return
            
            # Get opportunity details to find the opportunity_id
            opp_response = requests.get(
                f"{self.base_url}/opportunities/{self.l5_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if opp_response.status_code != 200:
                self.log_test("Verify Project Creation", False, "Could not get opportunity details")
                return
            
            opportunity = opp_response.json()
            opportunity_id = opportunity.get("opportunity_id")  # The OPP-XXXXXXX format ID
            
            # Look for project with matching opp_id
            matching_projects = [
                proj for proj in self.upcoming_projects 
                if proj.get("opp_id") == opportunity_id
            ]
            
            if matching_projects:
                project = matching_projects[0]
                self.created_project_id = project.get("id")
                
                # Verify project has required fields
                required_fields = ["order_id", "opp_id", "customer_name", "setup_cost"]
                missing_fields = [field for field in required_fields if not project.get(field)]
                
                if not missing_fields:
                    self.log_test(
                        "Verify Project Creation", 
                        True, 
                        f"Found upcoming project for opportunity {opportunity_id}: Order ID {project.get('order_id')}, Setup Cost: ₹{project.get('setup_cost'):,.2f}"
                    )
                else:
                    self.log_test(
                        "Verify Project Creation", 
                        False, 
                        f"Project found but missing fields: {missing_fields}"
                    )
            else:
                self.log_test(
                    "Verify Project Creation", 
                    False, 
                    f"No upcoming project found for opportunity {opportunity_id}"
                )
                
        except Exception as e:
            self.log_test("Verify Project Creation", False, f"Exception: {str(e)}")

    def test_integration_function_manually(self):
        """Test the integration function manually using the test trigger endpoint"""
        print("\n🔧 TESTING INTEGRATION FUNCTION MANUALLY")
        print("=" * 50)
        
        if not self.l5_opportunity_id:
            self.log_test("Manual Integration Test", False, "No opportunity available for testing")
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/test/trigger-upcoming-project/{self.l5_opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "project_id" in result:
                    self.log_test(
                        "Manual Integration Test", 
                        True, 
                        f"Integration function executed successfully: {result.get('message', 'Success')}"
                    )
                elif "already exists" in result.get("message", "").lower():
                    self.log_test(
                        "Manual Integration Test", 
                        True, 
                        f"Integration function correctly detected duplicate: {result.get('message')}"
                    )
                else:
                    self.log_test(
                        "Manual Integration Test", 
                        False, 
                        f"Unexpected response: {result}"
                    )
            else:
                self.log_test(
                    "Manual Integration Test", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Manual Integration Test", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all L6 stage transition and SD integration tests"""
        print("🚀 STARTING L6 STAGE TRANSITION AND SD INTEGRATION TESTING")
        print("=" * 70)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Find or create L5 opportunity
        if not self.find_l5_opportunity():
            print("\n❌ COULD NOT FIND/CREATE L5 OPPORTUNITY - Cannot proceed with tests")
            return False
        
        # Run test suites
        self.test_l6_validation_fix()
        self.test_automatic_upcoming_project_creation()
        self.test_integration_function_manually()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 L6 STAGE TRANSITION & SD INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL L6 STAGE TRANSITION TESTS PASSED!")
            print("✅ L6 validation fix is working correctly")
            print("✅ SD integration is functional")
            print("✅ End-to-end workflow is operational")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ Some L6 stage transition or SD integration issues remain")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 50)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = L6StageTransitionTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()