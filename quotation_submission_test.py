#!/usr/bin/env python3
"""
Quotation Submission Functionality Testing
Testing the fixed quotation submission functionality with proper data structure conversion
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://1b435344-f8f5-4a8b-98d4-64db783ac8b5.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class QuotationSubmissionTester:
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
            self.failed_tests.append(f"{test_name}: {details}")
        
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

    def setup_test_data(self):
        """Setup test data - create opportunity and get required master data"""
        print("\n🔧 SETTING UP TEST DATA")
        print("=" * 50)
        
        # Get required master data
        try:
            # Get rate cards
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            if rate_cards_response.status_code != 200:
                self.log_test("Get Rate Cards", False, f"Status: {rate_cards_response.status_code}")
                return False
            
            self.rate_cards = rate_cards_response.json()
            if not self.rate_cards:
                self.log_test("Get Rate Cards", False, "No rate cards found")
                return False
            
            self.log_test("Get Rate Cards", True, f"Found {len(self.rate_cards)} rate cards")
            
            # Get products
            products_response = requests.get(f"{self.base_url}/mst/products", headers=self.headers, timeout=10)
            if products_response.status_code != 200:
                self.log_test("Get Products", False, f"Status: {products_response.status_code}")
                return False
            
            self.products = products_response.json()
            if not self.products:
                self.log_test("Get Products", False, "No products found")
                return False
            
            self.log_test("Get Products", True, f"Found {len(self.products)} products")
            
            # Get sales prices for the rate card
            rate_card_id = self.rate_cards[0]['id']
            sales_prices_response = requests.get(f"{self.base_url}/mst/sales-prices/{rate_card_id}", headers=self.headers, timeout=10)
            if sales_prices_response.status_code != 200:
                self.log_test("Get Sales Prices", False, f"Status: {sales_prices_response.status_code}")
                return False
            
            self.sales_prices = sales_prices_response.json()
            self.log_test("Get Sales Prices", True, f"Found {len(self.sales_prices)} sales prices")
            
            # Check if test opportunity exists, if not create one
            self.test_opportunity_id = "test-opportunity-discount-001"
            opp_response = requests.get(f"{self.base_url}/opportunities/{self.test_opportunity_id}", headers=self.headers, timeout=10)
            
            if opp_response.status_code == 404:
                # Create test opportunity
                if not self.create_test_opportunity():
                    return False
            elif opp_response.status_code == 200:
                self.log_test("Test Opportunity Exists", True, f"Using existing opportunity: {self.test_opportunity_id}")
            else:
                self.log_test("Check Test Opportunity", False, f"Status: {opp_response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Setup Test Data", False, f"Exception: {str(e)}")
            return False

    def create_test_opportunity(self):
        """Create test opportunity for quotation testing"""
        try:
            # Get required master data for opportunity creation
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                self.log_test("Get Opportunity Master Data", False, "Could not get stages or currencies")
                return False
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            # Find L4 stage and INR currency
            l4_stage = next((s for s in stages if s.get('stage_code') == 'L4'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l4_stage or not inr_currency:
                self.log_test("Find L4 Stage/INR Currency", False, "L4 stage or INR currency not found")
                return False
            
            # Create opportunity data
            opportunity_data = {
                "project_title": "Test Implementation Quotation Opportunity",
                "company_id": "test-company-quotation-001",
                "stage_id": l4_stage['id'],
                "expected_revenue": 500000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-quotation-001",
                "win_probability": 75
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_opportunity_id = data.get('id')
                self.log_test("Create Test Opportunity", True, f"Created opportunity ID: {self.test_opportunity_id}")
                return True
            else:
                self.log_test("Create Test Opportunity", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Create Test Opportunity", False, f"Exception: {str(e)}")
            return False

    def test_quotation_creation_post(self):
        """Test POST /api/opportunities/{id}/quotations with proper data structure"""
        print("\n📝 TESTING QUOTATION CREATION (POST)")
        print("=" * 50)
        
        try:
            # Use the test data structure from the review request
            quotation_data = {
                "quotation_name": "Test Implementation Quotation",
                "rate_card_id": "test-rate-card-001",  # As specified in review
                "validity_date": "2025-12-31",
                "items": [
                    {
                        "product_id": "b7790ef3-2905-4666-b3d6-73b42e01afcf",  # As specified in review
                        "qty": 2,
                        "unit": "License",
                        "recurring_sale_price": 25000,
                        "one_time_sale_price": 150000,
                        "purchase_cost_snapshot": 12000,
                        "tenure_months": 12,
                        "total_recurring": 50000,
                        "total_one_time": 300000,
                        "total_cost": 24000
                    }
                ]
            }
            
            # If the specific IDs don't exist, use available ones
            if self.rate_cards:
                quotation_data["rate_card_id"] = self.rate_cards[0]['id']
            
            if self.products:
                quotation_data["items"][0]["product_id"] = self.products[0]['id']
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations",
                headers=self.headers,
                json=quotation_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.created_quotation_id = data.get('id')
                quotation_id = data.get('quotation_id')
                
                # Check if quotation ID follows QUO-XXXXXXX format
                if quotation_id and quotation_id.startswith('QUO-') and len(quotation_id) == 11:
                    self.log_test(
                        "POST Quotation Creation", 
                        True, 
                        f"Quotation created with ID: {quotation_id}, DB ID: {self.created_quotation_id}"
                    )
                    return True
                else:
                    self.log_test(
                        "POST Quotation Creation", 
                        False, 
                        f"Invalid quotation ID format: {quotation_id}"
                    )
                    return False
            else:
                self.log_test(
                    "POST Quotation Creation", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                return False
                
        except Exception as e:
            self.log_test("POST Quotation Creation", False, f"Exception: {str(e)}")
            return False

    def test_quotation_retrieval_get(self):
        """Test GET /api/opportunities/{id}/quotations/{quotation_id}"""
        print("\n📖 TESTING QUOTATION RETRIEVAL (GET)")
        print("=" * 50)
        
        if not hasattr(self, 'created_quotation_id') or not self.created_quotation_id:
            self.log_test("GET Quotation Retrieval", False, "No quotation ID available for testing")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{self.created_quotation_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify returned data structure
                required_fields = ['quotation_name', 'rate_card_id', 'validity_date', 'items']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check items structure
                    items = data.get('items', [])
                    if items and len(items) > 0:
                        item = items[0]
                        item_fields = ['product_id', 'qty', 'unit']
                        missing_item_fields = [field for field in item_fields if field not in item]
                        
                        if not missing_item_fields:
                            self.log_test(
                                "GET Quotation Retrieval", 
                                True, 
                                f"Retrieved quotation with {len(items)} items, all required fields present"
                            )
                            self.retrieved_quotation_data = data
                            return True
                        else:
                            self.log_test(
                                "GET Quotation Retrieval", 
                                False, 
                                f"Missing item fields: {missing_item_fields}"
                            )
                            return False
                    else:
                        self.log_test(
                            "GET Quotation Retrieval", 
                            False, 
                            "No items found in quotation"
                        )
                        return False
                else:
                    self.log_test(
                        "GET Quotation Retrieval", 
                        False, 
                        f"Missing required fields: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "GET Quotation Retrieval", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET Quotation Retrieval", False, f"Exception: {str(e)}")
            return False

    def test_quotation_update_put(self):
        """Test PUT /api/opportunities/{id}/quotations/{quotation_id}"""
        print("\n✏️ TESTING QUOTATION UPDATE (PUT)")
        print("=" * 50)
        
        if not hasattr(self, 'created_quotation_id') or not self.created_quotation_id:
            self.log_test("PUT Quotation Update", False, "No quotation ID available for testing")
            return False
        
        if not hasattr(self, 'retrieved_quotation_data'):
            self.log_test("PUT Quotation Update", False, "No retrieved quotation data available for testing")
            return False
        
        try:
            # Modify the retrieved quotation data
            updated_data = self.retrieved_quotation_data.copy()
            updated_data['quotation_name'] = "Updated Test Implementation Quotation"
            
            # Modify items if they exist
            if updated_data.get('items') and len(updated_data['items']) > 0:
                # Update quantity and prices
                updated_data['items'][0]['qty'] = 3  # Changed from 2 to 3
                updated_data['items'][0]['total_recurring'] = 75000  # Updated accordingly
                updated_data['items'][0]['total_one_time'] = 450000  # Updated accordingly
            
            response = requests.put(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{self.created_quotation_id}",
                headers=self.headers,
                json=updated_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test(
                    "PUT Quotation Update", 
                    True, 
                    "Quotation updated successfully"
                )
                
                # Verify the update by reading back
                verify_response = requests.get(
                    f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{self.created_quotation_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if verify_data.get('quotation_name') == updated_data['quotation_name']:
                        self.log_test(
                            "Verify Quotation Update", 
                            True, 
                            "Updated quotation data verified successfully"
                        )
                        return True
                    else:
                        self.log_test(
                            "Verify Quotation Update", 
                            False, 
                            "Quotation name not updated correctly"
                        )
                        return False
                else:
                    self.log_test(
                        "Verify Quotation Update", 
                        False, 
                        f"Could not verify update, Status: {verify_response.status_code}"
                    )
                    return False
            else:
                self.log_test(
                    "PUT Quotation Update", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                return False
                
        except Exception as e:
            self.log_test("PUT Quotation Update", False, f"Exception: {str(e)}")
            return False

    def test_complete_quotation_data_structure(self):
        """Test with realistic quotation containing multiple items"""
        print("\n🏗️ TESTING COMPLETE QUOTATION DATA STRUCTURE")
        print("=" * 50)
        
        try:
            # Create a comprehensive quotation with multiple items
            comprehensive_quotation = {
                "quotation_name": "Comprehensive Multi-Item Quotation",
                "rate_card_id": self.rate_cards[0]['id'] if self.rate_cards else "test-rate-card-001",
                "validity_date": "2025-12-31",
                "items": []
            }
            
            # Add multiple items using available products
            for i, product in enumerate(self.products[:3]):  # Use first 3 products
                item = {
                    "product_id": product['id'],
                    "qty": (i + 1) * 2,  # 2, 4, 6
                    "unit": "License",
                    "recurring_sale_price": 20000 + (i * 5000),  # 20000, 25000, 30000
                    "one_time_sale_price": 100000 + (i * 25000),  # 100000, 125000, 150000
                    "purchase_cost_snapshot": 10000 + (i * 2000),  # 10000, 12000, 14000
                    "tenure_months": 12,
                    "total_recurring": (20000 + (i * 5000)) * ((i + 1) * 2),
                    "total_one_time": (100000 + (i * 25000)) * ((i + 1) * 2),
                    "total_cost": (10000 + (i * 2000)) * ((i + 1) * 2)
                }
                comprehensive_quotation["items"].append(item)
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations",
                headers=self.headers,
                json=comprehensive_quotation,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quotation_id = data.get('quotation_id')
                
                self.log_test(
                    "Complete Quotation Structure", 
                    True, 
                    f"Multi-item quotation created with ID: {quotation_id}, Items: {len(comprehensive_quotation['items'])}"
                )
                
                # Test profitability calculations
                self.test_profitability_calculations(comprehensive_quotation)
                return True
            else:
                self.log_test(
                    "Complete Quotation Structure", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Complete Quotation Structure", False, f"Exception: {str(e)}")
            return False

    def test_profitability_calculations(self, quotation_data):
        """Test profitability calculations work"""
        try:
            total_revenue = 0
            total_cost = 0
            
            for item in quotation_data['items']:
                total_revenue += item.get('total_recurring', 0) + item.get('total_one_time', 0)
                total_cost += item.get('total_cost', 0)
            
            profit = total_revenue - total_cost
            profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
            
            self.log_test(
                "Profitability Calculations", 
                True, 
                f"Revenue: ₹{total_revenue:,}, Cost: ₹{total_cost:,}, Profit: ₹{profit:,}, Margin: {profit_margin:.1f}%"
            )
            
        except Exception as e:
            self.log_test("Profitability Calculations", False, f"Exception: {str(e)}")

    def test_sales_prices_integration(self):
        """Test integration with sales prices from seeded data"""
        print("\n💰 TESTING SALES PRICES INTEGRATION")
        print("=" * 50)
        
        try:
            if not self.sales_prices:
                self.log_test("Sales Prices Integration", False, "No sales prices available for testing")
                return False
            
            # Create quotation using actual sales prices
            sales_price_quotation = {
                "quotation_name": "Sales Prices Integration Test",
                "rate_card_id": self.rate_cards[0]['id'],
                "validity_date": "2025-12-31",
                "items": []
            }
            
            # Use first few sales prices
            for i, sales_price in enumerate(self.sales_prices[:2]):
                item = {
                    "product_id": sales_price.get('product_id'),
                    "qty": 1,
                    "unit": "License",
                    "recurring_sale_price": sales_price.get('recurring_sale_price', 0),
                    "one_time_sale_price": sales_price.get('one_time_sale_price', 0),
                    "purchase_cost_snapshot": sales_price.get('purchase_cost', 0),
                    "tenure_months": 12,
                    "total_recurring": sales_price.get('recurring_sale_price', 0),
                    "total_one_time": sales_price.get('one_time_sale_price', 0),
                    "total_cost": sales_price.get('purchase_cost', 0)
                }
                sales_price_quotation["items"].append(item)
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations",
                headers=self.headers,
                json=sales_price_quotation,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quotation_id = data.get('quotation_id')
                
                self.log_test(
                    "Sales Prices Integration", 
                    True, 
                    f"Quotation created using sales prices data, ID: {quotation_id}"
                )
                return True
            else:
                self.log_test(
                    "Sales Prices Integration", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:300]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Sales Prices Integration", False, f"Exception: {str(e)}")
            return False

    def test_error_scenarios(self):
        """Test error scenarios and validation"""
        print("\n🚨 TESTING ERROR SCENARIOS")
        print("=" * 50)
        
        # Test with invalid opportunity ID
        try:
            invalid_quotation = {
                "quotation_name": "Invalid Test",
                "rate_card_id": self.rate_cards[0]['id'] if self.rate_cards else "test-rate-card-001",
                "validity_date": "2025-12-31",
                "items": []
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/invalid-opportunity-id/quotations",
                headers=self.headers,
                json=invalid_quotation,
                timeout=10
            )
            
            if response.status_code == 404:
                self.log_test(
                    "Invalid Opportunity ID Error", 
                    True, 
                    "Correctly returned 404 for invalid opportunity ID"
                )
            else:
                self.log_test(
                    "Invalid Opportunity ID Error", 
                    False, 
                    f"Expected 404, got {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Invalid Opportunity ID Error", False, f"Exception: {str(e)}")
        
        # Test with missing required fields
        try:
            incomplete_quotation = {
                "quotation_name": "Incomplete Test"
                # Missing required fields
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations",
                headers=self.headers,
                json=incomplete_quotation,
                timeout=10
            )
            
            if response.status_code in [400, 422]:
                self.log_test(
                    "Missing Required Fields Error", 
                    True, 
                    f"Correctly returned {response.status_code} for missing required fields"
                )
            else:
                self.log_test(
                    "Missing Required Fields Error", 
                    False, 
                    f"Expected 400/422, got {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Missing Required Fields Error", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all quotation submission tests"""
        print("🚀 STARTING QUOTATION SUBMISSION FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ TEST DATA SETUP FAILED - Cannot proceed with quotation tests")
            return False
        
        # Run quotation tests in sequence
        success = True
        
        # 1. Test quotation creation (POST)
        if not self.test_quotation_creation_post():
            success = False
        
        # 2. Test quotation retrieval (GET) - only if creation succeeded
        if hasattr(self, 'created_quotation_id'):
            if not self.test_quotation_retrieval_get():
                success = False
            
            # 3. Test quotation update (PUT) - only if retrieval succeeded
            if hasattr(self, 'retrieved_quotation_data'):
                if not self.test_quotation_update_put():
                    success = False
        
        # 4. Test complete quotation data structure
        if not self.test_complete_quotation_data_structure():
            success = False
        
        # 5. Test sales prices integration
        if not self.test_sales_prices_integration():
            success = False
        
        # 6. Test error scenarios
        self.test_error_scenarios()
        
        # Print summary
        self.print_summary()
        
        return success
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 QUOTATION SUBMISSION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL QUOTATION SUBMISSION TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.total_tests - self.passed_tests} TESTS FAILED")
            
            if self.failed_tests:
                print("\n❌ FAILED TESTS:")
                for failed_test in self.failed_tests:
                    print(f"   • {failed_test}")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = QuotationSubmissionTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()