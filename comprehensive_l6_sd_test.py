#!/usr/bin/env python3
"""
Comprehensive L6→SD Integration Test - Final Verification
Testing L6 Won opportunities and their corresponding upcoming projects with proper ID mapping
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

class ComprehensiveL6SDTester:
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
    
    def get_l6_won_opportunities_with_mapping(self):
        """Get L6 Won opportunities with proper ID mapping"""
        print("\n🔍 STEP 1: ANALYZING L6 WON OPPORTUNITIES WITH ID MAPPING")
        print("=" * 60)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                opportunities = response_data.get("opportunities", []) if isinstance(response_data, dict) else response_data
                l6_won_opportunities = []
                
                print(f"📊 Total opportunities found: {len(opportunities)}")
                
                for opp in opportunities:
                    current_stage = opp.get("current_stage")
                    status = opp.get("status")
                    
                    if current_stage == 6 and status == "Won":
                        uuid_id = opp.get("id")
                        opp_id = opp.get("opportunity_id")
                        project_title = opp.get("project_title", "No Title")
                        
                        l6_won_opportunities.append({
                            "uuid_id": uuid_id,
                            "opportunity_id": opp_id,
                            "project_title": project_title,
                            "expected_revenue": opp.get("expected_revenue", 0),
                            "company_id": opp.get("company_id"),
                            "full_data": opp
                        })
                        
                        print(f"   📋 L6 Won Opportunity:")
                        print(f"      UUID ID: {uuid_id}")
                        print(f"      Opportunity ID: {opp_id}")
                        print(f"      Title: {project_title}")
                        print(f"      Expected Revenue: ₹{opp.get('expected_revenue', 0)}")
                
                self.log_test("Find L6 Won Opportunities with Mapping", True, 
                             f"Found {len(l6_won_opportunities)} L6 Won opportunities")
                
                return l6_won_opportunities
            else:
                self.log_test("Find L6 Won Opportunities with Mapping", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Find L6 Won Opportunities with Mapping", False, f"Exception: {str(e)}")
            return []
    
    def get_upcoming_projects_with_mapping(self):
        """Get upcoming projects with proper mapping"""
        print("\n📊 STEP 2: ANALYZING UPCOMING PROJECTS")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/sd/upcoming-projects/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                self.log_test("Get Upcoming Projects", True, 
                             f"Found {len(projects)} upcoming projects")
                
                project_mapping = {}
                for project in projects:
                    opp_id = project.get('opp_id')
                    if opp_id and opp_id != 'No OppID':
                        project_mapping[opp_id] = project
                        customer = project.get('customer_name', 'Unknown Customer')
                        setup_cost = project.get('setup_cost', 0)
                        order_id = project.get('order_id', 'No OrderID')
                        pot_id = project.get('pot_id', 'No POTID')
                        print(f"   📋 Project: OppID={opp_id}")
                        print(f"      Customer: {customer}")
                        print(f"      Setup Cost: ₹{setup_cost}")
                        print(f"      Order ID: {order_id}")
                        print(f"      POT ID: {pot_id}")
                
                return project_mapping
            else:
                self.log_test("Get Upcoming Projects", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Get Upcoming Projects", False, f"Exception: {str(e)}")
            return {}
    
    def verify_l6_sd_integration(self, l6_opportunities, project_mapping):
        """Verify L6→SD integration by matching opportunities to projects"""
        print("\n✅ STEP 3: VERIFYING L6→SD INTEGRATION")
        print("=" * 50)
        
        matched_projects = []
        missing_projects = []
        
        for opp in l6_opportunities:
            opp_id = opp["opportunity_id"]
            uuid_id = opp["uuid_id"]
            title = opp["project_title"]
            
            if opp_id in project_mapping:
                project = project_mapping[opp_id]
                matched_projects.append({
                    "opportunity": opp,
                    "project": project
                })
                print(f"   ✅ MATCH FOUND:")
                print(f"      Opportunity: {title} ({opp_id})")
                print(f"      Project: {project.get('order_id')} - {project.get('customer_name')}")
                print(f"      Revenue Match: ₹{opp['expected_revenue']} → ₹{project.get('setup_cost', 0)}")
            else:
                missing_projects.append(opp)
                print(f"   ❌ MISSING PROJECT:")
                print(f"      Opportunity: {title} ({opp_id})")
                print(f"      UUID: {uuid_id}")
        
        # Test results
        if len(matched_projects) == len(l6_opportunities):
            self.log_test("All L6 Opportunities Have Projects", True, 
                         f"All {len(l6_opportunities)} L6 opportunities have corresponding projects")
        else:
            self.log_test("All L6 Opportunities Have Projects", False, 
                         f"{len(missing_projects)} out of {len(l6_opportunities)} L6 opportunities missing projects")
        
        if len(matched_projects) > 0:
            self.log_test("L6→SD Integration Working", True, 
                         f"{len(matched_projects)} L6 opportunities successfully integrated")
        else:
            self.log_test("L6→SD Integration Working", False, 
                         "No L6 opportunities found in upcoming projects")
        
        return matched_projects, missing_projects
    
    def test_manual_trigger_for_missing(self, missing_projects):
        """Test manual trigger for missing projects"""
        if not missing_projects:
            print("\n🎉 NO MISSING PROJECTS - MANUAL TRIGGER NOT NEEDED")
            self.log_test("Manual Trigger Required", False, "All projects already exist")
            return True
        
        print(f"\n🚀 STEP 4: TESTING MANUAL TRIGGER FOR {len(missing_projects)} MISSING PROJECTS")
        print("=" * 60)
        
        success_count = 0
        for opp in missing_projects:
            uuid_id = opp["uuid_id"]
            opp_id = opp["opportunity_id"]
            title = opp["project_title"]
            
            print(f"\n   🚀 Triggering for: {title}")
            print(f"      UUID: {uuid_id}")
            print(f"      Opportunity ID: {opp_id}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/test/trigger-upcoming-project/{uuid_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get('message', 'Success')
                    print(f"      ✅ Success: {message}")
                    success_count += 1
                else:
                    print(f"      ❌ Failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"      ❌ Exception: {str(e)}")
        
        if success_count == len(missing_projects):
            self.log_test("Manual Trigger for Missing Projects", True, 
                         f"Successfully triggered {success_count} missing projects")
            return True
        else:
            self.log_test("Manual Trigger for Missing Projects", False, 
                         f"Only {success_count}/{len(missing_projects)} triggers successful")
            return False
    
    def final_verification(self, l6_opportunities):
        """Final verification after manual triggers"""
        print("\n🔍 STEP 5: FINAL VERIFICATION AFTER MANUAL TRIGGERS")
        print("=" * 60)
        
        # Re-get upcoming projects
        updated_project_mapping = self.get_upcoming_projects_with_mapping()
        
        # Re-verify integration
        final_matched, final_missing = self.verify_l6_sd_integration(l6_opportunities, updated_project_mapping)
        
        if len(final_missing) == 0:
            self.log_test("Final Integration Verification", True, 
                         f"All {len(l6_opportunities)} L6 opportunities now have projects")
            return True
        else:
            self.log_test("Final Integration Verification", False, 
                         f"{len(final_missing)} L6 opportunities still missing projects")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive L6→SD integration test"""
        print("🎯 COMPREHENSIVE L6→SD INTEGRATION TEST")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📝 OBJECTIVE: Verify L6 Won opportunities appear in upcoming projects")
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Get L6 Won opportunities with proper mapping
        l6_opportunities = self.get_l6_won_opportunities_with_mapping()
        if not l6_opportunities:
            print("\n⚠️ No L6 Won opportunities found.")
            self.log_test("L6 Opportunities Available", False, "No L6 Won opportunities found")
            return False
        
        # Step 3: Get upcoming projects
        project_mapping = self.get_upcoming_projects_with_mapping()
        
        # Step 4: Verify integration
        matched_projects, missing_projects = self.verify_l6_sd_integration(l6_opportunities, project_mapping)
        
        # Step 5: Test manual trigger for missing projects
        if missing_projects:
            trigger_success = self.test_manual_trigger_for_missing(missing_projects)
            
            # Step 6: Final verification
            if trigger_success:
                self.final_verification(l6_opportunities)
        
        # Final Results
        print("\n" + "=" * 70)
        print("🎯 COMPREHENSIVE L6→SD INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests} tests passed)")
        
        # Summary
        print(f"\n📋 INTEGRATION SUMMARY:")
        print(f"   🔍 L6 Won Opportunities Found: {len(l6_opportunities)}")
        print(f"   📊 Upcoming Projects Found: {len(project_mapping)}")
        print(f"   ✅ Successfully Matched: {len(matched_projects)}")
        print(f"   ❌ Missing Projects: {len(missing_projects) if missing_projects else 0}")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT: L6→SD integration is working correctly!")
            print("   ✅ User should see L6 Won opportunities in upcoming projects")
            integration_status = "WORKING"
        elif success_rate >= 75:
            print("\n✅ GOOD: L6→SD integration is mostly working")
            print("   ⚠️ Minor issues may need attention")
            integration_status = "MOSTLY_WORKING"
        else:
            print("\n❌ CRITICAL: L6→SD integration has significant issues")
            print("   🚨 User's problem confirmed - integration not working properly")
            integration_status = "BROKEN"
        
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(f"   {result}")
        
        return integration_status == "WORKING"

def main():
    """Main test execution"""
    tester = ComprehensiveL6SDTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 Comprehensive L6→SD Integration test completed successfully!")
        print("   ✅ L6 Won opportunities are properly appearing in upcoming projects")
        sys.exit(0)
    else:
        print("\n❌ Comprehensive L6→SD Integration test identified issues!")
        print("   🚨 User's problem confirmed - L6 opportunities not properly integrated")
        sys.exit(1)

if __name__ == "__main__":
    main()