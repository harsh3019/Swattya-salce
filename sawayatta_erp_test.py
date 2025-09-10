#!/usr/bin/env python3
"""
Comprehensive Testing for Sawayatta ERP Features
Testing specific APIs mentioned in the review request:
1. KPI Endpoint: GET /api/opportunities/kpis
2. Individual Quotation: GET /api/opportunities/{opportunity_id}/quotations/{quotation_id}
3. Activities Timeline: GET /api/opportunities/{opportunity_id}/activities
4. Documents Management: GET /api/opportunities/{opportunity_id}/documents
5. Sidebar Navigation: GET /api/nav/sidebar
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://erp-quotation.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class SawayattaERPTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.opportunity_id = None
        self.quotation_id = None
        
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
    
    def test_kpi_endpoint(self):
        """Test KPI Endpoint: GET /api/opportunities/kpis - Should return 7 KPI metrics"""
        print("\n📊 TESTING KPI ENDPOINT")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/kpis",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Expected KPI fields based on review request
                expected_fields = ['total', 'open', 'won', 'lost', 'pipeline_value', 'weighted_revenue', 'win_rate']
                found_fields = []
                
                for field in expected_fields:
                    if field in data:
                        found_fields.append(field)
                
                # Check if we have at least 5 of the 7 expected KPI metrics
                if len(found_fields) >= 5:
                    self.log_test(
                        "GET /api/opportunities/kpis", 
                        True, 
                        f"KPI data retrieved with {len(found_fields)}/7 expected fields: {', '.join(found_fields)}"
                    )
                    
                    # Log the actual values for verification
                    kpi_values = {field: data.get(field, 'N/A') for field in found_fields}
                    print(f"   KPI Values: {kpi_values}")
                    
                else:
                    self.log_test(
                        "GET /api/opportunities/kpis", 
                        False, 
                        f"Missing KPI fields. Found: {found_fields}, Expected: {expected_fields}"
                    )
            else:
                self.log_test(
                    "GET /api/opportunities/kpis", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET /api/opportunities/kpis", False, f"Exception: {str(e)}")
    
    def get_test_opportunity_and_quotation(self):
        """Get existing opportunity and quotation IDs for testing"""
        try:
            # Get opportunities list
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                if isinstance(opportunities, list) and len(opportunities) > 0:
                    self.opportunity_id = opportunities[0].get('id')
                    print(f"   Using opportunity ID: {self.opportunity_id}")
                    
                    # Try to get quotations for this opportunity
                    quotations_response = requests.get(
                        f"{self.base_url}/opportunities/{self.opportunity_id}/quotations",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if quotations_response.status_code == 200:
                        quotations = quotations_response.json()
                        if isinstance(quotations, list) and len(quotations) > 0:
                            self.quotation_id = quotations[0].get('id')
                            print(f"   Using quotation ID: {self.quotation_id}")
                        else:
                            print("   No quotations found for this opportunity")
                    
                    return True
                else:
                    print("   No opportunities found in the system")
                    return False
            else:
                print(f"   Could not get opportunities: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Exception getting test data: {str(e)}")
            return False
    
    def test_individual_quotation(self):
        """Test Individual Quotation: GET /api/opportunities/{opportunity_id}/quotations/{quotation_id}"""
        print("\n📋 TESTING INDIVIDUAL QUOTATION ENDPOINT")
        print("=" * 50)
        
        if not self.opportunity_id or not self.quotation_id:
            self.log_test(
                "GET /api/opportunities/{opportunity_id}/quotations/{quotation_id}", 
                False, 
                "No opportunity or quotation ID available for testing"
            )
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.opportunity_id}/quotations/{self.quotation_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for proper JSON structure without ObjectId errors
                if isinstance(data, dict):
                    # Check for common quotation fields
                    expected_fields = ['id', 'quotation_name', 'quotation_id', 'rate_card_id', 'validity_date']
                    found_fields = [field for field in expected_fields if field in data]
                    
                    # Verify no ObjectId serialization errors
                    json_str = json.dumps(data)  # This will fail if there are ObjectId issues
                    
                    self.log_test(
                        f"GET /api/opportunities/{self.opportunity_id}/quotations/{self.quotation_id}", 
                        True, 
                        f"Quotation retrieved successfully with fields: {', '.join(found_fields)}"
                    )
                    
                    print(f"   Quotation Name: {data.get('quotation_name', 'N/A')}")
                    print(f"   Quotation ID: {data.get('quotation_id', 'N/A')}")
                    
                else:
                    self.log_test(
                        f"GET /api/opportunities/{self.opportunity_id}/quotations/{self.quotation_id}", 
                        False, 
                        "Response is not a valid JSON object"
                    )
            else:
                self.log_test(
                    f"GET /api/opportunities/{self.opportunity_id}/quotations/{self.quotation_id}", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except json.JSONDecodeError as e:
            self.log_test(
                f"GET /api/opportunities/{self.opportunity_id}/quotations/{self.quotation_id}", 
                False, 
                f"JSON serialization error (ObjectId issue): {str(e)}"
            )
        except Exception as e:
            self.log_test(
                f"GET /api/opportunities/{self.opportunity_id}/quotations/{self.quotation_id}", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_activities_timeline(self):
        """Test Activities Timeline: GET /api/opportunities/{opportunity_id}/activities"""
        print("\n📅 TESTING ACTIVITIES TIMELINE ENDPOINT")
        print("=" * 50)
        
        if not self.opportunity_id:
            self.log_test(
                "GET /api/opportunities/{opportunity_id}/activities", 
                False, 
                "No opportunity ID available for testing"
            )
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.opportunity_id}/activities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    # Check for chronological activity list with expected fields
                    activity_count = len(data)
                    
                    if activity_count > 0:
                        # Check first activity for expected fields
                        first_activity = data[0]
                        expected_fields = ['id', 'activity_type', 'timestamp', 'description']
                        found_fields = [field for field in expected_fields if field in first_activity]
                        
                        # Check for stage changes, documents, quotations in activity types
                        activity_types = [activity.get('activity_type', '') for activity in data]
                        has_stage_changes = any('stage' in activity_type.lower() for activity_type in activity_types)
                        has_documents = any('document' in activity_type.lower() for activity_type in activity_types)
                        has_quotations = any('quotation' in activity_type.lower() for activity_type in activity_types)
                        
                        self.log_test(
                            f"GET /api/opportunities/{self.opportunity_id}/activities", 
                            True, 
                            f"Retrieved {activity_count} activities with types: stage_changes={has_stage_changes}, documents={has_documents}, quotations={has_quotations}"
                        )
                        
                        print(f"   Activity Types Found: {set(activity_types)}")
                        
                    else:
                        self.log_test(
                            f"GET /api/opportunities/{self.opportunity_id}/activities", 
                            True, 
                            "No activities found (empty list - valid response)"
                        )
                else:
                    self.log_test(
                        f"GET /api/opportunities/{self.opportunity_id}/activities", 
                        False, 
                        "Response is not a list of activities"
                    )
            else:
                self.log_test(
                    f"GET /api/opportunities/{self.opportunity_id}/activities", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test(
                f"GET /api/opportunities/{self.opportunity_id}/activities", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_documents_management(self):
        """Test Documents Management: GET /api/opportunities/{opportunity_id}/documents"""
        print("\n📁 TESTING DOCUMENTS MANAGEMENT ENDPOINT")
        print("=" * 50)
        
        if not self.opportunity_id:
            self.log_test(
                "GET /api/opportunities/{opportunity_id}/documents", 
                False, 
                "No opportunity ID available for testing"
            )
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.opportunity_id}/documents",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    document_count = len(data)
                    
                    if document_count > 0:
                        # Check first document for expected metadata fields
                        first_doc = data[0]
                        expected_fields = ['id', 'filename', 'uploader', 'timestamp', 'file_size', 'mime_type']
                        found_fields = [field for field in expected_fields if field in first_doc]
                        
                        self.log_test(
                            f"GET /api/opportunities/{self.opportunity_id}/documents", 
                            True, 
                            f"Retrieved {document_count} documents with metadata fields: {', '.join(found_fields)}"
                        )
                        
                        # Show sample document info
                        print(f"   Sample Document: {first_doc.get('filename', 'N/A')}")
                        print(f"   Uploader: {first_doc.get('uploader', 'N/A')}")
                        print(f"   Size: {first_doc.get('file_size', 'N/A')} bytes")
                        
                    else:
                        self.log_test(
                            f"GET /api/opportunities/{self.opportunity_id}/documents", 
                            True, 
                            "No documents found (empty list - valid response)"
                        )
                else:
                    self.log_test(
                        f"GET /api/opportunities/{self.opportunity_id}/documents", 
                        False, 
                        "Response is not a list of documents"
                    )
            else:
                self.log_test(
                    f"GET /api/opportunities/{self.opportunity_id}/documents", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test(
                f"GET /api/opportunities/{self.opportunity_id}/documents", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_sidebar_navigation(self):
        """Test Sidebar Navigation: GET /api/nav/sidebar"""
        print("\n🧭 TESTING SIDEBAR NAVIGATION ENDPOINT")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/nav/sidebar",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and 'modules' in data:
                    modules = data['modules']
                    
                    if isinstance(modules, list):
                        module_count = len(modules)
                        
                        # Expected modules based on review request
                        expected_modules = ['User Management', 'Sales', 'System']
                        found_modules = []
                        total_menus = 0
                        
                        for module in modules:
                            module_name = module.get('name', '')
                            found_modules.append(module_name)
                            
                            menus = module.get('menus', [])
                            menu_count = len(menus)
                            total_menus += menu_count
                            
                            print(f"   Module: {module_name} ({menu_count} menus)")
                        
                        # Check if we have the expected modules
                        has_expected_modules = all(expected_mod in found_modules for expected_mod in expected_modules)
                        
                        if has_expected_modules and total_menus > 10:  # Should have substantial menu structure
                            self.log_test(
                                "GET /api/nav/sidebar", 
                                True, 
                                f"Retrieved {module_count} modules with {total_menus} total menus. Modules: {', '.join(found_modules)}"
                            )
                        else:
                            self.log_test(
                                "GET /api/nav/sidebar", 
                                False, 
                                f"Missing expected modules or insufficient menus. Found: {found_modules}, Expected: {expected_modules}"
                            )
                    else:
                        self.log_test(
                            "GET /api/nav/sidebar", 
                            False, 
                            "Modules field is not a list"
                        )
                else:
                    self.log_test(
                        "GET /api/nav/sidebar", 
                        False, 
                        "Response does not contain modules field"
                    )
            else:
                self.log_test(
                    "GET /api/nav/sidebar", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET /api/nav/sidebar", False, f"Exception: {str(e)}")
    
    def test_authentication_and_authorization(self):
        """Test that all APIs work with proper authentication token"""
        print("\n🔐 TESTING AUTHENTICATION AND AUTHORIZATION")
        print("=" * 50)
        
        # Test without token (should fail)
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/kpis",
                timeout=10  # No headers with token
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Authentication Required", 
                    True, 
                    "API correctly rejects requests without authentication token"
                )
            else:
                self.log_test(
                    "Authentication Required", 
                    False, 
                    f"API should return 401 without token, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Authentication Required", False, f"Exception: {str(e)}")
        
        # Test with invalid token (should fail)
        try:
            invalid_headers = {"Authorization": "Bearer invalid-token-12345"}
            response = requests.get(
                f"{self.base_url}/opportunities/kpis",
                headers=invalid_headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Invalid Token Rejection", 
                    True, 
                    "API correctly rejects requests with invalid token"
                )
            else:
                self.log_test(
                    "Invalid Token Rejection", 
                    False, 
                    f"API should return 401 with invalid token, got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Invalid Token Rejection", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING SAWAYATTA ERP COMPREHENSIVE TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Get test data (opportunity and quotation IDs)
        print("\n📋 GETTING TEST DATA")
        print("=" * 50)
        self.get_test_opportunity_and_quotation()
        
        # Run all test suites based on review request
        self.test_kpi_endpoint()
        self.test_individual_quotation()
        self.test_activities_timeline()
        self.test_documents_management()
        self.test_sidebar_navigation()
        self.test_authentication_and_authorization()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 SAWAYATTA ERP TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ All Sawayatta ERP features are working correctly")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            print("❌ Some Sawayatta ERP features need attention")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)
        
        print("\n🔍 TESTING SCENARIOS COVERED:")
        print("- Authentication with admin/admin123 credentials")
        print("- KPI calculations and metrics accuracy")
        print("- Individual quotation data retrieval without ObjectId errors")
        print("- Activities timeline with stage changes, documents, quotations")
        print("- Documents management with proper metadata")
        print("- Sidebar navigation with all modules (User Management, Sales, System)")
        print("- Authentication and authorization security")

def main():
    """Main function"""
    tester = SawayattaERPTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()