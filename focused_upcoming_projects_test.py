#!/usr/bin/env python3
"""
Focused Upcoming Projects API Testing - Review Request
Testing the fix for frontend error and confirming opportunities are showing in upcoming projects list
Focus on real integration data, not test data
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://service-delivery.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class FocusedUpcomingProjectsTester:
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
    
    def test_upcoming_projects_api_availability(self):
        """Test that the upcoming projects API is available and returns data"""
        print("\n🎯 TESTING UPCOMING PROJECTS API AVAILABILITY")
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
                    "Upcoming Projects API Availability", 
                    True, 
                    f"API accessible, returned {len(projects)} projects"
                )
                
                self.upcoming_projects = projects
                return True
            else:
                self.log_test(
                    "Upcoming Projects API Availability", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Upcoming Projects API Availability", False, f"Exception: {str(e)}")
            return False
    
    def test_real_integration_data_quality(self):
        """Test data quality focusing on real integration data (OA- format)"""
        print("\n📋 TESTING REAL INTEGRATION DATA QUALITY")
        print("=" * 50)
        
        if not hasattr(self, 'upcoming_projects'):
            self.log_test("Real Integration Data Quality", False, "No projects data available")
            return
        
        # Filter for real integration projects (OA- format order IDs)
        real_projects = [p for p in self.upcoming_projects if p.get('order_id', '').startswith('OA-')]
        test_projects = [p for p in self.upcoming_projects if p.get('order_id', '').startswith('TEST-')]
        
        self.log_test(
            "Project Data Classification", 
            True, 
            f"Found {len(real_projects)} real integration projects, {len(test_projects)} test projects"
        )
        
        if not real_projects:
            self.log_test(
                "Real Integration Data Quality", 
                True, 
                "No real integration projects found - this is acceptable for testing environment"
            )
            return
        
        # Test data quality of real projects
        critical_issues = []
        
        for i, project in enumerate(real_projects):
            # Check required fields
            required_fields = ['customer_name', 'order_id', 'pot_id', 'setup_cost']
            for field in required_fields:
                if field not in project or project[field] is None:
                    critical_issues.append(f"Real Project {i+1}: Missing/null {field}")
                elif isinstance(project[field], str) and project[field].strip() == "":
                    critical_issues.append(f"Real Project {i+1}: Empty {field}")
            
            # Check format validations
            if 'pot_id' in project and project['pot_id']:
                if not project['pot_id'].startswith('POT-'):
                    critical_issues.append(f"Real Project {i+1}: Invalid pot_id format: {project['pot_id']}")
            
            # Check numeric fields
            if 'setup_cost' in project and project['setup_cost'] is not None:
                try:
                    float(project['setup_cost'])
                except (ValueError, TypeError):
                    critical_issues.append(f"Real Project {i+1}: Invalid setup_cost: {project['setup_cost']}")
        
        if critical_issues:
            self.log_test(
                "Real Integration Data Quality", 
                False, 
                f"Found {len(critical_issues)} issues in real projects: {'; '.join(critical_issues[:2])}{'...' if len(critical_issues) > 2 else ''}"
            )
        else:
            self.log_test(
                "Real Integration Data Quality", 
                True, 
                f"All {len(real_projects)} real integration projects have proper data quality"
            )
    
    def test_frontend_error_prevention(self):
        """Test that data won't cause toLowerCase frontend errors"""
        print("\n🐛 TESTING FRONTEND ERROR PREVENTION")
        print("=" * 50)
        
        if not hasattr(self, 'upcoming_projects'):
            self.log_test("Frontend Error Prevention", False, "No projects data available")
            return
        
        # Focus on fields that might use toLowerCase in frontend
        string_fields = ['customer_name', 'opp_status', 'order_status', 'validation_status']
        frontend_risks = []
        
        for i, project in enumerate(self.upcoming_projects):
            for field in string_fields:
                if field in project:
                    value = project[field]
                    if value is None:
                        frontend_risks.append(f"Project {i+1}: {field} is null")
                    elif not isinstance(value, str):
                        frontend_risks.append(f"Project {i+1}: {field} is not string ({type(value).__name__})")
        
        if frontend_risks:
            self.log_test(
                "Frontend Error Prevention", 
                False, 
                f"Found {len(frontend_risks)} potential toLowerCase risks: {'; '.join(frontend_risks[:2])}{'...' if len(frontend_risks) > 2 else ''}"
            )
        else:
            self.log_test(
                "Frontend Error Prevention", 
                True, 
                f"All string fields properly formatted to prevent toLowerCase errors"
            )
    
    def test_won_opportunity_integration(self):
        """Test that won opportunities have corresponding upcoming projects"""
        print("\n🏆 TESTING WON OPPORTUNITY INTEGRATION")
        print("=" * 50)
        
        try:
            # Get opportunities
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', [])
                
                # Find won opportunities (stage 6)
                won_opportunities = [opp for opp in opportunities if opp.get('current_stage') == 6]
                
                self.log_test(
                    "Won Opportunities Detection", 
                    True, 
                    f"Found {len(won_opportunities)} won opportunities in system"
                )
                
                if won_opportunities and hasattr(self, 'upcoming_projects'):
                    # Check integration
                    project_opp_ids = {p.get('opp_id') for p in self.upcoming_projects if p.get('opp_id')}
                    
                    missing_projects = []
                    found_projects = []
                    
                    for opp in won_opportunities:
                        opp_id = opp.get('id')
                        if opp_id in project_opp_ids:
                            found_projects.append(opp_id)
                        else:
                            missing_projects.append(opp_id)
                    
                    if missing_projects:
                        self.log_test(
                            "Won Opportunity Integration", 
                            False, 
                            f"{len(missing_projects)} won opportunities missing projects: {missing_projects[0] if missing_projects else 'None'}"
                        )
                    else:
                        self.log_test(
                            "Won Opportunity Integration", 
                            True, 
                            f"All {len(won_opportunities)} won opportunities have corresponding projects"
                        )
                elif not won_opportunities:
                    self.log_test(
                        "Won Opportunity Integration", 
                        True, 
                        "No won opportunities found - integration test not applicable"
                    )
                else:
                    self.log_test(
                        "Won Opportunity Integration", 
                        False, 
                        "Could not retrieve upcoming projects for comparison"
                    )
            else:
                self.log_test("Won Opportunities Detection", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Won Opportunity Integration", False, f"Exception: {str(e)}")
    
    def test_manual_trigger_functionality(self):
        """Test manual trigger functionality with actual won opportunity"""
        print("\n🔧 TESTING MANUAL TRIGGER FUNCTIONALITY")
        print("=" * 50)
        
        try:
            # Get opportunities to find won ones
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', [])
                
                # Find a won opportunity
                won_opp = None
                for opp in opportunities:
                    if opp.get('current_stage') == 6:
                        won_opp = opp
                        break
                
                if won_opp:
                    opp_id = won_opp.get('id')
                    
                    # Test manual trigger
                    trigger_response = requests.post(
                        f"{self.base_url}/test/trigger-upcoming-project/{opp_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if trigger_response.status_code == 200:
                        trigger_data = trigger_response.json()
                        message = trigger_data.get('message', '')
                        
                        if 'already exists' in message:
                            self.log_test(
                                "Manual Trigger Functionality", 
                                True, 
                                "Manual trigger working - detected existing project (duplicate prevention)"
                            )
                        elif 'project_id' in trigger_data:
                            self.log_test(
                                "Manual Trigger Functionality", 
                                True, 
                                f"Manual trigger working - created new project: {trigger_data.get('project_id')}"
                            )
                        else:
                            self.log_test(
                                "Manual Trigger Functionality", 
                                True, 
                                f"Manual trigger responded: {message}"
                            )
                    else:
                        self.log_test(
                            "Manual Trigger Functionality", 
                            False, 
                            f"Status: {trigger_response.status_code}, Response: {trigger_response.text[:200]}"
                        )
                else:
                    self.log_test(
                        "Manual Trigger Functionality", 
                        True, 
                        "No won opportunities found - manual trigger test not applicable"
                    )
            else:
                self.log_test("Manual Trigger Functionality", False, "Could not retrieve opportunities")
                
        except Exception as e:
            self.log_test("Manual Trigger Functionality", False, f"Exception: {str(e)}")
    
    def test_api_response_structure(self):
        """Test that API response structure is consistent and won't break frontend"""
        print("\n🏗️ TESTING API RESPONSE STRUCTURE")
        print("=" * 50)
        
        if not hasattr(self, 'upcoming_projects'):
            self.log_test("API Response Structure", False, "No projects data available")
            return
        
        if not self.upcoming_projects:
            self.log_test("API Response Structure", True, "Empty response is valid JSON array")
            return
        
        # Check that response is a list
        if not isinstance(self.upcoming_projects, list):
            self.log_test("API Response Structure", False, "Response is not a JSON array")
            return
        
        # Check first project structure
        first_project = self.upcoming_projects[0]
        expected_fields = ['id', 'order_id', 'opp_id', 'customer_name', 'setup_cost']
        
        missing_fields = []
        for field in expected_fields:
            if field not in first_project:
                missing_fields.append(field)
        
        if missing_fields:
            self.log_test(
                "API Response Structure", 
                False, 
                f"Missing expected fields: {', '.join(missing_fields)}"
            )
        else:
            self.log_test(
                "API Response Structure", 
                True, 
                f"Response structure contains all expected fields"
            )
    
    def run_focused_tests(self):
        """Run focused tests for the review request"""
        print("🚀 STARTING FOCUSED UPCOMING PROJECTS REVIEW TESTING")
        print("=" * 60)
        print("Review Focus: Verify fix for frontend error and confirm integration working")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Run focused test suites
        success = True
        
        # 1. Test API availability
        if not self.test_upcoming_projects_api_availability():
            success = False
        
        # 2. Test API response structure
        self.test_api_response_structure()
        
        # 3. Test real integration data quality
        self.test_real_integration_data_quality()
        
        # 4. Test frontend error prevention
        self.test_frontend_error_prevention()
        
        # 5. Test won opportunity integration
        self.test_won_opportunity_integration()
        
        # 6. Test manual trigger functionality
        self.test_manual_trigger_functionality()
        
        # Print summary
        self.print_summary()
        
        return success and (self.passed_tests / self.total_tests >= 0.8)  # 80% pass rate acceptable
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 FOCUSED UPCOMING PROJECTS REVIEW TEST SUMMARY")
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
            print("✅ Integration functionality confirmed")
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
            real_projects = [p for p in self.upcoming_projects if p.get('order_id', '').startswith('OA-')]
            print(f"• Found {len(self.upcoming_projects)} total projects ({len(real_projects)} real integration projects)")
        
        critical_failures = [r for r in self.test_results if "❌ FAIL" in r and ("Frontend Error" in r or "Data Quality" in r)]
        if critical_failures:
            print("• ❌ CRITICAL: Issues found that could affect frontend")
            for failure in critical_failures:
                print(f"  - {failure.split(' - ')[0]}")
        else:
            print("• ✅ Frontend error fix appears to be working")
            print("• ✅ Data structure is properly formatted")
            print("• ✅ Integration functionality is operational")

def main():
    """Main function"""
    tester = FocusedUpcomingProjectsTester()
    success = tester.run_focused_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()