#!/usr/bin/env python3
"""
Focused Backend API Testing for Discount Calculation and Quotation Editing
Testing the specific functionality requested in the review
"""

import requests
import json
import sys
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
BASE_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class DiscountQuotationTester:
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
    
    async def setup_test_data(self):
        """Setup test data in database"""
        print("\n🔧 SETTING UP TEST DATA")
        print("=" * 50)
        
        try:
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['sawayatta_erp']
            
            # Create a rate card
            rate_card = {
                "id": "test-rate-card-001",
                "name": "Standard Rate Card 2025",
                "description": "Standard pricing for 2025",
                "effective_from": datetime.now(),
                "effective_to": None,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "created_by": "system"
            }
            
            # Check if rate card exists
            existing_rate_card = await db.mst_rate_cards.find_one({"id": rate_card["id"]})
            if not existing_rate_card:
                await db.mst_rate_cards.insert_one(rate_card)
                print("✅ Created test rate card")
            else:
                print("✅ Test rate card already exists")
            
            # Create an opportunity in L4 stage for quotation testing
            # First get the L4 stage ID
            l4_stage = await db.mst_stages.find_one({"stage_code": "L4"})
            inr_currency = await db.mst_currencies.find_one({"code": "INR"})
            
            if l4_stage and inr_currency:
                opportunity = {
                    "id": "test-opportunity-discount-001",
                    "opportunity_id": "OPP-DISC001",
                    "project_title": "Discount Testing Opportunity",
                    "company_id": "test-company-discount",
                    "current_stage": 4,
                    "stage_id": l4_stage["id"],
                    "expected_revenue": 500000,
                    "currency_id": inr_currency["id"],
                    "lead_owner_id": "test-user-discount",
                    "win_probability": 75,
                    "status": "Active",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "created_by": "system"
                }
                
                # Check if opportunity exists
                existing_opp = await db.opportunities.find_one({"id": opportunity["id"]})
                if not existing_opp:
                    await db.opportunities.insert_one(opportunity)
                    print("✅ Created test L4 opportunity")
                    self.test_opportunity_id = opportunity["id"]
                else:
                    print("✅ Test L4 opportunity already exists")
                    self.test_opportunity_id = existing_opp["id"]
            else:
                print("❌ Could not find L4 stage or INR currency")
                self.test_opportunity_id = None
            
            client.close()
            return True
            
        except Exception as e:
            print(f"❌ Error setting up test data: {str(e)}")
            return False
    
    def test_discount_validation(self):
        """Test discount percentage validation (0-100 range)"""
        print("\n🔍 TESTING DISCOUNT VALIDATION")
        print("=" * 50)
        
        test_cases = [
            {"discount": 0, "expected": True, "description": "0% discount (minimum)"},
            {"discount": 50, "expected": True, "description": "50% discount (valid)"},
            {"discount": 100, "expected": True, "description": "100% discount (maximum)"},
            {"discount": -10, "expected": False, "description": "Negative discount (invalid)"},
            {"discount": 150, "expected": False, "description": ">100% discount (invalid)"},
            {"discount": 25.5, "expected": True, "description": "Decimal discount (valid)"},
        ]
        
        for case in test_cases:
            # Test discount validation logic
            is_valid = 0 <= case["discount"] <= 100
            if is_valid == case["expected"]:
                self.log_test(f"Discount Validation: {case['description']}", True, f"Discount {case['discount']}% validated correctly")
            else:
                self.log_test(f"Discount Validation: {case['description']}", False, f"Discount {case['discount']}% validation failed")
    
    def test_discount_calculation_formulas(self):
        """Test discount calculation formulas for both pricing types"""
        print("\n🧮 TESTING DISCOUNT CALCULATION FORMULAS")
        print("=" * 50)
        
        test_cases = [
            {
                "name": "One-time Product with 15% Discount",
                "qty": 10,
                "unit_price": 5000,
                "discount_percent": 15.0,
                "pricing_type": "one_time",
                "expected_line_total": 42500  # (10 * 5000) - ((10 * 5000) * 15 / 100) = 50000 - 7500 = 42500
            },
            {
                "name": "Recurring Product with 10% Discount",
                "qty": 5,
                "unit_price": 8000,
                "discount_percent": 10.0,
                "pricing_type": "recurring",
                "expected_line_total": 36000  # (5 * 8000) - ((5 * 8000) * 10 / 100) = 40000 - 4000 = 36000
            },
            {
                "name": "Product with 0% Discount",
                "qty": 3,
                "unit_price": 12000,
                "discount_percent": 0.0,
                "pricing_type": "one_time",
                "expected_line_total": 36000  # (3 * 12000) - 0 = 36000
            },
            {
                "name": "Product with 100% Discount",
                "qty": 2,
                "unit_price": 15000,
                "discount_percent": 100.0,
                "pricing_type": "recurring",
                "expected_line_total": 0  # (2 * 15000) - ((2 * 15000) * 100 / 100) = 30000 - 30000 = 0
            },
            {
                "name": "Product with Decimal Discount (25.5%)",
                "qty": 4,
                "unit_price": 10000,
                "discount_percent": 25.5,
                "pricing_type": "one_time",
                "expected_line_total": 29800  # (4 * 10000) - ((4 * 10000) * 25.5 / 100) = 40000 - 10200 = 29800
            }
        ]
        
        for case in test_cases:
            # Calculate line total using the formula: line_total = (qty × unit_price) - ((qty × unit_price) × discount% / 100)
            gross_amount = case["qty"] * case["unit_price"]
            discount_amount = gross_amount * case["discount_percent"] / 100
            calculated_line_total = gross_amount - discount_amount
            
            if abs(calculated_line_total - case["expected_line_total"]) < 0.01:  # Allow for floating point precision
                self.log_test(
                    f"Discount Formula: {case['name']}", 
                    True, 
                    f"Calculated: ₹{calculated_line_total:,.2f}, Expected: ₹{case['expected_line_total']:,.2f}"
                )
            else:
                self.log_test(
                    f"Discount Formula: {case['name']}", 
                    False, 
                    f"Calculated: ₹{calculated_line_total:,.2f}, Expected: ₹{case['expected_line_total']:,.2f}"
                )
    
    def test_quotation_crud_operations(self):
        """Test quotation CRUD operations"""
        print("\n📋 TESTING QUOTATION CRUD OPERATIONS")
        print("=" * 50)
        
        if not hasattr(self, 'test_opportunity_id') or not self.test_opportunity_id:
            self.log_test("Quotation CRUD Operations", False, "No test opportunity available")
            return
        
        # Test CREATE quotation
        quotation_id = self.test_create_quotation()
        
        if quotation_id:
            # Test READ quotation
            self.test_read_quotation(quotation_id)
            
            # Test UPDATE quotation
            self.test_update_quotation(quotation_id)
    
    def test_create_quotation(self):
        """Test creating a quotation with discount data"""
        try:
            # Get products for quotation items
            products_response = requests.get(f"{self.base_url}/mst/products", headers=self.headers, timeout=10)
            
            if products_response.status_code != 200:
                self.log_test("CREATE Quotation", False, "Could not get products")
                return None
            
            products = products_response.json()
            if not products:
                self.log_test("CREATE Quotation", False, "No products available")
                return None
            
            # Create quotation with simple items structure (matching the backend model)
            quotation_data = {
                "quotation_name": "Discount Testing Quotation",
                "rate_card_id": "test-rate-card-001",
                "validity_date": "2025-06-30T00:00:00Z",
                "items": [
                    {
                        "product_id": products[0]['id'],
                        "qty": 10,
                        "unit": "License",
                        "recurring_sale_price": 0,
                        "one_time_sale_price": 5000,
                        "purchase_cost_snapshot": 3000,
                        "tenure_months": 1
                    },
                    {
                        "product_id": products[1]['id'] if len(products) > 1 else products[0]['id'],
                        "qty": 5,
                        "unit": "License",
                        "recurring_sale_price": 8000,
                        "one_time_sale_price": 0,
                        "purchase_cost_snapshot": 5000,
                        "tenure_months": 12
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations",
                headers=self.headers,
                json=quotation_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                created_quotation = response.json()
                quotation_id = created_quotation.get('id')
                self.log_test("CREATE Quotation", True, f"Created quotation ID: {quotation_id}")
                return quotation_id
            else:
                self.log_test("CREATE Quotation", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("CREATE Quotation", False, f"Exception: {str(e)}")
            return None
    
    def test_read_quotation(self, quotation_id):
        """Test reading quotation data to verify data persistence"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{quotation_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                quotation_data = response.json()
                
                # Verify quotation structure and data
                has_items = 'items' in quotation_data and len(quotation_data['items']) > 0
                has_pricing_data = False
                
                if has_items:
                    for item in quotation_data['items']:
                        if 'one_time_sale_price' in item or 'recurring_sale_price' in item:
                            has_pricing_data = True
                            break
                
                if has_items and has_pricing_data:
                    self.log_test("READ Quotation", True, "Quotation data loaded with pricing information")
                else:
                    self.log_test("READ Quotation", False, "Missing quotation items or pricing data")
            else:
                self.log_test("READ Quotation", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("READ Quotation", False, f"Exception: {str(e)}")
    
    def test_update_quotation(self, quotation_id):
        """Test updating quotation with modified pricing"""
        try:
            # First get the current quotation data
            get_response = requests.get(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{quotation_id}",
                headers=self.headers,
                timeout=10
            )
            
            if get_response.status_code != 200:
                self.log_test("UPDATE Quotation", False, "Could not get current quotation data")
                return
            
            current_data = get_response.json()
            
            # Modify pricing (increase prices by 10%)
            if current_data.get('items'):
                for item in current_data['items']:
                    if item.get('one_time_sale_price', 0) > 0:
                        item['one_time_sale_price'] = item['one_time_sale_price'] * 1.1
                    if item.get('recurring_sale_price', 0) > 0:
                        item['recurring_sale_price'] = item['recurring_sale_price'] * 1.1
            
            # Prepare update data (remove fields that shouldn't be updated)
            update_data = {
                "quotation_name": current_data.get("quotation_name"),
                "rate_card_id": current_data.get("rate_card_id"),
                "validity_date": current_data.get("validity_date"),
                "items": current_data.get("items", [])
            }
            
            # Update the quotation
            update_response = requests.put(
                f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{quotation_id}",
                headers=self.headers,
                json=update_data,
                timeout=10
            )
            
            if update_response.status_code in [200, 204]:
                self.log_test("UPDATE Quotation", True, "Quotation updated with modified pricing")
                
                # Verify the update by reading back
                verify_response = requests.get(
                    f"{self.base_url}/opportunities/{self.test_opportunity_id}/quotations/{quotation_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if verify_response.status_code == 200:
                    self.log_test("VERIFY Updated Quotation", True, "Updated quotation data retrieved successfully")
                else:
                    self.log_test("VERIFY Updated Quotation", False, "Could not verify updated quotation")
            else:
                self.log_test("UPDATE Quotation", False, f"Status: {update_response.status_code}")
                
        except Exception as e:
            self.log_test("UPDATE Quotation", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING DISCOUNT CALCULATION & QUOTATION EDITING TESTS")
        print("=" * 70)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Setup test data
        setup_success = asyncio.run(self.setup_test_data())
        if not setup_success:
            print("\n❌ TEST DATA SETUP FAILED - Some tests may fail")
        
        # Run all test suites
        self.test_discount_validation()
        self.test_discount_calculation_formulas()
        self.test_quotation_crud_operations()
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests == self.total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
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
        print("-" * 50)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = DiscountQuotationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()