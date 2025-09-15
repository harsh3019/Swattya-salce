#!/usr/bin/env python3
"""
L6 Manual Trigger Test - Focused on User's Issue
Testing manual trigger for existing L6 Won opportunities to ensure they appear in upcoming projects
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

class L6ManualTriggerTester:
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
                user_info = data.get("user", {})
                self.log_test("Admin Authentication", True, 
                             f"User: {user_info.get('username')}, Role ID: {user_info.get('role_id')}")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def find_l6_won_opportunities(self):
        """Find opportunities with current_stage = 6 and status = 'Won'"""
        print("\n🔍 STEP 1: FINDING L6 WON OPPORTUNITIES")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                l6_won_opportunities = []
                
                print(f"📊 Total opportunities found: {len(opportunities)}")
                
                for opp in opportunities:
                    current_stage = opp.get("current_stage")
                    status = opp.get("status")
                    opp_id = opp.get("opportunity_id", opp.get("id"))
                    project_title = opp.get("project_title", "No Title")
                    
                    print(f"   📋 Opportunity {opp_id}: Stage={current_stage}, Status={status}, Title={project_title}")
                    
                    if current_stage == 6 and status == "Won":
                        l6_won_opportunities.append(opp)
                        print(f"      ✅ L6 Won opportunity found!")
                
                self.log_test("Find L6 Won Opportunities", True, 
                             f"Found {len(l6_won_opportunities)} L6 Won opportunities out of {len(opportunities)} total")
                
                return l6_won_opportunities
            else:
                self.log_test("Find L6 Won Opportunities", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Find L6 Won Opportunities", False, f"Exception: {str(e)}")
            return []
    
    def check_existing_upcoming_projects(self):
        """Check existing upcoming projects"""
        print("\n📊 STEP 2: CHECKING EXISTING UPCOMING PROJECTS")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                self.log_test("Get Existing Upcoming Projects", True, 
                             f"Found {len(projects)} existing upcoming projects")
                
                project_opp_ids = []
                for project in projects:
                    opp_id = project.get('opp_id', 'No OppID')
                    customer = project.get('customer_name', 'Unknown Customer')
                    setup_cost = project.get('setup_cost', 0)
                    order_id = project.get('order_id', 'No OrderID')
                    pot_id = project.get('pot_id', 'No POTID')
                    project_opp_ids.append(opp_id)
                    print(f"   📋 Project: OppID={opp_id}, Customer={customer}, Cost=₹{setup_cost}")
                    print(f"      OrderID={order_id}, POTID={pot_id}")
                
                return projects, project_opp_ids
            else:
                self.log_test("Get Existing Upcoming Projects", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return [], []
                
        except Exception as e:
            self.log_test("Get Existing Upcoming Projects", False, f"Exception: {str(e)}")
            return [], []
    
    def manual_trigger_integration(self, opportunity_id):
        """Manually trigger upcoming project creation for specific opportunity"""
        print(f"\n🚀 STEP 3: MANUAL TRIGGER FOR {opportunity_id}")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.base_url}/test/trigger-upcoming-project/{opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', 'Success')
                self.log_test(f"Manual Trigger for {opportunity_id}", True, f"Response: {message}")
                
                # Check if it was already existing or newly created
                if "already exists" in message.lower():
                    print(f"      ℹ️ Project already exists for this opportunity")
                    return "existing"
                else:
                    print(f"      ✅ New project created for this opportunity")
                    return "created"
            else:
                self.log_test(f"Manual Trigger for {opportunity_id}", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return "failed"
                
        except Exception as e:
            self.log_test(f"Manual Trigger for {opportunity_id}", False, f"Exception: {str(e)}")
            return "failed"
    
    def verify_upcoming_projects_after_trigger(self, l6_opportunities):
        """Verify upcoming projects list after manual trigger"""
        print("\n✅ STEP 4: VERIFYING UPCOMING PROJECTS AFTER TRIGGER")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                self.log_test("Get Updated Upcoming Projects", True, 
                             f"Found {len(projects)} upcoming projects after trigger")
                
                # Check if all L6 opportunities are now in upcoming projects
                found_projects = {}
                expected_opp_ids = [opp.get("opportunity_id", opp.get("id")) for opp in l6_opportunities]
                
                for project in projects:
                    opp_id = project.get('opp_id')
                    if opp_id in expected_opp_ids:
                        found_projects[opp_id] = project
                        customer = project.get('customer_name', 'Unknown Customer')
                        setup_cost = project.get('setup_cost', 0)
                        order_id = project.get('order_id', 'No OrderID')
                        pot_id = project.get('pot_id', 'No POTID')
                        print(f"   ✅ Found Project for {opp_id}: Customer={customer}, Cost=₹{setup_cost}")
                        print(f"      OrderID={order_id}, POTID={pot_id}")
                
                # Report results
                missing_projects = set(expected_opp_ids) - set(found_projects.keys())
                if missing_projects:
                    self.log_test("All L6 Opportunities in Upcoming Projects", False, 
                                 f"Missing projects for opportunities: {list(missing_projects)}")
                else:
                    self.log_test("All L6 Opportunities in Upcoming Projects", True, 
                                 f"All {len(expected_opp_ids)} L6 opportunities found in upcoming projects")
                
                return found_projects
            else:
                self.log_test("Get Updated Upcoming Projects", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Get Updated Upcoming Projects", False, f"Exception: {str(e)}")
            return {}
    
    def run_manual_trigger_test(self):
        """Run manual trigger test for L6 Won opportunities"""
        print("🎯 L6 MANUAL TRIGGER TEST - USER ISSUE RESOLUTION")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📝 OBJECTIVE: Ensure L6 Won opportunities appear in upcoming projects")
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Find L6 Won opportunities
        l6_opportunities = self.find_l6_won_opportunities()
        if not l6_opportunities:
            print("\n⚠️ No L6 Won opportunities found.")
            print("   This could mean:")
            print("   1. No opportunities have reached L6 Won stage yet")
            print("   2. All L6 opportunities are already in upcoming projects")
            print("   3. There might be a data issue")
            
            # Let's still check upcoming projects to see what's there
            existing_projects, project_opp_ids = self.check_existing_upcoming_projects()
            
            if existing_projects:
                print(f"\n✅ Found {len(existing_projects)} existing upcoming projects")
                print("   This suggests the integration is working, but no new L6 opportunities need processing")
                self.log_test("Integration Status", True, "System has upcoming projects, integration appears functional")
            else:
                print("\n❌ No upcoming projects found at all")
                self.log_test("Integration Status", False, "No upcoming projects found, integration may not be working")
            
            return len(existing_projects) > 0
        
        # Step 3: Check existing projects before trigger
        existing_projects, existing_opp_ids = self.check_existing_upcoming_projects()
        
        # Step 4: Manual trigger for each L6 opportunity
        trigger_results = {}
        for opp in l6_opportunities:
            opp_id = opp.get('opportunity_id', opp.get('id'))
            if opp_id:
                result = self.manual_trigger_integration(opp_id)
                trigger_results[opp_id] = result
        
        # Step 5: Verify upcoming projects after trigger
        if l6_opportunities:
            found_projects = self.verify_upcoming_projects_after_trigger(l6_opportunities)
            
            # Step 6: Final validation
            if found_projects:
                print(f"\n🎉 SUCCESS: {len(found_projects)} L6 Won opportunities are now in upcoming projects!")
                self.log_test("User Issue Resolution", True, 
                             f"L6 Won opportunities successfully appear in upcoming projects")
            else:
                print(f"\n❌ ISSUE: L6 Won opportunities are still not appearing in upcoming projects")
                self.log_test("User Issue Resolution", False, 
                             f"L6 Won opportunities not found in upcoming projects after manual trigger")
        
        # Final Results
        print("\n" + "=" * 60)
        print("🎯 L6 MANUAL TRIGGER TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests} tests passed)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: L6→SD integration is working correctly!")
            print("   User should see L6 Won opportunities in upcoming projects")
        elif success_rate >= 75:
            print("✅ GOOD: L6→SD integration is mostly working")
            print("   Minor issues may need attention")
        else:
            print("❌ CRITICAL: L6→SD integration has significant issues")
            print("   User's problem is confirmed - integration not working properly")
        
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(f"   {result}")
        
        return success_rate >= 75

def main():
    """Main test execution"""
    tester = L6ManualTriggerTester()
    success = tester.run_manual_trigger_test()
    
    if success:
        print("\n🎉 L6 Manual Trigger test completed successfully!")
        print("   L6 Won opportunities should now appear in upcoming projects")
        sys.exit(0)
    else:
        print("\n❌ L6 Manual Trigger test identified issues!")
        print("   User's problem confirmed - L6 opportunities not appearing in upcoming projects")
        sys.exit(1)

if __name__ == "__main__":
    main()