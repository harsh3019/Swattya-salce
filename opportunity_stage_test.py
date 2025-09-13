#!/usr/bin/env python3
"""
Opportunity Stage Management Testing
Testing specific issues with opportunity stage display and management
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class OpportunityStageTestRunner:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.opportunities_data = []
        
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
                self.log_test(
                    "Admin Authentication", 
                    True, 
                    f"User: {user_info.get('username')}, Role ID: {user_info.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_opportunities_list_current_stage(self):
        """Test GET /api/opportunities and check current_stage values"""
        print("\n📋 TESTING OPPORTUNITIES LIST - CURRENT STAGE VALUES")
        print("=" * 60)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                self.opportunities_data = opportunities
                
                total_count = len(opportunities)
                self.log_test(
                    "GET /api/opportunities", 
                    True, 
                    f"Retrieved {total_count} opportunities"
                )
                
                # Analyze current_stage values
                stage_analysis = {}
                opportunities_with_stages = []
                
                for opp in opportunities:
                    current_stage = opp.get('current_stage')
                    opp_id = opp.get('opportunity_id') or opp.get('id')
                    
                    if current_stage is not None:
                        if current_stage not in stage_analysis:
                            stage_analysis[current_stage] = 0
                        stage_analysis[current_stage] += 1
                        
                        opportunities_with_stages.append({
                            'id': opp_id,
                            'current_stage': current_stage,
                            'project_title': opp.get('project_title', 'N/A')
                        })
                
                # Log stage distribution
                print(f"\n📊 CURRENT STAGE DISTRIBUTION:")
                for stage, count in sorted(stage_analysis.items()):
                    print(f"   Stage {stage}: {count} opportunities")
                
                # Check for opportunities beyond L1 (stage > 1)
                beyond_l1 = [opp for opp in opportunities_with_stages if opp['current_stage'] > 1]
                
                if beyond_l1:
                    self.log_test(
                        "Opportunities Beyond L1 Stage", 
                        True, 
                        f"Found {len(beyond_l1)} opportunities at L2+ stages"
                    )
                    
                    print(f"\n🎯 OPPORTUNITIES AT L2+ STAGES:")
                    for opp in beyond_l1[:5]:  # Show first 5
                        print(f"   ID: {opp['id']}, Stage: L{opp['current_stage']}, Title: {opp['project_title']}")
                else:
                    self.log_test(
                        "Opportunities Beyond L1 Stage", 
                        False, 
                        "No opportunities found beyond L1 stage - all opportunities stuck at L1"
                    )
                
                return True
                
            else:
                self.log_test(
                    "GET /api/opportunities", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/opportunities", False, f"Error: {str(e)}")
            return False
    
    def test_specific_opportunity_current_stage(self):
        """Test GET /api/opportunities/{id} for specific opportunities"""
        print("\n🔍 TESTING SPECIFIC OPPORTUNITY CURRENT STAGE DATA")
        print("=" * 55)
        
        if not self.opportunities_data:
            self.log_test("Specific Opportunity Test", False, "No opportunities data available")
            return False
        
        # Test first few opportunities
        # Handle both list and dict response formats
        if isinstance(self.opportunities_data, dict):
            opportunities_list = self.opportunities_data.get('opportunities', [])
        elif isinstance(self.opportunities_data, list):
            opportunities_list = self.opportunities_data
        else:
            opportunities_list = []
            
        test_opportunities = opportunities_list[:3]
        
        for opp in test_opportunities:
            opp_id = opp.get('opportunity_id') or opp.get('id')
            if not opp_id:
                continue
                
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{opp_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    opp_detail = response.json()
                    current_stage = opp_detail.get('current_stage')
                    project_title = opp_detail.get('project_title', 'N/A')
                    
                    self.log_test(
                        f"GET /api/opportunities/{opp_id}", 
                        True, 
                        f"Stage: L{current_stage}, Title: {project_title}"
                    )
                    
                    # Check if current_stage matches what we got from list
                    list_stage = opp.get('current_stage')
                    if current_stage == list_stage:
                        self.log_test(
                            f"Stage Consistency Check - {opp_id}", 
                            True, 
                            f"List and detail both show stage {current_stage}"
                        )
                    else:
                        self.log_test(
                            f"Stage Consistency Check - {opp_id}", 
                            False, 
                            f"List shows {list_stage}, detail shows {current_stage}"
                        )
                        
                else:
                    self.log_test(
                        f"GET /api/opportunities/{opp_id}", 
                        False, 
                        f"Status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"GET /api/opportunities/{opp_id}", False, f"Error: {str(e)}")
        
        return True
    
    def test_stage_progression_data(self):
        """Test if opportunities have proper stage progression data"""
        print("\n📈 TESTING STAGE PROGRESSION DATA")
        print("=" * 45)
        
        # Handle both list and dict response formats
        if isinstance(self.opportunities_data, dict):
            opportunities_list = self.opportunities_data.get('opportunities', [])
        elif isinstance(self.opportunities_data, list):
            opportunities_list = self.opportunities_data
        else:
            opportunities_list = []
            
        if not opportunities_list:
            self.log_test("Stage Progression Test", False, "No opportunities data available")
            return False
        
        # Look for opportunities that should have progressed beyond L1
        opportunities_analysis = []
        
        for opp in opportunities_list:
            current_stage = opp.get('current_stage', 1)
            created_at = opp.get('created_at', '')
            opp_id = opp.get('opportunity_id') or opp.get('id')
            
            opportunities_analysis.append({
                'id': opp_id,
                'current_stage': current_stage,
                'created_at': created_at,
                'project_title': opp.get('project_title', 'N/A')
            })
        
        # Sort by creation date (oldest first)
        opportunities_analysis.sort(key=lambda x: x['created_at'])
        
        # Check if older opportunities have progressed
        older_opportunities = opportunities_analysis[:10]  # First 10 (oldest)
        
        progressed_count = sum(1 for opp in older_opportunities if opp['current_stage'] > 1)
        
        if progressed_count > 0:
            self.log_test(
                "Stage Progression Analysis", 
                True, 
                f"{progressed_count}/{len(older_opportunities)} older opportunities have progressed beyond L1"
            )
        else:
            self.log_test(
                "Stage Progression Analysis", 
                False, 
                f"None of the {len(older_opportunities)} older opportunities have progressed beyond L1"
            )
        
        # Show sample of stage distribution
        print(f"\n📋 SAMPLE OPPORTUNITIES STAGE ANALYSIS:")
        for opp in older_opportunities[:5]:
            print(f"   ID: {opp['id']}, Stage: L{opp['current_stage']}, Created: {opp['created_at'][:10]}")
        
        return True
    
    def test_stage_display_format(self):
        """Test if stage display format is correct (L1-L8 format)"""
        print("\n🎨 TESTING STAGE DISPLAY FORMAT")
        print("=" * 40)
        
        # Test master data stages endpoint
        try:
            response = requests.get(
                f"{self.base_url}/mst/stages",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                stages = response.json()
                self.log_test(
                    "GET /api/mst/stages", 
                    True, 
                    f"Retrieved {len(stages)} stages"
                )
                
                # Check stage format
                print(f"\n📋 AVAILABLE STAGES:")
                for stage in stages:
                    stage_code = stage.get('code', 'N/A')
                    stage_name = stage.get('name', 'N/A')
                    stage_order = stage.get('stage_order', 'N/A')
                    print(f"   {stage_code} - {stage_name} (Order: {stage_order})")
                
                # Verify L1-L8 format exists
                expected_stages = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']
                found_stages = [stage.get('code') for stage in stages]
                
                missing_stages = [stage for stage in expected_stages if stage not in found_stages]
                
                if not missing_stages:
                    self.log_test(
                        "Stage Format Validation", 
                        True, 
                        "All L1-L8 stages found in master data"
                    )
                else:
                    self.log_test(
                        "Stage Format Validation", 
                        False, 
                        f"Missing stages: {missing_stages}"
                    )
                
                return True
                
            else:
                self.log_test(
                    "GET /api/mst/stages", 
                    False, 
                    f"Status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/mst/stages", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all opportunity stage management tests"""
        print("🚀 OPPORTUNITY STAGE MANAGEMENT TESTING")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test opportunities list and current_stage values
        self.test_opportunities_list_current_stage()
        
        # Step 3: Test specific opportunity current_stage data
        self.test_specific_opportunity_current_stage()
        
        # Step 4: Test stage progression data
        self.test_stage_progression_data()
        
        # Step 5: Test stage display format
        self.test_stage_display_format()
        
        # Final Results
        print("\n" + "=" * 60)
        print("🏁 FINAL TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
        
        # Summary of findings
        print(f"\n🔍 KEY FINDINGS:")
        if self.opportunities_data:
            total_opps = len(self.opportunities_data)
            beyond_l1 = sum(1 for opp in self.opportunities_data if opp.get('current_stage', 1) > 1)
            
            print(f"  • Total Opportunities: {total_opps}")
            print(f"  • Opportunities Beyond L1: {beyond_l1}")
            print(f"  • Opportunities Stuck at L1: {total_opps - beyond_l1}")
            
            if beyond_l1 == 0:
                print(f"  ⚠️  CRITICAL ISSUE: All opportunities are stuck at L1 stage")
                print(f"  ⚠️  This explains why 'Manage Stages' always opens at L1")
            else:
                print(f"  ✅ Stage progression appears to be working")
        
        return success_rate > 80

if __name__ == "__main__":
    tester = OpportunityStageTestRunner()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)