#!/usr/bin/env python3
"""
Opportunity Data Display Debug Test
Focus on debugging the issue where KPIs show 7 opportunities but table shows empty data
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://lead-opp-crm.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class OpportunityDebugTester:
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
        """Test admin authentication with specific credentials"""
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
                    "Admin Login (admin/admin123)", 
                    True, 
                    f"✅ SUCCESS - User: {user_data.get('username')}, Email: {user_data.get('email')}, Role ID: {user_data.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Login (admin/admin123)", False, f"❌ FAILED - Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login (admin/admin123)", False, f"❌ EXCEPTION - {str(e)}")
            return False
    
    def test_opportunities_kpis_detailed(self):
        """Test GET /api/opportunities/kpis with detailed analysis"""
        print("\n📊 TESTING OPPORTUNITIES KPIs API")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/kpis",
                headers=self.headers,
                timeout=10
            )
            
            print(f"🔍 KPIs API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"🔍 KPIs API Raw Response: {json.dumps(data, indent=2)}")
                
                # Check for total opportunities
                total_opportunities = data.get('total', 0)
                
                if total_opportunities == 7:
                    self.log_test(
                        "GET /api/opportunities/kpis - Total Count", 
                        True, 
                        f"✅ CONFIRMED - Shows {total_opportunities} total opportunities as expected"
                    )
                else:
                    self.log_test(
                        "GET /api/opportunities/kpis - Total Count", 
                        False, 
                        f"❌ MISMATCH - Shows {total_opportunities} opportunities, expected 7"
                    )
                
                # Analyze all KPI fields
                kpi_fields = ['total', 'open', 'won', 'lost', 'weighted_pipeline']
                found_fields = {}
                
                for field in kpi_fields:
                    if field in data:
                        found_fields[field] = data[field]
                
                self.log_test(
                    "GET /api/opportunities/kpis - Field Analysis", 
                    True, 
                    f"KPI Fields Found: {found_fields}"
                )
                
            else:
                self.log_test(
                    "GET /api/opportunities/kpis", 
                    False, 
                    f"❌ API ERROR - Status: {response.status_code}, Response: {response.text[:500]}"
                )
                
        except Exception as e:
            self.log_test("GET /api/opportunities/kpis", False, f"❌ EXCEPTION - {str(e)}")
    
    def test_opportunities_list_detailed(self):
        """Test GET /api/opportunities with detailed data structure analysis"""
        print("\n🎯 TESTING OPPORTUNITIES LIST API")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            print(f"🔍 Opportunities API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"🔍 Opportunities API Raw Response Type: {type(data)}")
                print(f"🔍 Opportunities API Raw Response: {json.dumps(data, indent=2, default=str)}")
                
                # Analyze response structure
                if isinstance(data, list):
                    count = len(data)
                    self.log_test(
                        "GET /api/opportunities - Response Structure", 
                        True, 
                        f"✅ DIRECT ARRAY - Contains {count} opportunities"
                    )
                    
                    if count > 0:
                        # Analyze first opportunity structure
                        first_opp = data[0]
                        self.analyze_opportunity_structure(first_opp, "First Opportunity in Array")
                    else:
                        self.log_test(
                            "GET /api/opportunities - Data Count", 
                            False, 
                            f"❌ EMPTY ARRAY - No opportunities found despite KPIs showing 7"
                        )
                        
                elif isinstance(data, dict):
                    # Check if data is wrapped in another object
                    if 'data' in data:
                        opportunities = data['data']
                        count = len(opportunities) if isinstance(opportunities, list) else 0
                        self.log_test(
                            "GET /api/opportunities - Response Structure", 
                            True, 
                            f"✅ WRAPPED OBJECT - data.data contains {count} opportunities"
                        )
                        
                        if count > 0 and isinstance(opportunities, list):
                            first_opp = opportunities[0]
                            self.analyze_opportunity_structure(first_opp, "First Opportunity in data.data")
                        else:
                            self.log_test(
                                "GET /api/opportunities - Data Count", 
                                False, 
                                f"❌ EMPTY DATA ARRAY - No opportunities in data.data despite KPIs showing 7"
                            )
                    else:
                        # Check if it's a single opportunity object
                        if 'id' in data or 'opportunity_id' in data:
                            self.log_test(
                                "GET /api/opportunities - Response Structure", 
                                True, 
                                f"✅ SINGLE OBJECT - Contains single opportunity"
                            )
                            self.analyze_opportunity_structure(data, "Single Opportunity Object")
                        else:
                            self.log_test(
                                "GET /api/opportunities - Response Structure", 
                                False, 
                                f"❌ UNKNOWN OBJECT STRUCTURE - Keys: {list(data.keys())}"
                            )
                else:
                    self.log_test(
                        "GET /api/opportunities - Response Structure", 
                        False, 
                        f"❌ UNEXPECTED TYPE - Response is {type(data)}, not list or dict"
                    )
                    
            else:
                self.log_test(
                    "GET /api/opportunities", 
                    False, 
                    f"❌ API ERROR - Status: {response.status_code}, Response: {response.text[:500]}"
                )
                
        except Exception as e:
            self.log_test("GET /api/opportunities", False, f"❌ EXCEPTION - {str(e)}")
    
    def analyze_opportunity_structure(self, opportunity, context):
        """Analyze the structure of an opportunity object"""
        print(f"\n🔬 ANALYZING OPPORTUNITY STRUCTURE - {context}")
        print("-" * 50)
        
        # Expected fields for frontend
        expected_fields = [
            'id', 'opportunity_id', 'project_title', 'company_id', 'stage_id', 
            'status', 'expected_revenue', 'weighted_revenue', 'win_probability', 
            'lead_owner_id', 'created_at'
        ]
        
        found_fields = []
        missing_fields = []
        
        for field in expected_fields:
            if field in opportunity:
                found_fields.append(field)
                value = opportunity[field]
                print(f"  ✅ {field}: {value} ({type(value).__name__})")
            else:
                missing_fields.append(field)
                print(f"  ❌ {field}: MISSING")
        
        # Check for unexpected fields
        unexpected_fields = [key for key in opportunity.keys() if key not in expected_fields]
        if unexpected_fields:
            print(f"  🔍 Additional fields: {unexpected_fields}")
        
        # Log analysis results
        if len(missing_fields) == 0:
            self.log_test(
                f"Opportunity Structure Analysis - {context}", 
                True, 
                f"✅ ALL REQUIRED FIELDS PRESENT - Found: {len(found_fields)}, Missing: 0"
            )
        else:
            self.log_test(
                f"Opportunity Structure Analysis - {context}", 
                False, 
                f"❌ MISSING FIELDS - Found: {len(found_fields)}, Missing: {missing_fields}"
            )
        
        # Check data types
        self.check_data_types(opportunity, context)
    
    def check_data_types(self, opportunity, context):
        """Check data types of opportunity fields"""
        print(f"\n🔍 DATA TYPE VALIDATION - {context}")
        print("-" * 30)
        
        type_checks = [
            ('id', str),
            ('opportunity_id', str),
            ('project_title', str),
            ('company_id', str),
            ('stage_id', str),
            ('expected_revenue', (int, float)),
            ('weighted_revenue', (int, float)),
            ('win_probability', (int, float)),
            ('lead_owner_id', str),
        ]
        
        type_issues = []
        
        for field, expected_type in type_checks:
            if field in opportunity:
                value = opportunity[field]
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        type_issues.append(f"{field}: expected {expected_type}, got {type(value).__name__}")
                        print(f"  ❌ {field}: {value} (expected {expected_type}, got {type(value).__name__})")
                    else:
                        print(f"  ✅ {field}: {value} ({type(value).__name__})")
                else:
                    if not isinstance(value, expected_type):
                        type_issues.append(f"{field}: expected {expected_type.__name__}, got {type(value).__name__}")
                        print(f"  ❌ {field}: {value} (expected {expected_type.__name__}, got {type(value).__name__})")
                    else:
                        print(f"  ✅ {field}: {value} ({type(value).__name__})")
        
        if len(type_issues) == 0:
            self.log_test(
                f"Data Type Validation - {context}", 
                True, 
                f"✅ ALL DATA TYPES CORRECT"
            )
        else:
            self.log_test(
                f"Data Type Validation - {context}", 
                False, 
                f"❌ TYPE ISSUES - {'; '.join(type_issues)}"
            )
    
    def compare_kpis_vs_list(self):
        """Compare KPI data with list data to identify discrepancy"""
        print("\n🔍 COMPARING KPIs vs LIST DATA")
        print("=" * 50)
        
        # Get KPI data
        kpi_total = 0
        try:
            kpi_response = requests.get(f"{self.base_url}/opportunities/kpis", headers=self.headers, timeout=10)
            if kpi_response.status_code == 200:
                kpi_data = kpi_response.json()
                kpi_total = kpi_data.get('total', 0)
        except:
            pass
        
        # Get list data
        list_count = 0
        try:
            list_response = requests.get(f"{self.base_url}/opportunities", headers=self.headers, timeout=10)
            if list_response.status_code == 200:
                list_data = list_response.json()
                if isinstance(list_data, list):
                    list_count = len(list_data)
                elif isinstance(list_data, dict) and 'data' in list_data:
                    list_count = len(list_data['data']) if isinstance(list_data['data'], list) else 0
        except:
            pass
        
        print(f"🔍 KPI Total: {kpi_total}")
        print(f"🔍 List Count: {list_count}")
        
        if kpi_total == list_count:
            self.log_test(
                "KPIs vs List Comparison", 
                True, 
                f"✅ CONSISTENT - Both show {kpi_total} opportunities"
            )
        else:
            self.log_test(
                "KPIs vs List Comparison", 
                False, 
                f"❌ MISMATCH - KPIs show {kpi_total}, List shows {list_count} opportunities"
            )
            
            # Provide diagnosis
            if kpi_total > 0 and list_count == 0:
                print("🔍 DIAGNOSIS: KPIs show data exists but list API returns empty")
                print("   Possible causes:")
                print("   - List API has different filtering logic")
                print("   - List API has pagination that's not being handled")
                print("   - List API has permission restrictions")
                print("   - Data format mismatch between KPI and List calculations")
    
    def test_pagination_and_filters(self):
        """Test if pagination or filters are affecting the results"""
        print("\n📄 TESTING PAGINATION AND FILTERS")
        print("=" * 50)
        
        # Test with different query parameters
        test_params = [
            {},  # No parameters
            {"page": 1, "limit": 10},  # Pagination
            {"page": 1, "per_page": 10},  # Alternative pagination
            {"offset": 0, "limit": 10},  # Offset pagination
            {"status": "active"},  # Status filter
            {"is_active": True},  # Active filter
        ]
        
        for i, params in enumerate(test_params):
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities",
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict) and 'data' in data:
                        count = len(data['data']) if isinstance(data['data'], list) else 0
                    else:
                        count = 1 if data else 0
                    
                    param_str = f"?{requests.compat.urlencode(params)}" if params else "no params"
                    self.log_test(
                        f"Pagination Test {i+1}", 
                        True, 
                        f"With {param_str}: {count} opportunities returned"
                    )
                else:
                    param_str = f"?{requests.compat.urlencode(params)}" if params else "no params"
                    self.log_test(
                        f"Pagination Test {i+1}", 
                        False, 
                        f"With {param_str}: Status {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"Pagination Test {i+1}", False, f"Exception: {str(e)}")
    
    def run_debug_tests(self):
        """Run all debug tests"""
        print("🔍 STARTING OPPORTUNITY DATA DISPLAY DEBUG TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with debug tests")
            return False
        
        # Run debug test suites in order
        self.test_opportunities_kpis_detailed()
        self.test_opportunities_list_detailed()
        self.compare_kpis_vs_list()
        self.test_pagination_and_filters()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 DEBUG TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)
        
        print("\n🔍 DEBUGGING CONCLUSIONS:")
        print("-" * 40)
        
        # Analyze results to provide conclusions
        kpi_working = any("KPIs API" in result and "✅ PASS" in result for result in self.test_results)
        list_working = any("Opportunities API Response Status: 200" in result for result in self.test_results)
        data_mismatch = any("MISMATCH" in result for result in self.test_results)
        
        if kpi_working and not list_working:
            print("❌ ISSUE: KPIs API works but Opportunities List API fails")
        elif kpi_working and list_working and data_mismatch:
            print("❌ ISSUE: Both APIs work but return different counts - data inconsistency")
        elif kpi_working and list_working and not data_mismatch:
            print("✅ CONCLUSION: Both APIs work and return consistent data")
        else:
            print("❓ INCONCLUSIVE: Need to check individual test results above")

def main():
    """Main function"""
    tester = OpportunityDebugTester()
    success = tester.run_debug_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()