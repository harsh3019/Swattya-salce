#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Opportunity Management System
Testing all master data APIs and opportunity management functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://sawayatta-erp-1.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class OpportunityBackendTester:
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
    
    def test_master_data_apis(self):
        """Test all master data APIs"""
        print("\n📊 TESTING MASTER DATA APIs")
        print("=" * 50)
        
        # Test cases: (endpoint, expected_name, expected_count_min)
        master_data_tests = [
            ("/mst/primary-categories", "Primary Categories", 4),
            ("/mst/products", "Products", 5), 
            ("/mst/stages", "Stages", 8),
            ("/mst/currencies", "Currencies", 3),
            ("/mst/rate-cards", "Rate Cards", 1),
        ]
        
        for endpoint, name, expected_min in master_data_tests:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else len(data.get('data', []))
                    
                    if count >= expected_min:
                        self.log_test(
                            f"GET {endpoint}", 
                            True, 
                            f"Retrieved {count} {name.lower()} (expected min: {expected_min})"
                        )
                    else:
                        self.log_test(
                            f"GET {endpoint}", 
                            False, 
                            f"Only {count} {name.lower()} found, expected min: {expected_min}"
                        )
                else:
                    self.log_test(
                        f"GET {endpoint}", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text[:200]}"
                    )
                    
            except Exception as e:
                self.log_test(f"GET {endpoint}", False, f"Exception: {str(e)}")
        
        # Test sales prices with rate card ID
        self.test_sales_prices()
        
        # Test purchase costs
        self.test_purchase_costs()
    
    def test_sales_prices(self):
        """Test sales prices API with rate card ID"""
        try:
            # First get rate cards to get an ID
            response = requests.get(
                f"{self.base_url}/mst/rate-cards",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                rate_cards = response.json()
                if rate_cards and len(rate_cards) > 0:
                    rate_card_id = rate_cards[0].get('id')
                    
                    # Test sales prices with rate card ID
                    sales_response = requests.get(
                        f"{self.base_url}/mst/sales-prices/{rate_card_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if sales_response.status_code == 200:
                        sales_data = sales_response.json()
                        count = len(sales_data) if isinstance(sales_data, list) else len(sales_data.get('data', []))
                        self.log_test(
                            "GET /mst/sales-prices/{rate_card_id}", 
                            True, 
                            f"Retrieved {count} sales prices for rate card"
                        )
                    else:
                        self.log_test(
                            "GET /mst/sales-prices/{rate_card_id}", 
                            False, 
                            f"Status: {sales_response.status_code}"
                        )
                else:
                    self.log_test("GET /mst/sales-prices/{rate_card_id}", False, "No rate cards found to test with")
            else:
                self.log_test("GET /mst/sales-prices/{rate_card_id}", False, "Could not get rate cards")
                
        except Exception as e:
            self.log_test("GET /mst/sales-prices/{rate_card_id}", False, f"Exception: {str(e)}")
    
    def test_purchase_costs(self):
        """Test purchase costs API - Note: This endpoint may not be implemented yet"""
        try:
            response = requests.get(
                f"{self.base_url}/mst/purchase-costs",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else len(data.get('data', []))
                self.log_test(
                    "GET /mst/purchase-costs", 
                    True, 
                    f"Retrieved {count} purchase costs"
                )
            elif response.status_code == 404:
                self.log_test(
                    "GET /mst/purchase-costs", 
                    False, 
                    "Endpoint not implemented yet (404 Not Found)"
                )
            else:
                self.log_test(
                    "GET /mst/purchase-costs", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET /mst/purchase-costs", False, f"Exception: {str(e)}")
    
    def test_opportunity_apis(self):
        """Test opportunity management APIs"""
        print("\n🎯 TESTING OPPORTUNITY APIs")
        print("=" * 50)
        
        # Test opportunity list
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else len(data.get('data', []))
                self.log_test(
                    "GET /opportunities", 
                    True, 
                    f"Retrieved {count} opportunities"
                )
                
                # Store first opportunity ID for later tests
                self.opportunity_id = None
                if isinstance(data, list) and len(data) > 0:
                    self.opportunity_id = data[0].get('id')
                elif isinstance(data, dict) and data.get('data') and len(data['data']) > 0:
                    self.opportunity_id = data['data'][0].get('id')
                    
            else:
                self.log_test(
                    "GET /opportunities", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET /opportunities", False, f"Exception: {str(e)}")
        
        # Test opportunity KPIs
        self.test_opportunity_kpis()
        
        # Test create opportunity
        self.test_create_opportunity()
        
        # Test single opportunity (if we have an ID)
        if hasattr(self, 'opportunity_id') and self.opportunity_id:
            self.test_single_opportunity()
        elif hasattr(self, 'created_opportunity_id') and self.created_opportunity_id:
            self.opportunity_id = self.created_opportunity_id
            self.test_single_opportunity()
    
    def test_opportunity_kpis(self):
        """Test opportunity KPIs dashboard"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/kpis",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for actual KPI fields returned by the API
                expected_fields = ['total', 'open', 'won', 'lost', 'weighted_pipeline']
                found_fields = []
                
                for field in expected_fields:
                    if field in data:
                        found_fields.append(field)
                
                if len(found_fields) >= 3:  # At least 3 KPI fields should be present
                    self.log_test(
                        "GET /opportunities/kpis", 
                        True, 
                        f"KPI data retrieved with fields: {', '.join(found_fields)}"
                    )
                else:
                    self.log_test(
                        "GET /opportunities/kpis", 
                        False, 
                        f"Missing KPI fields. Found: {found_fields}, Expected: {expected_fields}"
                    )
            else:
                self.log_test(
                    "GET /opportunities/kpis", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET /opportunities/kpis", False, f"Exception: {str(e)}")
    
    def test_create_opportunity(self):
        """Test opportunity creation"""
        try:
            # First get required master data
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                self.log_test("POST /opportunities", False, "Could not get required master data")
                return
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            # Find L1 stage and INR currency
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                self.log_test("POST /opportunities", False, "L1 stage or INR currency not found in master data")
                return
            
            # Sample opportunity data with correct field names
            opportunity_data = {
                "project_title": "Test Opportunity - Backend Testing",
                "company_id": "test-company-id",
                "stage_id": l1_stage['id'],
                "expected_revenue": 100000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-id",
                "win_probability": 50
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                opportunity_id = data.get('opportunity_id')  # Note: using opportunity_id not id
                
                # Check if opportunity ID follows OPP-XXXXXXX format
                if opportunity_id and opportunity_id.startswith('OPP-') and len(opportunity_id) == 11:
                    self.log_test(
                        "POST /opportunities", 
                        True, 
                        f"Opportunity created with ID: {opportunity_id}"
                    )
                    self.created_opportunity_id = data.get('id')  # Store the actual database ID
                else:
                    self.log_test(
                        "POST /opportunities", 
                        False, 
                        f"Invalid opportunity ID format: {opportunity_id}"
                    )
            else:
                self.log_test(
                    "POST /opportunities", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("POST /opportunities", False, f"Exception: {str(e)}")
    
    def test_single_opportunity(self):
        """Test single opportunity retrieval"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    f"GET /opportunities/{self.opportunity_id}", 
                    True, 
                    f"Retrieved opportunity: {data.get('name', 'Unknown')}"
                )
            else:
                self.log_test(
                    f"GET /opportunities/{self.opportunity_id}", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test(f"GET /opportunities/{self.opportunity_id}", False, f"Exception: {str(e)}")
    
    def test_quotation_apis(self):
        """Test quotation APIs"""
        print("\n📋 TESTING QUOTATION APIs")
        print("=" * 50)
        
        # Use created opportunity ID or existing one
        test_opp_id = getattr(self, 'created_opportunity_id', getattr(self, 'opportunity_id', 'test-opp-id'))
        
        # Test list quotations for opportunity
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{test_opp_id}/quotations",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else len(data.get('data', []))
                self.log_test(
                    f"GET /opportunities/{test_opp_id}/quotations", 
                    True, 
                    f"Retrieved {count} quotations for opportunity"
                )
            else:
                self.log_test(
                    f"GET /opportunities/{test_opp_id}/quotations", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test(f"GET /opportunities/{test_opp_id}/quotations", False, f"Exception: {str(e)}")
        
        # Test create quotation
        self.test_create_quotation(test_opp_id)
    
    def test_create_quotation(self, opportunity_id):
        """Test quotation creation"""
        try:
            # First get rate cards for quotation
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            
            if rate_cards_response.status_code != 200:
                self.log_test(f"POST /opportunities/{opportunity_id}/quotations", False, "Could not get rate cards")
                return
            
            rate_cards = rate_cards_response.json()
            if not rate_cards:
                self.log_test(f"POST /opportunities/{opportunity_id}/quotations", False, "No rate cards available")
                return
            
            quotation_data = {
                "quotation_name": "Test Quotation - Backend Testing",
                "rate_card_id": rate_cards[0]['id'],
                "validity_date": "2025-04-30T00:00:00Z",
                "items": []  # Empty items list for basic test
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/quotations",
                headers=self.headers,
                json=quotation_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quotation_id = data.get('quotation_id')  # Note: using quotation_id not id
                
                # Check if quotation ID follows QUO-XXXXXXX format
                if quotation_id and quotation_id.startswith('QUO-') and len(quotation_id) == 11:
                    self.log_test(
                        f"POST /opportunities/{opportunity_id}/quotations", 
                        True, 
                        f"Quotation created with ID: {quotation_id}"
                    )
                else:
                    self.log_test(
                        f"POST /opportunities/{opportunity_id}/quotations", 
                        False, 
                        f"Invalid quotation ID format: {quotation_id}"
                    )
            else:
                self.log_test(
                    f"POST /opportunities/{opportunity_id}/quotations", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test(f"POST /opportunities/{opportunity_id}/quotations", False, f"Exception: {str(e)}")
    
    def test_rbac_permissions(self):
        """Test RBAC permissions for opportunity management"""
        print("\n🔒 TESTING RBAC PERMISSIONS")
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
                opp_permissions = [p for p in permissions if 'opportunities' in p.get('path', '').lower()]
                
                if len(opp_permissions) > 0:
                    self.log_test(
                        "RBAC Opportunity Permissions", 
                        True, 
                        f"Found {len(opp_permissions)} opportunity-related permissions"
                    )
                else:
                    self.log_test(
                        "RBAC Opportunity Permissions", 
                        False, 
                        "No opportunity-related permissions found"
                    )
            else:
                self.log_test(
                    "RBAC Opportunity Permissions", 
                    False, 
                    f"Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("RBAC Opportunity Permissions", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING OPPORTUNITY MANAGEMENT BACKEND API TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Run all test suites
        self.test_master_data_apis()
        self.test_opportunity_apis()
        self.test_quotation_apis()
        self.test_rbac_permissions()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = OpportunityBackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()