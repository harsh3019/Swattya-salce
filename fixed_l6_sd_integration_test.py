#!/usr/bin/env python3
"""
FIXED L6→SD Integration Testing - Verify Won Opportunities Now Appear
Testing the FIXED L6→SD integration to ensure L6 Won opportunities now appear in upcoming projects list
This test specifically addresses the user's reported issue of L6 Won opportunities not appearing.
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://sawayatta-sd.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class FixedL6SDIntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.l6_opportunities = []
        self.upcoming_projects_before = []
        self.upcoming_projects_after = []
        self.critical_issues = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            # Track critical issues
            if "critical" in test_name.lower() or "integration" in test_name.lower():
                self.critical_issues.append(f"{test_name}: {details}")
        
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
    
    def find_l6_won_opportunities(self):
        """Find L6 Won opportunities in the system"""
        print("\n🎯 FINDING L6 WON OPPORTUNITIES")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get("opportunities", []) if isinstance(data, dict) else data
                
                # Filter for L6 Won opportunities
                l6_opportunities = []
                for opp in opportunities:
                    if opp.get("current_stage") == 6 and opp.get("status") == "Won":
                        l6_opportunities.append(opp)
                
                self.l6_opportunities = l6_opportunities
                
                if len(l6_opportunities) > 0:
                    self.log_test(
                        "Find L6 Won Opportunities", 
                        True, 
                        f"Found {len(l6_opportunities)} L6 Won opportunities"
                    )
                    
                    # Log details with opportunity_id format analysis
                    opp_format_analysis = {"OPP-": 0, "UUID": 0, "Other": 0}
                    for opp in l6_opportunities:
                        opp_id = opp.get("opportunity_id", opp.get("id", "Unknown"))
                        company_name = opp.get("company_name", "Unknown Company")
                        
                        # Analyze opportunity_id format
                        if isinstance(opp_id, str):
                            if opp_id.startswith("OPP-"):
                                opp_format_analysis["OPP-"] += 1
                            elif len(opp_id) == 36 and opp_id.count("-") == 4:  # UUID format
                                opp_format_analysis["UUID"] += 1
                            else:
                                opp_format_analysis["Other"] += 1
                        
                        print(f"   - {opp_id}: {company_name} (Stage: L{opp.get('current_stage')}, Status: {opp.get('status')})")
                    
                    print(f"   Format Analysis: OPP- format: {opp_format_analysis['OPP-']}, UUID format: {opp_format_analysis['UUID']}, Other: {opp_format_analysis['Other']}")
                    return True
                else:
                    self.log_test(
                        "Find L6 Won Opportunities", 
                        False, 
                        "No L6 Won opportunities found in system"
                    )
                    return False
            else:
                self.log_test(
                    "Find L6 Won Opportunities", 
                    False, 
                    f"Status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Find L6 Won Opportunities", False, f"Exception: {str(e)}")
            return False
    
    def get_upcoming_projects_baseline(self):
        """Get baseline upcoming projects before testing"""
        print("\n📊 GETTING UPCOMING PROJECTS BASELINE")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                self.upcoming_projects_before = projects
                
                self.log_test(
                    "Get Upcoming Projects Baseline", 
                    True, 
                    f"Found {len(projects)} existing upcoming projects"
                )
                
                # Analyze existing projects for opp_id format
                if projects:
                    opp_format_analysis = {"OPP-": 0, "UUID": 0, "Other": 0, "Missing": 0}
                    for project in projects:
                        opp_id = project.get("opp_id")
                        if not opp_id:
                            opp_format_analysis["Missing"] += 1
                        elif opp_id.startswith("OPP-"):
                            opp_format_analysis["OPP-"] += 1
                        elif len(str(opp_id)) == 36 and str(opp_id).count("-") == 4:  # UUID format
                            opp_format_analysis["UUID"] += 1
                        else:
                            opp_format_analysis["Other"] += 1
                    
                    print(f"   Existing Projects Opp ID Analysis: OPP-: {opp_format_analysis['OPP-']}, UUID: {opp_format_analysis['UUID']}, Other: {opp_format_analysis['Other']}, Missing: {opp_format_analysis['Missing']}")
                
                return True
            else:
                self.log_test(
                    "Get Upcoming Projects Baseline", 
                    False, 
                    f"Status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Get Upcoming Projects Baseline", False, f"Exception: {str(e)}")
            return False
    
    def test_manual_trigger_with_fixed_integration(self):
        """Test manual trigger endpoint POST /api/test/trigger-upcoming-project/{opportunity_id}"""
        print("\n🔧 TESTING MANUAL TRIGGER WITH FIXED INTEGRATION")
        print("=" * 50)
        
        if not self.l6_opportunities:
            self.log_test("Manual Trigger Test", False, "No L6 opportunities available for testing")
            return False
        
        success_count = 0
        total_count = len(self.l6_opportunities)
        
        for opp in self.l6_opportunities:
            opp_id = opp.get("id")  # Use database ID for API call
            opp_display_id = opp.get("opportunity_id", opp_id)
            
            try:
                response = requests.post(
                    f"{self.base_url}/test/trigger-upcoming-project/{opp_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", "")
                    
                    if "Successfully created" in message or "already exists" in message:
                        success_count += 1
                        self.log_test(
                            f"Manual Trigger: {opp_display_id}", 
                            True, 
                            f"{message}"
                        )
                    else:
                        self.log_test(
                            f"Manual Trigger: {opp_display_id}", 
                            False, 
                            f"Unexpected response: {message}"
                        )
                else:
                    self.log_test(
                        f"Manual Trigger: {opp_display_id}", 
                        False, 
                        f"Status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"Manual Trigger: {opp_display_id}", False, f"Exception: {str(e)}")
        
        # Overall manual trigger test result
        if success_count == total_count:
            self.log_test(
                "CRITICAL: Manual Trigger Integration", 
                True, 
                f"All {success_count}/{total_count} L6 opportunities processed successfully"
            )
            return True
        else:
            self.log_test(
                "CRITICAL: Manual Trigger Integration", 
                False, 
                f"Only {success_count}/{total_count} L6 opportunities processed successfully"
            )
            return False
    
    def verify_upcoming_projects_visibility(self):
        """Verify L6 Won opportunities now appear in upcoming projects list"""
        print("\n👁️ VERIFYING UPCOMING PROJECTS VISIBILITY")
        print("=" * 50)
        
        try:
            # Wait a moment for database consistency
            time.sleep(2)
            
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                self.upcoming_projects_after = projects
                
                # Check if L6 opportunities appear in upcoming projects
                l6_opp_ids = set()
                for opp in self.l6_opportunities:
                    # Check both opportunity_id and id fields
                    opp_id = opp.get("opportunity_id")
                    if opp_id:
                        l6_opp_ids.add(opp_id)
                    # Also add UUID-based ID as fallback
                    uuid_id = opp.get("id")
                    if uuid_id:
                        l6_opp_ids.add(uuid_id)
                
                project_opp_ids = set()
                for project in projects:
                    opp_id = project.get("opp_id")
                    if opp_id:
                        project_opp_ids.add(opp_id)
                
                # Find matches
                matched_opportunities = l6_opp_ids.intersection(project_opp_ids)
                missing_opportunities = l6_opp_ids - project_opp_ids
                
                self.log_test(
                    "Get Updated Upcoming Projects", 
                    True, 
                    f"Retrieved {len(projects)} upcoming projects after trigger"
                )
                
                if len(matched_opportunities) > 0:
                    match_percentage = (len(matched_opportunities) / len(l6_opp_ids)) * 100
                    self.log_test(
                        "CRITICAL: L6 Opportunities Visibility", 
                        len(matched_opportunities) == len(l6_opp_ids), 
                        f"{len(matched_opportunities)}/{len(l6_opp_ids)} L6 opportunities visible ({match_percentage:.1f}%)"
                    )
                    
                    # Log matched opportunities
                    print("   ✅ VISIBLE L6 OPPORTUNITIES:")
                    for matched_id in matched_opportunities:
                        print(f"      - {matched_id}")
                    
                    # Log missing opportunities if any
                    if missing_opportunities:
                        print(f"   ❌ STILL MISSING {len(missing_opportunities)} OPPORTUNITIES:")
                        for missing_id in missing_opportunities:
                            print(f"      - {missing_id}")
                    
                    return len(matched_opportunities) == len(l6_opp_ids)
                else:
                    self.log_test(
                        "CRITICAL: L6 Opportunities Visibility", 
                        False, 
                        f"NONE of the {len(l6_opp_ids)} L6 opportunities appear in upcoming projects list"
                    )
                    return False
            else:
                self.log_test(
                    "CRITICAL: Verify Upcoming Projects Visibility", 
                    False, 
                    f"Status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("CRITICAL: Verify Upcoming Projects Visibility", False, f"Exception: {str(e)}")
            return False
    
    def test_opp_id_format_fix(self):
        """Test that opp_id field contains proper opportunity_id format (OPP-XXXXXXXX)"""
        print("\n🔍 TESTING OPP_ID FORMAT FIX")
        print("=" * 50)
        
        if not self.upcoming_projects_after:
            self.log_test("Opp ID Format Fix", False, "No upcoming projects data available")
            return False
        
        format_issues = []
        correct_formats = 0
        
        for project in self.upcoming_projects_after:
            opp_id = project.get("opp_id")
            
            if opp_id:
                # Check if it's in OPP-XXXXXXXX format (the fix should ensure this)
                if opp_id.startswith("OPP-") and len(opp_id) >= 11:
                    correct_formats += 1
                elif len(str(opp_id)) == 36 and str(opp_id).count("-") == 4:  # UUID format (old issue)
                    format_issues.append(f"Still using UUID format: {opp_id}")
                else:
                    format_issues.append(f"Invalid format: {opp_id}")
            else:
                format_issues.append("Missing opp_id field")
        
        if len(format_issues) == 0:
            self.log_test(
                "CRITICAL: Opp ID Format Fix", 
                True, 
                f"All {len(self.upcoming_projects_after)} projects use correct OPP-XXXXXXXX format"
            )
            return True
        else:
            self.log_test(
                "CRITICAL: Opp ID Format Fix", 
                False, 
                f"Found {len(format_issues)} format issues: {correct_formats} correct, {len(format_issues)} incorrect"
            )
            # Log first few issues for debugging
            for issue in format_issues[:3]:
                print(f"   - {issue}")
            return False
    
    def test_integration_function_fix(self):
        """Test that integration function uses correct opportunity.get('opportunity_id') instead of UUID"""
        print("\n⚙️ TESTING INTEGRATION FUNCTION FIX")
        print("=" * 50)
        
        # This test verifies the fix by checking if projects created have the correct opp_id mapping
        if not self.l6_opportunities or not self.upcoming_projects_after:
            self.log_test("Integration Function Fix", False, "Insufficient data for testing")
            return False
        
        # Check if the integration function is using opportunity_id correctly
        correct_mappings = 0
        incorrect_mappings = 0
        
        for opp in self.l6_opportunities:
            expected_opp_id = opp.get("opportunity_id")  # This should be used by the fixed function
            
            if expected_opp_id:
                # Find corresponding project
                found_project = None
                for project in self.upcoming_projects_after:
                    if project.get("opp_id") == expected_opp_id:
                        found_project = project
                        break
                
                if found_project:
                    correct_mappings += 1
                    print(f"   ✅ Correct mapping: {expected_opp_id} → Project {found_project.get('id', 'Unknown')}")
                else:
                    incorrect_mappings += 1
                    print(f"   ❌ Missing mapping: {expected_opp_id}")
        
        if correct_mappings > 0 and incorrect_mappings == 0:
            self.log_test(
                "CRITICAL: Integration Function Fix", 
                True, 
                f"Integration function correctly uses opportunity_id field ({correct_mappings} correct mappings)"
            )
            return True
        else:
            self.log_test(
                "CRITICAL: Integration Function Fix", 
                False, 
                f"Integration function issues: {correct_mappings} correct, {incorrect_mappings} incorrect mappings"
            )
            return False
    
    def test_schema_verification(self):
        """Verify all required fields are populated correctly"""
        print("\n📋 TESTING SCHEMA VERIFICATION")
        print("=" * 50)
        
        if not self.upcoming_projects_after:
            self.log_test("Schema Verification", False, "No upcoming projects data available")
            return False
        
        required_fields = [
            "id", "order_id", "opp_id", "pot_id", "customer_name", 
            "setup_cost", "opp_status", "order_status", "created_at"
        ]
        
        schema_issues = []
        valid_projects = 0
        
        for project in self.upcoming_projects_after:
            project_issues = []
            
            # Check required fields
            for field in required_fields:
                if field not in project or project[field] is None:
                    project_issues.append(f"Missing {field}")
            
            # Verify specific field formats
            if project.get("order_id") and not project.get("order_id").startswith("OA-"):
                project_issues.append(f"Invalid order_id format: {project.get('order_id')}")
            
            if project.get("pot_id") and not project.get("pot_id").startswith("POT-"):
                project_issues.append(f"Invalid pot_id format: {project.get('pot_id')}")
            
            if project.get("opp_status") != "Won":
                project_issues.append(f"Invalid opp_status: {project.get('opp_status')}")
            
            if len(project_issues) == 0:
                valid_projects += 1
            else:
                schema_issues.extend(project_issues)
        
        if len(schema_issues) == 0:
            self.log_test(
                "Schema Verification", 
                True, 
                f"All {len(self.upcoming_projects_after)} projects have valid schema"
            )
            return True
        else:
            self.log_test(
                "Schema Verification", 
                False, 
                f"Found {len(schema_issues)} schema issues in {len(self.upcoming_projects_after) - valid_projects} projects"
            )
            return False
    
    def test_no_duplicate_projects(self):
        """Verify no duplicate projects are created"""
        print("\n🚫 TESTING NO DUPLICATE PROJECTS")
        print("=" * 50)
        
        if not self.upcoming_projects_after:
            self.log_test("No Duplicate Projects", False, "No upcoming projects data available")
            return False
        
        # Check for duplicates by opp_id
        opp_ids = []
        duplicates = []
        
        for project in self.upcoming_projects_after:
            opp_id = project.get("opp_id")
            if opp_id:
                if opp_id in opp_ids:
                    duplicates.append(opp_id)
                else:
                    opp_ids.append(opp_id)
        
        if len(duplicates) == 0:
            self.log_test(
                "No Duplicate Projects", 
                True, 
                f"No duplicate projects found among {len(self.upcoming_projects_after)} projects"
            )
            return True
        else:
            self.log_test(
                "No Duplicate Projects", 
                False, 
                f"Found {len(duplicates)} duplicate opp_ids: {duplicates[:3]}..."
            )
            return False
    
    def run_all_tests(self):
        """Run all tests for the FIXED L6→SD integration"""
        print("🚀 STARTING FIXED L6→SD INTEGRATION TESTING")
        print("=" * 60)
        print("Testing the FIXED L6→SD integration to verify Won opportunities now appear")
        print("Focus: Resolve user's reported issue of L6 Won opportunities not appearing")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Step 1: Find L6 Won opportunities
        if not self.find_l6_won_opportunities():
            print("\n⚠️ NO L6 WON OPPORTUNITIES FOUND - Cannot test integration")
            self.print_summary()
            return False
        
        # Step 2: Get baseline upcoming projects
        if not self.get_upcoming_projects_baseline():
            print("\n❌ FAILED TO GET BASELINE DATA - Cannot proceed")
            return False
        
        # Step 3: Test manual trigger with fixed integration
        self.test_manual_trigger_with_fixed_integration()
        
        # Step 4: Verify upcoming projects visibility (CRITICAL TEST)
        self.verify_upcoming_projects_visibility()
        
        # Step 5: Test opp_id format fix
        self.test_opp_id_format_fix()
        
        # Step 6: Test integration function fix
        self.test_integration_function_fix()
        
        # Step 7: Test schema verification
        self.test_schema_verification()
        
        # Step 8: Test no duplicate projects
        self.test_no_duplicate_projects()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 FIXED L6→SD INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Summary of key findings
        print(f"\n🔍 KEY FINDINGS:")
        print(f"L6 Won Opportunities Found: {len(self.l6_opportunities)}")
        print(f"Upcoming Projects Before: {len(self.upcoming_projects_before)}")
        print(f"Upcoming Projects After: {len(self.upcoming_projects_after)}")
        print(f"New Projects Created: {len(self.upcoming_projects_after) - len(self.upcoming_projects_before)}")
        
        # Critical issues summary
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for issue in self.critical_issues:
                print(f"   - {issue}")
        
        # Final verdict
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL TESTS PASSED! L6→SD INTEGRATION FIX IS WORKING!")
            print("✅ L6 Won opportunities now appear in upcoming projects list")
            print("✅ Fixed integration resolves the user's reported issue")
            print("✅ Integration function uses correct opportunity_id format")
            print("✅ No duplicate projects created")
        else:
            failed_tests = self.total_tests - self.passed_tests
            print(f"\n⚠️ {failed_tests} TESTS FAILED - INTEGRATION STILL HAS ISSUES")
            
            if any("CRITICAL" in result for result in self.test_results if "❌ FAIL" in result):
                print("❌ CRITICAL: L6→SD integration fix is not working properly")
                print("❌ User's reported issue may still persist")
            else:
                print("⚠️ Minor issues found, but core integration may be working")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = FixedL6SDIntegrationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()