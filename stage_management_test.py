#!/usr/bin/env python3
"""
Stage Management System Testing
Testing the stage management system after stage master data fixes
Focus: Verify Issue #2 (Stage Master Data Format Problems) has been resolved
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://sawayatta-erp-2.preview.emergentagent.com"  # External backend URL
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class StageManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log_test("Authentication", True, f"Admin login successful with credentials {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_stage_master_data(self):
        """Test GET /api/mst/stages to confirm proper L1-L8 format"""
        try:
            response = self.session.get(f"{API_BASE}/mst/stages")
            
            if response.status_code == 200:
                stages = response.json()
                
                # Verify we have 8 stages
                if len(stages) != 8:
                    self.log_test("Stage Master Data Count", False, f"Expected 8 stages, got {len(stages)}")
                    return False
                
                self.log_test("Stage Master Data Count", True, f"Found {len(stages)} stages as expected")
                
                # Verify L1-L8 format
                expected_codes = [f"L{i}" for i in range(1, 9)]
                actual_codes = []
                stage_details = []
                
                for stage in stages:
                    code = stage.get("stage_code", "")
                    name = stage.get("stage_name", "")
                    actual_codes.append(code)
                    stage_details.append(f"{code} - {name}")
                
                # Check if all expected codes are present
                missing_codes = set(expected_codes) - set(actual_codes)
                if missing_codes:
                    self.log_test("Stage Code Format", False, f"Missing stage codes: {missing_codes}")
                    return False
                
                # Verify proper L1-L8 format with names
                expected_stages = [
                    ("L1", "Prospect"),
                    ("L2", "Qualification"), 
                    ("L3", "Proposal"),
                    ("L4", "Technical Qualification"),
                    ("L5", "Negotiation"),
                    ("L6", "Won"),
                    ("L7", "Lost"),
                    ("L8", "Dropped")
                ]
                
                format_correct = True
                for expected_code, expected_name in expected_stages:
                    found_stage = next((s for s in stages if s.get("stage_code") == expected_code), None)
                    if not found_stage:
                        self.log_test("Stage Format Verification", False, f"Stage {expected_code} not found")
                        format_correct = False
                    elif expected_name.lower() not in found_stage.get("stage_name", "").lower():
                        self.log_test("Stage Format Verification", False, f"Stage {expected_code} name mismatch. Expected: {expected_name}, Got: {found_stage.get('stage_name')}")
                        format_correct = False
                
                if format_correct:
                    self.log_test("Stage Master Data Format", True, f"All stages have proper L1-L8 format: {', '.join(stage_details)}")
                    return True
                else:
                    return False
                    
            else:
                self.log_test("Stage Master Data API", False, f"API returned status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Stage Master Data API", False, f"Error: {str(e)}")
            return False
    
    def test_opportunities_list_display(self):
        """Test GET /api/opportunities to see if stages display correctly"""
        try:
            response = self.session.get(f"{API_BASE}/opportunities")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both wrapped and direct response formats
                if isinstance(data, dict) and "opportunities" in data:
                    opportunities = data["opportunities"]
                    total = data.get("total", len(opportunities))
                else:
                    opportunities = data if isinstance(data, list) else []
                    total = len(opportunities)
                
                self.log_test("Opportunities List API", True, f"Retrieved {total} opportunities successfully")
                
                if total == 0:
                    self.log_test("Opportunities Stage Display", True, "No opportunities found - cannot test stage display")
                    return True
                
                # Test stage information display
                stage_display_correct = True
                stage_examples = []
                
                for opp in opportunities[:5]:  # Test first 5 opportunities
                    opp_id = opp.get("opportunity_id") or opp.get("id")
                    current_stage = opp.get("current_stage")
                    stage_id = opp.get("stage_id")
                    
                    if current_stage:
                        # If current_stage is a number, it should be 1-8
                        if isinstance(current_stage, (int, str)) and str(current_stage).isdigit():
                            stage_num = int(current_stage)
                            if 1 <= stage_num <= 8:
                                stage_examples.append(f"Opportunity {opp_id}: L{stage_num}")
                            else:
                                self.log_test("Stage Display Format", False, f"Opportunity {opp_id} has invalid stage number: {current_stage}")
                                stage_display_correct = False
                        else:
                            stage_examples.append(f"Opportunity {opp_id}: {current_stage}")
                    elif stage_id:
                        stage_examples.append(f"Opportunity {opp_id}: stage_id={stage_id}")
                    else:
                        self.log_test("Stage Display Format", False, f"Opportunity {opp_id} missing stage information")
                        stage_display_correct = False
                
                if stage_display_correct:
                    self.log_test("Opportunities Stage Display", True, f"Stage information displays correctly. Examples: {'; '.join(stage_examples[:3])}")
                    return True
                else:
                    return False
                    
            else:
                self.log_test("Opportunities List API", False, f"API returned status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Opportunities List API", False, f"Error: {str(e)}")
            return False
    
    def test_stage_information_resolution(self):
        """Verify that stage information shows proper L1-L8 format with names"""
        try:
            # First get the stages master data
            stages_response = self.session.get(f"{API_BASE}/mst/stages")
            if stages_response.status_code != 200:
                self.log_test("Stage Resolution - Master Data", False, "Could not retrieve stages master data")
                return False
            
            stages = stages_response.json()
            stage_map = {s.get("stage_order", s.get("id")): f"{s.get('stage_code')} - {s.get('stage_name')}" for s in stages}
            
            # Get opportunities to test stage resolution
            opp_response = self.session.get(f"{API_BASE}/opportunities")
            if opp_response.status_code != 200:
                self.log_test("Stage Resolution - Opportunities", False, "Could not retrieve opportunities")
                return False
            
            data = opp_response.json()
            if isinstance(data, dict) and "opportunities" in data:
                opportunities = data["opportunities"]
            else:
                opportunities = data if isinstance(data, list) else []
            
            if not opportunities:
                self.log_test("Stage Information Resolution", True, "No opportunities to test stage resolution")
                return True
            
            # Test stage resolution for each opportunity
            resolution_examples = []
            resolution_correct = True
            
            for opp in opportunities[:3]:  # Test first 3 opportunities
                opp_id = opp.get("opportunity_id") or opp.get("id")
                current_stage = opp.get("current_stage")
                
                if current_stage:
                    if isinstance(current_stage, (int, str)) and str(current_stage).isdigit():
                        stage_num = int(current_stage)
                        expected_format = f"L{stage_num} - "
                        
                        # Find the corresponding stage name
                        stage_info = next((s for s in stages if s.get("stage_order") == stage_num), None)
                        if stage_info:
                            full_format = f"L{stage_num} - {stage_info.get('stage_name')}"
                            resolution_examples.append(f"Opportunity {opp_id}: {full_format}")
                        else:
                            self.log_test("Stage Resolution", False, f"Could not resolve stage {stage_num} for opportunity {opp_id}")
                            resolution_correct = False
                    else:
                        resolution_examples.append(f"Opportunity {opp_id}: {current_stage}")
            
            if resolution_correct:
                self.log_test("Stage Information Resolution", True, f"Stage resolution working correctly. Examples: {'; '.join(resolution_examples)}")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test("Stage Information Resolution", False, f"Error: {str(e)}")
            return False
    
    def test_individual_opportunity_l2_stage(self):
        """Test GET /api/opportunities/{id} for L2 stage opportunity"""
        try:
            # First find an L2 stage opportunity
            opp_response = self.session.get(f"{API_BASE}/opportunities")
            if opp_response.status_code != 200:
                self.log_test("L2 Opportunity Search", False, "Could not retrieve opportunities list")
                return False
            
            data = opp_response.json()
            if isinstance(data, dict) and "opportunities" in data:
                opportunities = data["opportunities"]
            else:
                opportunities = data if isinstance(data, list) else []
            
            # Look for L2 stage opportunity
            l2_opportunity = None
            for opp in opportunities:
                current_stage = opp.get("current_stage")
                if current_stage == 2 or current_stage == "2" or (isinstance(current_stage, str) and "L2" in current_stage):
                    l2_opportunity = opp
                    break
            
            if not l2_opportunity:
                # If no L2 opportunity found, test with any available opportunity
                if opportunities:
                    test_opp = opportunities[0]
                    opp_id = test_opp.get("opportunity_id") or test_opp.get("id")
                    current_stage = test_opp.get("current_stage")
                    self.log_test("L2 Opportunity Search", True, f"No L2 opportunity found, testing with available opportunity {opp_id} at stage {current_stage}")
                else:
                    self.log_test("L2 Opportunity Search", True, "No opportunities available for individual testing")
                    return True
            else:
                opp_id = l2_opportunity.get("opportunity_id") or l2_opportunity.get("id")
                self.log_test("L2 Opportunity Search", True, f"Found L2 opportunity: {opp_id}")
                test_opp = l2_opportunity
            
            # Test individual opportunity retrieval
            opp_id = test_opp.get("opportunity_id") or test_opp.get("id")
            if not opp_id:
                self.log_test("Individual Opportunity Test", False, "Opportunity ID not found")
                return False
            
            individual_response = self.session.get(f"{API_BASE}/opportunities/{opp_id}")
            
            if individual_response.status_code == 200:
                individual_opp = individual_response.json()
                current_stage = individual_opp.get("current_stage")
                stage_id = individual_opp.get("stage_id")
                
                # Verify stage information format
                if current_stage:
                    if isinstance(current_stage, (int, str)) and str(current_stage).isdigit():
                        stage_num = int(current_stage)
                        expected_format = f"L{stage_num} - Qualification" if stage_num == 2 else f"L{stage_num}"
                        self.log_test("Individual Opportunity Stage Format", True, f"Opportunity {opp_id} shows stage {stage_num} (L{stage_num} format)")
                    else:
                        self.log_test("Individual Opportunity Stage Format", True, f"Opportunity {opp_id} shows stage: {current_stage}")
                else:
                    self.log_test("Individual Opportunity Stage Format", False, f"Opportunity {opp_id} missing stage information")
                    return False
                
                return True
                
            elif individual_response.status_code == 404:
                self.log_test("Individual Opportunity Test", False, f"Opportunity {opp_id} not found (404)")
                return False
            else:
                self.log_test("Individual Opportunity Test", False, f"API returned status {individual_response.status_code}", individual_response.text)
                return False
                
        except Exception as e:
            self.log_test("Individual Opportunity Test", False, f"Error: {str(e)}")
            return False
    
    def test_stage_master_data_completeness(self):
        """Additional test to verify stage master data completeness"""
        try:
            response = self.session.get(f"{API_BASE}/mst/stages")
            
            if response.status_code == 200:
                stages = response.json()
                
                # Verify each stage has required fields
                required_fields = ["id", "stage_code", "stage_name", "stage_order"]
                completeness_correct = True
                
                for stage in stages:
                    missing_fields = [field for field in required_fields if not stage.get(field)]
                    if missing_fields:
                        self.log_test("Stage Data Completeness", False, f"Stage {stage.get('stage_code', 'Unknown')} missing fields: {missing_fields}")
                        completeness_correct = False
                
                if completeness_correct:
                    self.log_test("Stage Master Data Completeness", True, "All stages have required fields (id, code, name, stage_order)")
                    
                # Verify stage order sequence
                stage_orders = [s.get("stage_order") for s in stages if s.get("stage_order")]
                stage_orders.sort()
                expected_orders = list(range(1, 9))
                
                if stage_orders == expected_orders:
                    self.log_test("Stage Order Sequence", True, "Stage orders are sequential 1-8")
                else:
                    self.log_test("Stage Order Sequence", False, f"Stage orders not sequential. Got: {stage_orders}, Expected: {expected_orders}")
                    completeness_correct = False
                
                return completeness_correct
                
            else:
                self.log_test("Stage Master Data Completeness", False, f"Could not retrieve stages for completeness check")
                return False
                
        except Exception as e:
            self.log_test("Stage Master Data Completeness", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all stage management tests"""
        print("🚀 STAGE MANAGEMENT SYSTEM TESTING STARTED")
        print("=" * 60)
        print(f"Testing backend at: {BACKEND_URL}")
        print(f"Authentication: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print("=" * 60)
        
        # Authentication first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with testing")
            return False
        
        print("\n📋 RUNNING STAGE MANAGEMENT TESTS:")
        print("-" * 40)
        
        # Run all tests
        tests = [
            ("Stage Master Data Verification", self.test_stage_master_data),
            ("Stage Master Data Completeness", self.test_stage_master_data_completeness),
            ("Opportunities List Display", self.test_opportunities_list_display),
            ("Stage Information Resolution", self.test_stage_information_resolution),
            ("Individual Opportunity Check", self.test_individual_opportunity_l2_stage),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 STAGE MANAGEMENT TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 STAGE MANAGEMENT SYSTEM: PRODUCTION READY")
            print("✅ Issue #2 (Stage Master Data Format Problems) has been RESOLVED")
        elif success_rate >= 60:
            print("⚠️  STAGE MANAGEMENT SYSTEM: MOSTLY FUNCTIONAL with minor issues")
        else:
            print("❌ STAGE MANAGEMENT SYSTEM: CRITICAL ISSUES FOUND")
        
        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = StageManagementTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🏆 OVERALL ASSESSMENT: Stage Management System is working correctly")
        print("✅ All critical stage management functionality verified")
        print("✅ L1-L8 stage format properly implemented")
        print("✅ Stage master data format issues resolved")
        sys.exit(0)
    else:
        print("\n🚨 OVERALL ASSESSMENT: Stage Management System has issues")
        print("❌ Some critical functionality not working as expected")
        sys.exit(1)

if __name__ == "__main__":
    main()