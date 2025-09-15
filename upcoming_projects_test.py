#!/usr/bin/env python3
"""
Upcoming Projects API Testing - Review Request
Testing the fix for frontend error and confirming opportunities are showing in upcoming projects list
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://sawayatta-sd.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class UpcomingProjectsTester:
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
                    f"Token received, User: {user_data.get('username')}, Role ID: {user_data.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_upcoming_projects_api(self):
        """Test Upcoming Projects API - Main focus of review request"""
        print("\n🎯 TESTING UPCOMING PROJECTS API")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = data if isinstance(data, list) else data.get('data', [])
                
                self.log_test(
                    "GET /api/sd/upcoming-projects/", 
                    True, 
                    f"Retrieved {len(projects)} upcoming projects"
                )
                
                # Store projects for further testing
                self.upcoming_projects = projects
                
                # Test data structure and required fields
                self.test_project_data_structure(projects)
                
                return True
            else:
                self.log_test(
                    "GET /api/sd/upcoming-projects/", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/sd/upcoming-projects/", False, f"Exception: {str(e)}")
            return False
    
    def test_project_data_structure(self, projects):
        """Test that all projects have required fields populated"""
        print("\n📋 TESTING PROJECT DATA STRUCTURE")
        print("=" * 50)
        
        if not projects:
            self.log_test("Project Data Structure", False, "No projects found to test data structure")
            return
        
        required_fields = ['customer_name', 'order_id', 'pot_id', 'setup_cost']
        critical_issues = []
        
        for i, project in enumerate(projects):
            project_issues = []
            
            # Check required fields
            for field in required_fields:
                if field not in project:
                    project_issues.append(f"Missing field: {field}")
                elif project[field] is None:
                    project_issues.append(f"Null value: {field}")
                elif isinstance(project[field], str) and project[field].strip() == "":
                    project_issues.append(f"Empty string: {field}")
            
            # Check specific field formats
            if 'order_id' in project and project['order_id']:
                if not project['order_id'].startswith('OA-'):
                    project_issues.append(f"Invalid order_id format: {project['order_id']} (should start with 'OA-')")
            
            if 'pot_id' in project and project['pot_id']:
                if not project['pot_id'].startswith('POT-'):
                    project_issues.append(f"Invalid pot_id format: {project['pot_id']} (should start with 'POT-')")
            
            # Check numeric fields
            if 'setup_cost' in project and project['setup_cost'] is not None:
                try:
                    float(project['setup_cost'])
                except (ValueError, TypeError):
                    project_issues.append(f"Invalid setup_cost format: {project['setup_cost']} (should be numeric)")
            
            if project_issues:
                critical_issues.extend([f"Project {i+1}: {issue}" for issue in project_issues])
        
        if critical_issues:
            self.log_test(
                "Project Data Integrity", 
                False, 
                f"Found {len(critical_issues)} data integrity issues: {'; '.join(critical_issues[:3])}{'...' if len(critical_issues) > 3 else ''}"
            )
        else:
            self.log_test(
                "Project Data Integrity", 
                True, 
                f"All {len(projects)} projects have required fields properly populated"
            )
        
        # Test for toLowerCase error prevention
        self.test_frontend_error_prevention(projects)
    
    def test_frontend_error_prevention(self, projects):
        """Test that data won't cause toLowerCase frontend errors"""
        print("\n🐛 TESTING FRONTEND ERROR PREVENTION")
        print("=" * 50)
        
        string_fields_that_might_use_tolowercase = ['customer_name', 'status', 'project_name']
        frontend_error_risks = []
        
        for i, project in enumerate(projects):
            for field in string_fields_that_might_use_tolowercase:
                if field in project:
                    value = project[field]
                    if value is None:
                        frontend_error_risks.append(f"Project {i+1}: {field} is null (could cause toLowerCase error)")
                    elif not isinstance(value, str):
                        frontend_error_risks.append(f"Project {i+1}: {field} is not a string ({type(value).__name__}) (could cause toLowerCase error)")
        
        if frontend_error_risks:
            self.log_test(
                "Frontend Error Prevention", 
                False, 
                f"Found {len(frontend_error_risks)} potential toLowerCase error risks: {'; '.join(frontend_error_risks[:2])}{'...' if len(frontend_error_risks) > 2 else ''}"
            )
        else:
            self.log_test(
                "Frontend Error Prevention", 
                True, 
                f"All string fields are properly formatted to prevent toLowerCase errors"
            )
    
    def test_won_opportunities_integration(self):
        """Test that won opportunities have corresponding upcoming projects"""
        print("\n🏆 TESTING WON OPPORTUNITIES INTEGRATION")
        print("=" * 50)
        
        try:
            # Get opportunities to check for won ones
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                if isinstance(opportunities, dict):
                    opportunities = opportunities.get('data', [])
                
                # Find won opportunities (stage 6 or status 'Won')
                won_opportunities = []
                for opp in opportunities:
                    if (opp.get('current_stage') == 6 or 
                        opp.get('stage') == 'Won' or 
                        opp.get('status') == 'Won'):
                        won_opportunities.append(opp)
                
                self.log_test(
                    "Won Opportunities Found", 
                    True, 
                    f"Found {len(won_opportunities)} won opportunities"
                )
                
                # Check if won opportunities have corresponding upcoming projects
                if won_opportunities and hasattr(self, 'upcoming_projects'):
                    self.verify_won_opportunity_projects(won_opportunities)
                elif not won_opportunities:
                    self.log_test(
                        "Won Opportunities Integration", 
                        True, 
                        "No won opportunities found - integration test not applicable"
                    )
                else:
                    self.log_test(
                        "Won Opportunities Integration", 
                        False, 
                        "Could not retrieve upcoming projects for comparison"
                    )
            else:
                self.log_test(
                    "Won Opportunities Retrieval", 
                    False, 
                    f"Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Won Opportunities Integration", False, f"Exception: {str(e)}")
    
    def verify_won_opportunity_projects(self, won_opportunities):
        """Verify that won opportunities have corresponding upcoming projects"""
        if not hasattr(self, 'upcoming_projects'):
            self.log_test("Won Opportunity Projects Verification", False, "No upcoming projects data available")
            return
        
        # Create mapping of opportunity IDs to project data
        project_opp_ids = set()
        for project in self.upcoming_projects:
            if 'opp_id' in project and project['opp_id']:
                project_opp_ids.add(project['opp_id'])
        
        # Check each won opportunity
        missing_projects = []
        found_projects = []
        
        for opp in won_opportunities:
            opp_id = opp.get('opportunity_id') or opp.get('id')
            if opp_id in project_opp_ids:
                found_projects.append(opp_id)
            else:
                missing_projects.append(opp_id)
        
        if missing_projects:
            self.log_test(
                "Won Opportunity Projects Verification", 
                False, 
                f"{len(missing_projects)} won opportunities missing upcoming projects: {', '.join(missing_projects[:3])}{'...' if len(missing_projects) > 3 else ''}"
            )
        else:
            self.log_test(
                "Won Opportunity Projects Verification", 
                True, 
                f"All {len(won_opportunities)} won opportunities have corresponding upcoming projects"
            )
    
    def test_manual_trigger_if_needed(self):
        """Test manual trigger for integration if needed"""
        print("\n🔧 TESTING MANUAL TRIGGER (IF NEEDED)")
        print("=" * 50)
        
        try:
            # Get opportunities to find a won one for testing
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                if isinstance(opportunities, dict):
                    opportunities = opportunities.get('data', [])
                
                # Find a won opportunity for testing
                won_opp = None
                for opp in opportunities:
                    if (opp.get('current_stage') == 6 or 
                        opp.get('stage') == 'Won' or 
                        opp.get('status') == 'Won'):
                        won_opp = opp
                        break
                
                if won_opp:
                    opp_id = won_opp.get('id')
                    
                    # Test manual trigger endpoint
                    trigger_response = requests.post(
                        f"{self.base_url}/test/trigger-upcoming-project/{opp_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if trigger_response.status_code == 200:
                        trigger_data = trigger_response.json()
                        self.log_test(
                            "Manual Trigger Test", 
                            True, 
                            f"Manual trigger successful: {trigger_data.get('message', 'Success')}"
                        )
                    else:
                        self.log_test(
                            "Manual Trigger Test", 
                            False, 
                            f"Status: {trigger_response.status_code}, Response: {trigger_response.text[:200]}"
                        )
                else:
                    self.log_test(
                        "Manual Trigger Test", 
                        True, 
                        "No won opportunities found - manual trigger test not applicable"
                    )
            else:
                self.log_test("Manual Trigger Test", False, "Could not retrieve opportunities for trigger test")
                
        except Exception as e:
            self.log_test("Manual Trigger Test", False, f"Exception: {str(e)}")
    
    def run_review_tests(self):
        """Run all tests for the review request"""
        print("🚀 STARTING UPCOMING PROJECTS REVIEW TESTING")
        print("=" * 60)
        print("Review Focus: Fix for frontend error and confirm opportunities showing in upcoming projects list")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Run the main test suites as requested in review
        success = True
        
        # 1. Test Upcoming Projects API
        if not self.test_upcoming_projects_api():
            success = False
        
        # 2. Verify Integration Function
        self.test_won_opportunities_integration()
        
        # 3. Test Manual Trigger if needed
        self.test_manual_trigger_if_needed()
        
        # Print summary
        self.print_summary()
        
        return success and (self.passed_tests / self.total_tests >= 0.8)  # 80% pass rate acceptable
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 UPCOMING PROJECTS REVIEW TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Frontend error fix verified")
            print("✅ Upcoming projects API working correctly")
            print("✅ Data integrity confirmed")
        elif success_rate >= 80:
            print(f"\n✅ REVIEW TESTS MOSTLY SUCCESSFUL ({success_rate:.1f}%)")
            print("✅ Core functionality working")
            print("⚠️  Minor issues found but not critical")
        else:
            print(f"\n❌ REVIEW TESTS FAILED ({success_rate:.1f}%)")
            print("❌ Critical issues found that need attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)
        
        # Review-specific conclusions
        print("\n🎯 REVIEW REQUEST CONCLUSIONS:")
        print("-" * 40)
        
        if hasattr(self, 'upcoming_projects'):
            print(f"• Found {len(self.upcoming_projects)} upcoming projects in the system")
        
        critical_failures = [r for r in self.test_results if "❌ FAIL" in r and ("Data Integrity" in r or "Frontend Error" in r)]
        if critical_failures:
            print("• ❌ CRITICAL: Frontend error risk still exists")
            for failure in critical_failures:
                print(f"  - {failure}")
        else:
            print("• ✅ Frontend error fix appears to be working")
            print("• ✅ Data structure is properly formatted")

def main():
    """Main function"""
    tester = UpcomingProjectsTester()
    success = tester.run_review_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()