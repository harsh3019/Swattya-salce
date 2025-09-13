#!/usr/bin/env python3
"""
Opportunity Data Access Investigation Test
Testing specific opportunity data access issues found by frontend testing agent
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

# Specific opportunity IDs to test
SPECIFIC_OPPORTUNITY_IDS = ["POT-RA6G5J6I", "OPP-IGDMLHW", "OPP-712984"]

class OpportunityDataAccessTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            self.failed_tests.append({"test": test_name, "details": details})
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results.append(result)
        print(result)
        
    def authenticate(self):
        """Test admin authentication first"""
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
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
                    f"✅ SUCCESS - User: {user_data.get('username')}, Role ID: {user_data.get('role_id')}, Email: {user_data.get('email')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"❌ FAILED - Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"❌ EXCEPTION - {str(e)}")
            return False
    
    def test_permissions_api(self):
        """Test GET /api/auth/permissions endpoint for 403 Forbidden errors"""
        print("\n🔒 TESTING PERMISSIONS API")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/permissions",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                permissions = data.get('permissions', [])
                
                # Check for opportunity-related permissions
                opp_permissions = [p for p in permissions if 'opportunities' in p.get('path', '').lower() or 'opportunity' in p.get('menu', '').lower()]
                
                self.log_test(
                    "GET /api/auth/permissions", 
                    True, 
                    f"✅ SUCCESS - Retrieved {len(permissions)} total permissions, {len(opp_permissions)} opportunity-related"
                )
                
                # Log some opportunity permissions for verification
                if opp_permissions:
                    print("   📋 Opportunity Permissions Found:")
                    for perm in opp_permissions[:5]:  # Show first 5
                        print(f"      - {perm.get('module')}/{perm.get('menu')}: {perm.get('permission')}")
                
                return True
            elif response.status_code == 403:
                self.log_test("GET /api/auth/permissions", False, "❌ 403 FORBIDDEN ERROR - Admin user lacks permission access")
                return False
            else:
                self.log_test("GET /api/auth/permissions", False, f"❌ FAILED - Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/auth/permissions", False, f"❌ EXCEPTION - {str(e)}")
            return False
    
    def test_opportunities_list(self):
        """Test GET /api/opportunities endpoint to verify opportunities exist"""
        print("\n🎯 TESTING OPPORTUNITIES LIST API")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and object responses
                opportunities = data if isinstance(data, list) else data.get('data', [])
                count = len(opportunities)
                
                if count > 0:
                    self.log_test(
                        "GET /api/opportunities", 
                        True, 
                        f"✅ SUCCESS - Found {count} opportunities in database"
                    )
                    
                    # Log opportunity IDs and formats
                    print("   📋 Opportunity IDs Found:")
                    opp_formats = {"POT-": 0, "OPP-": 0, "Other": 0}
                    
                    for i, opp in enumerate(opportunities[:10]):  # Show first 10
                        opp_id = opp.get('opportunity_id') or opp.get('id', 'Unknown')
                        project_title = opp.get('project_title') or opp.get('name', 'Unknown')
                        stage = opp.get('current_stage', opp.get('stage', 'Unknown'))
                        
                        print(f"      {i+1}. ID: {opp_id}, Title: {project_title[:30]}..., Stage: {stage}")
                        
                        # Count ID formats
                        if str(opp_id).startswith('POT-'):
                            opp_formats["POT-"] += 1
                        elif str(opp_id).startswith('OPP-'):
                            opp_formats["OPP-"] += 1
                        else:
                            opp_formats["Other"] += 1
                    
                    print(f"   📊 ID Format Distribution: POT-: {opp_formats['POT-']}, OPP-: {opp_formats['OPP-']}, Other: {opp_formats['Other']}")
                    
                    # Store opportunities for later tests
                    self.opportunities = opportunities
                    return True
                else:
                    self.log_test("GET /api/opportunities", False, "❌ NO OPPORTUNITIES FOUND - Database appears empty")
                    self.opportunities = []
                    return False
            else:
                self.log_test("GET /api/opportunities", False, f"❌ FAILED - Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/opportunities", False, f"❌ EXCEPTION - {str(e)}")
            return False
    
    def test_specific_opportunity_ids(self):
        """Test specific opportunity IDs: POT-RA6G5J6I, OPP-IGDMLHW, OPP-712984"""
        print("\n🔍 TESTING SPECIFIC OPPORTUNITY IDs")
        print("=" * 50)
        
        for opp_id in SPECIFIC_OPPORTUNITY_IDS:
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{opp_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    project_title = data.get('project_title') or data.get('name', 'Unknown')
                    stage = data.get('current_stage', data.get('stage', 'Unknown'))
                    company_name = data.get('company_name', 'Unknown')
                    
                    self.log_test(
                        f"GET /api/opportunities/{opp_id}", 
                        True, 
                        f"✅ ACCESSIBLE - Title: {project_title}, Stage: {stage}, Company: {company_name}"
                    )
                elif response.status_code == 404:
                    self.log_test(f"GET /api/opportunities/{opp_id}", False, "❌ 404 NOT FOUND - Opportunity does not exist")
                else:
                    self.log_test(f"GET /api/opportunities/{opp_id}", False, f"❌ FAILED - Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"GET /api/opportunities/{opp_id}", False, f"❌ EXCEPTION - {str(e)}")
    
    def test_opportunity_crud_operations(self):
        """Test opportunity CRUD operations"""
        print("\n🔧 TESTING OPPORTUNITY CRUD OPERATIONS")
        print("=" * 50)
        
        # Test creating a new opportunity if needed
        created_opp_id = self.test_create_opportunity()
        
        if created_opp_id:
            # Test reading the created opportunity
            self.test_read_opportunity(created_opp_id)
            
            # Test updating the opportunity
            self.test_update_opportunity(created_opp_id)
    
    def test_create_opportunity(self):
        """Test POST /api/opportunities (create new opportunity)"""
        try:
            # Get required master data first
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                self.log_test("POST /api/opportunities (Setup)", False, "❌ Could not get required master data")
                return None
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            # Find L1 stage and INR currency
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                self.log_test("POST /api/opportunities (Setup)", False, "❌ L1 stage or INR currency not found")
                return None
            
            # Create opportunity data
            opportunity_data = {
                "project_title": "Data Access Test Opportunity",
                "company_id": "test-company-data-access",
                "stage_id": l1_stage['id'],
                "expected_revenue": 250000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-data-access",
                "win_probability": 60
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                opportunity_id = data.get('opportunity_id') or data.get('id')
                
                # Check ID format
                if opportunity_id and (opportunity_id.startswith('OPP-') or opportunity_id.startswith('POT-')):
                    self.log_test(
                        "POST /api/opportunities", 
                        True, 
                        f"✅ SUCCESS - Created opportunity with ID: {opportunity_id}"
                    )
                    return data.get('id')  # Return database ID for further tests
                else:
                    self.log_test("POST /api/opportunities", False, f"❌ Invalid ID format: {opportunity_id}")
                    return None
            else:
                self.log_test("POST /api/opportunities", False, f"❌ FAILED - Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("POST /api/opportunities", False, f"❌ EXCEPTION - {str(e)}")
            return None
    
    def test_read_opportunity(self, opportunity_id):
        """Test reading a specific opportunity"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify data structure and field availability
                required_fields = ['project_title', 'expected_revenue', 'currency_id', 'current_stage']
                missing_fields = [field for field in required_fields if field not in data and field.replace('_', '') not in str(data)]
                
                if len(missing_fields) == 0:
                    self.log_test(
                        f"READ Opportunity Data Structure", 
                        True, 
                        f"✅ All required fields present: {', '.join(required_fields)}"
                    )
                else:
                    self.log_test(
                        f"READ Opportunity Data Structure", 
                        False, 
                        f"❌ Missing fields: {', '.join(missing_fields)}"
                    )
            else:
                self.log_test(f"READ Opportunity {opportunity_id}", False, f"❌ FAILED - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test(f"READ Opportunity {opportunity_id}", False, f"❌ EXCEPTION - {str(e)}")
    
    def test_update_opportunity(self, opportunity_id):
        """Test updating an opportunity"""
        try:
            update_data = {
                "project_title": "Updated Data Access Test Opportunity",
                "expected_revenue": 300000,
                "win_probability": 70
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                json=update_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test(
                    f"UPDATE Opportunity {opportunity_id}", 
                    True, 
                    "✅ SUCCESS - Opportunity updated successfully"
                )
            else:
                self.log_test(f"UPDATE Opportunity {opportunity_id}", False, f"❌ FAILED - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test(f"UPDATE Opportunity {opportunity_id}", False, f"❌ EXCEPTION - {str(e)}")
    
    def test_data_seeding_verification(self):
        """Verify if opportunities are properly seeded in the database"""
        print("\n🌱 TESTING DATA SEEDING VERIFICATION")
        print("=" * 50)
        
        if hasattr(self, 'opportunities') and len(self.opportunities) > 0:
            # Analyze opportunity data quality
            total_opps = len(self.opportunities)
            complete_opps = 0
            stage_distribution = {}
            
            for opp in self.opportunities:
                # Check if opportunity has complete data
                required_fields = ['project_title', 'expected_revenue', 'current_stage']
                has_complete_data = all(opp.get(field) or opp.get(field.replace('_', '')) for field in required_fields)
                
                if has_complete_data:
                    complete_opps += 1
                
                # Track stage distribution
                stage = opp.get('current_stage', opp.get('stage', 'Unknown'))
                stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
            
            completion_rate = (complete_opps / total_opps * 100) if total_opps > 0 else 0
            
            self.log_test(
                "Data Seeding Quality", 
                completion_rate >= 80, 
                f"✅ {complete_opps}/{total_opps} opportunities have complete data ({completion_rate:.1f}%)"
            )
            
            print("   📊 Stage Distribution:")
            for stage, count in stage_distribution.items():
                print(f"      - Stage {stage}: {count} opportunities")
                
        else:
            self.log_test("Data Seeding Quality", False, "❌ No opportunities found to analyze")
    
    def create_sample_opportunities_if_needed(self):
        """Create sample opportunities if database is empty"""
        print("\n🏗️  CREATING SAMPLE OPPORTUNITIES")
        print("=" * 50)
        
        if not hasattr(self, 'opportunities') or len(self.opportunities) == 0:
            print("   📝 Database appears empty, creating sample opportunities...")
            
            # Get required master data
            try:
                stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
                currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
                
                if stages_response.status_code != 200 or currencies_response.status_code != 200:
                    self.log_test("Sample Data Creation", False, "❌ Could not get master data")
                    return
                
                stages = stages_response.json()
                currencies = currencies_response.json()
                
                inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
                if not inr_currency:
                    self.log_test("Sample Data Creation", False, "❌ INR currency not found")
                    return
                
                # Create sample opportunities in different stages
                sample_opportunities = [
                    {
                        "project_title": "Sample CRM Implementation",
                        "company_id": "sample-company-1",
                        "expected_revenue": 500000,
                        "currency_id": inr_currency['id'],
                        "lead_owner_id": "sample-user-1",
                        "win_probability": 75
                    },
                    {
                        "project_title": "Sample ERP System Upgrade",
                        "company_id": "sample-company-2", 
                        "expected_revenue": 750000,
                        "currency_id": inr_currency['id'],
                        "lead_owner_id": "sample-user-2",
                        "win_probability": 60
                    },
                    {
                        "project_title": "Sample Digital Transformation",
                        "company_id": "sample-company-3",
                        "expected_revenue": 1000000,
                        "currency_id": inr_currency['id'],
                        "lead_owner_id": "sample-user-3",
                        "win_probability": 50
                    }
                ]
                
                created_count = 0
                for i, opp_data in enumerate(sample_opportunities):
                    # Use different stages (L1, L2, L3)
                    stage_codes = ['L1', 'L2', 'L3']
                    stage_code = stage_codes[i % len(stage_codes)]
                    stage = next((s for s in stages if s.get('stage_code') == stage_code), stages[0])
                    opp_data['stage_id'] = stage['id']
                    
                    try:
                        response = requests.post(
                            f"{self.base_url}/opportunities",
                            headers=self.headers,
                            json=opp_data,
                            timeout=10
                        )
                        
                        if response.status_code in [200, 201]:
                            created_count += 1
                            data = response.json()
                            opp_id = data.get('opportunity_id', data.get('id'))
                            print(f"      ✅ Created: {opp_id} - {opp_data['project_title']}")
                        else:
                            print(f"      ❌ Failed to create: {opp_data['project_title']} - Status: {response.status_code}")
                            
                    except Exception as e:
                        print(f"      ❌ Exception creating {opp_data['project_title']}: {str(e)}")
                
                self.log_test(
                    "Sample Opportunities Creation", 
                    created_count > 0, 
                    f"✅ Created {created_count}/{len(sample_opportunities)} sample opportunities"
                )
                
            except Exception as e:
                self.log_test("Sample Data Creation", False, f"❌ EXCEPTION - {str(e)}")
        else:
            print("   ✅ Database already contains opportunities, skipping sample creation")
    
    def run_investigation(self):
        """Run the complete opportunity data access investigation"""
        print("🔍 STARTING OPPORTUNITY DATA ACCESS INVESTIGATION")
        print("=" * 60)
        
        # Step 1: Authentication first (required)
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with investigation")
            return False
        
        # Step 2: Test permissions API for 403 errors
        self.test_permissions_api()
        
        # Step 3: Test opportunities list to verify data exists
        opportunities_exist = self.test_opportunities_list()
        
        # Step 4: Test specific opportunity IDs
        self.test_specific_opportunity_ids()
        
        # Step 5: Test opportunity CRUD operations
        self.test_opportunity_crud_operations()
        
        # Step 6: Verify data seeding quality
        self.test_data_seeding_verification()
        
        # Step 7: Create sample opportunities if needed
        if not opportunities_exist:
            self.create_sample_opportunities_if_needed()
        
        # Print investigation summary
        self.print_investigation_summary()
        
        return len(self.failed_tests) == 0
    
    def print_investigation_summary(self):
        """Print investigation summary"""
        print("\n" + "=" * 60)
        print("📊 OPPORTUNITY DATA ACCESS INVESTIGATION SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if len(self.failed_tests) == 0:
            print("\n🎉 ALL INVESTIGATION OBJECTIVES MET!")
            print("✅ Admin authentication working")
            print("✅ Permissions API accessible")
            print("✅ Opportunities data available")
            print("✅ CRUD operations functional")
        else:
            print(f"\n⚠️  {len(self.failed_tests)} ISSUES IDENTIFIED:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"{i}. {failure['test']}: {failure['details']}")
        
        print("\n📋 DETAILED INVESTIGATION RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 20)
        if len(self.failed_tests) == 0:
            print("✅ No critical issues found. System is ready for frontend testing.")
        else:
            if any("404 NOT FOUND" in f['details'] for f in self.failed_tests):
                print("🔧 Fix 404 errors on opportunity detail APIs")
            if any("403 FORBIDDEN" in f['details'] for f in self.failed_tests):
                print("🔧 Fix permission API 403 Forbidden errors")
            if any("NO OPPORTUNITIES FOUND" in f['details'] for f in self.failed_tests):
                print("🔧 Ensure opportunity data is properly seeded")
            if any("Invalid ID format" in f['details'] for f in self.failed_tests):
                print("🔧 Verify opportunity ID formats are consistent (OPP-XXXXXXX)")

def main():
    """Main function"""
    tester = OpportunityDataAccessTester()
    success = tester.run_investigation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()