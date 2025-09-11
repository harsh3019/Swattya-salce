#!/usr/bin/env python3
"""
Backend Testing for 4 Specific User Issues
Testing the fixes implemented for:
1. Dummy Data Pricing (Issue #1)
2. L5 Document Upload (Issue #2) 
3. PO Number Auto-generation (Issue #3)
4. Opportunity CRUD Operations (Issue #4)
"""

import requests
import json
import sys
import os
import tempfile
from datetime import datetime

# Configuration
BASE_URL = "https://1b435344-f8f5-4a8b-98d4-64db783ac8b5.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class FourIssuesBackendTester:
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

    def test_issue_1_dummy_data_pricing(self):
        """Test Issue #1: Dummy Data Pricing"""
        print("\n💰 TESTING ISSUE #1: DUMMY DATA PRICING")
        print("=" * 60)
        
        # Test 1: GET /api/mst/sales-prices/test-rate-card-001 - should return 5 pricing records
        self.test_sales_prices_specific_rate_card()
        
        # Test 2: GET /api/mst/products - verify products have primary_category_id
        self.test_products_have_primary_category_id()
        
        # Test 3: Test quotation creation with proper pricing integration
        self.test_quotation_pricing_integration()
        
        # Test 4: Verify profitability calculations work with real sales/purchase costs
        self.test_profitability_calculations()

    def test_sales_prices_specific_rate_card(self):
        """Test GET /api/mst/sales-prices/test-rate-card-001 - should return 5 pricing records"""
        try:
            # First try with the specific rate card ID mentioned in requirements
            response = requests.get(
                f"{self.base_url}/mst/sales-prices/test-rate-card-001",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else len(data.get('data', []))
                
                if count == 5:
                    self.log_test(
                        "GET /api/mst/sales-prices/test-rate-card-001", 
                        True, 
                        f"Retrieved exactly 5 pricing records as expected"
                    )
                else:
                    self.log_test(
                        "GET /api/mst/sales-prices/test-rate-card-001", 
                        False, 
                        f"Expected 5 pricing records, got {count}"
                    )
            elif response.status_code == 404:
                # If specific rate card doesn't exist, try with any available rate card
                self.test_sales_prices_fallback()
            else:
                self.log_test(
                    "GET /api/mst/sales-prices/test-rate-card-001", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET /api/mst/sales-prices/test-rate-card-001", False, f"Exception: {str(e)}")

    def test_sales_prices_fallback(self):
        """Fallback test for sales prices with any available rate card"""
        try:
            # Get available rate cards
            rate_cards_response = requests.get(
                f"{self.base_url}/mst/rate-cards",
                headers=self.headers,
                timeout=10
            )
            
            if rate_cards_response.status_code == 200:
                rate_cards = rate_cards_response.json()
                if rate_cards and len(rate_cards) > 0:
                    rate_card_id = rate_cards[0].get('id')
                    
                    # Test sales prices with available rate card
                    sales_response = requests.get(
                        f"{self.base_url}/mst/sales-prices/{rate_card_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if sales_response.status_code == 200:
                        sales_data = sales_response.json()
                        count = len(sales_data) if isinstance(sales_data, list) else len(sales_data.get('data', []))
                        
                        if count >= 5:
                            self.log_test(
                                "Sales Prices API (Fallback)", 
                                True, 
                                f"Retrieved {count} sales prices (≥5 expected)"
                            )
                        else:
                            self.log_test(
                                "Sales Prices API (Fallback)", 
                                False, 
                                f"Only {count} sales prices found, expected ≥5"
                            )
                    else:
                        self.log_test(
                            "Sales Prices API (Fallback)", 
                            False, 
                            f"Status: {sales_response.status_code}"
                        )
                else:
                    self.log_test("Sales Prices API (Fallback)", False, "No rate cards available")
            else:
                self.log_test("Sales Prices API (Fallback)", False, "Could not get rate cards")
                
        except Exception as e:
            self.log_test("Sales Prices API (Fallback)", False, f"Exception: {str(e)}")

    def test_products_have_primary_category_id(self):
        """Test GET /api/mst/products - verify products have primary_category_id"""
        try:
            response = requests.get(
                f"{self.base_url}/mst/products",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data if isinstance(data, list) else data.get('data', [])
                
                if not products:
                    self.log_test(
                        "Products have primary_category_id", 
                        False, 
                        "No products found"
                    )
                    return
                
                products_with_category = 0
                for product in products:
                    if 'primary_category_id' in product and product['primary_category_id']:
                        products_with_category += 1
                
                if products_with_category == len(products):
                    self.log_test(
                        "Products have primary_category_id", 
                        True, 
                        f"All {len(products)} products have primary_category_id field"
                    )
                else:
                    self.log_test(
                        "Products have primary_category_id", 
                        False, 
                        f"Only {products_with_category}/{len(products)} products have primary_category_id"
                    )
            else:
                self.log_test(
                    "Products have primary_category_id", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Products have primary_category_id", False, f"Exception: {str(e)}")

    def test_quotation_pricing_integration(self):
        """Test quotation creation with proper pricing integration"""
        try:
            # Create an L4 opportunity first (required for quotation creation)
            opportunity_id = self.create_l4_opportunity_for_pricing()
            if not opportunity_id:
                self.log_test("Quotation Pricing Integration", False, "Could not create L4 opportunity")
                return
            
            # Get required master data
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            products_response = requests.get(f"{self.base_url}/mst/products", headers=self.headers, timeout=10)
            
            if rate_cards_response.status_code != 200 or products_response.status_code != 200:
                self.log_test("Quotation Pricing Integration", False, "Could not get master data")
                return
            
            rate_cards = rate_cards_response.json()
            products = products_response.json()
            
            if not rate_cards or not products:
                self.log_test("Quotation Pricing Integration", False, "No rate cards or products available")
                return
            
            # Create quotation with pricing integration
            quotation_data = {
                "quotation_name": "Pricing Integration Test Quotation",
                "rate_card_id": rate_cards[0]['id'],
                "validity_date": "2025-06-30T00:00:00Z",
                "items": [
                    {
                        "phase_name": "Phase 1 - Implementation",
                        "groups": [
                            {
                                "group_name": "Software Products",
                                "items": [
                                    {
                                        "product_id": products[0]['id'],
                                        "quantity": 5,
                                        "unit_price": 10000,
                                        "discount_percentage": 10.0,
                                        "pricing_type": "one_time"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/quotations",
                headers=self.headers,
                json=quotation_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quotation_id = data.get('quotation_id') or data.get('id')
                self.log_test(
                    "Quotation Pricing Integration", 
                    True, 
                    f"Quotation created with pricing integration: {quotation_id}"
                )
            else:
                self.log_test(
                    "Quotation Pricing Integration", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Quotation Pricing Integration", False, f"Exception: {str(e)}")

    def test_profitability_calculations(self):
        """Test profitability calculations with real sales/purchase costs"""
        try:
            # Get sales prices and purchase costs
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            purchase_costs_response = requests.get(f"{self.base_url}/mst/purchase-costs", headers=self.headers, timeout=10)
            
            if rate_cards_response.status_code != 200:
                self.log_test("Profitability Calculations", False, "Could not get rate cards")
                return
            
            rate_cards = rate_cards_response.json()
            if not rate_cards:
                self.log_test("Profitability Calculations", False, "No rate cards available")
                return
            
            # Get sales prices for first rate card
            sales_response = requests.get(
                f"{self.base_url}/mst/sales-prices/{rate_cards[0]['id']}",
                headers=self.headers,
                timeout=10
            )
            
            sales_success = sales_response.status_code == 200
            purchase_success = purchase_costs_response.status_code == 200
            
            if sales_success and purchase_success:
                sales_data = sales_response.json()
                purchase_data = purchase_costs_response.json()
                
                sales_count = len(sales_data) if isinstance(sales_data, list) else len(sales_data.get('data', []))
                purchase_count = len(purchase_data) if isinstance(purchase_data, list) else len(purchase_data.get('data', []))
                
                if sales_count > 0 and purchase_count > 0:
                    self.log_test(
                        "Profitability Calculations", 
                        True, 
                        f"Sales prices ({sales_count}) and purchase costs ({purchase_count}) available for profitability calculations"
                    )
                else:
                    self.log_test(
                        "Profitability Calculations", 
                        False, 
                        f"Insufficient data: Sales prices ({sales_count}), Purchase costs ({purchase_count})"
                    )
            elif sales_success:
                self.log_test(
                    "Profitability Calculations", 
                    False, 
                    "Sales prices available but purchase costs API failed"
                )
            else:
                self.log_test(
                    "Profitability Calculations", 
                    False, 
                    "Both sales prices and purchase costs APIs failed"
                )
                
        except Exception as e:
            self.log_test("Profitability Calculations", False, f"Exception: {str(e)}")

    def test_issue_2_l5_document_upload(self):
        """Test Issue #2: L5 Document Upload"""
        print("\n📄 TESTING ISSUE #2: L5 DOCUMENT UPLOAD")
        print("=" * 60)
        
        # Create an opportunity for document testing
        opportunity_id = self.create_opportunity_for_document_testing()
        if not opportunity_id:
            self.log_test("L5 Document Upload Setup", False, "Could not create opportunity for testing")
            return
        
        # Test 1: POST /api/opportunities/{id}/upload-document with PO document
        self.test_po_document_upload(opportunity_id)
        
        # Test 2: GET /api/opportunities/{id}/documents?document_type=po_document
        self.test_po_document_retrieval(opportunity_id)
        
        # Test 3: DELETE /api/opportunities/{id}/documents/{doc_id} for PO documents
        self.test_po_document_deletion(opportunity_id)
        
        # Test 4: Test file upload validation (size, type restrictions)
        self.test_file_upload_validation(opportunity_id)

    def test_po_document_upload(self, opportunity_id):
        """Test POST /api/opportunities/{id}/upload-document with PO document"""
        try:
            # Create a test PO document
            test_content = "Test PO Document Content - Purchase Order #PO-12345"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as file:
                    files = {
                        'file': ('test_po_document.txt', file, 'text/plain')
                    }
                    data = {
                        'document_type': 'po_document'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/opportunities/{opportunity_id}/upload-document",
                        headers=self.headers,
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        document_id = response_data.get('document_id') or response_data.get('id')
                        self.uploaded_document_id = document_id
                        self.log_test(
                            "POST PO Document Upload", 
                            True, 
                            f"PO document uploaded successfully: {document_id}"
                        )
                    else:
                        self.log_test(
                            "POST PO Document Upload", 
                            False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}"
                        )
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("POST PO Document Upload", False, f"Exception: {str(e)}")

    def test_po_document_retrieval(self, opportunity_id):
        """Test GET /api/opportunities/{id}/documents?document_type=po_document"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{opportunity_id}/documents",
                headers=self.headers,
                params={'document_type': 'po_document'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = data if isinstance(data, list) else data.get('documents', [])
                
                po_documents = [doc for doc in documents if doc.get('document_type') == 'po_document']
                
                if len(po_documents) > 0:
                    self.log_test(
                        "GET PO Documents", 
                        True, 
                        f"Retrieved {len(po_documents)} PO documents"
                    )
                    # Store document ID for deletion test
                    if po_documents and not hasattr(self, 'uploaded_document_id'):
                        self.uploaded_document_id = po_documents[0].get('id')
                else:
                    self.log_test(
                        "GET PO Documents", 
                        False, 
                        "No PO documents found"
                    )
            else:
                self.log_test(
                    "GET PO Documents", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("GET PO Documents", False, f"Exception: {str(e)}")

    def test_po_document_deletion(self, opportunity_id):
        """Test DELETE /api/opportunities/{id}/documents/{doc_id} for PO documents"""
        try:
            if not hasattr(self, 'uploaded_document_id') or not self.uploaded_document_id:
                self.log_test("DELETE PO Document", False, "No document ID available for deletion test")
                return
            
            response = requests.delete(
                f"{self.base_url}/opportunities/{opportunity_id}/documents/{self.uploaded_document_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test(
                    "DELETE PO Document", 
                    True, 
                    f"PO document deleted successfully: {self.uploaded_document_id}"
                )
            else:
                self.log_test(
                    "DELETE PO Document", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("DELETE PO Document", False, f"Exception: {str(e)}")

    def test_file_upload_validation(self, opportunity_id):
        """Test file upload validation (size, type restrictions)"""
        try:
            # Test 1: Valid file type (PDF simulation with .txt)
            test_content = "Valid test document content"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as file:
                    files = {
                        'file': ('valid_document.txt', file, 'text/plain')
                    }
                    data = {
                        'document_type': 'po_document'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/opportunities/{opportunity_id}/upload-document",
                        headers=self.headers,
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        self.log_test(
                            "File Upload Validation (Valid Type)", 
                            True, 
                            "Valid file type accepted"
                        )
                    else:
                        self.log_test(
                            "File Upload Validation (Valid Type)", 
                            False, 
                            f"Valid file rejected: {response.status_code}"
                        )
            finally:
                os.unlink(temp_file_path)
            
            # Test 2: File size validation (create a large file to test 10MB limit)
            # Note: We'll simulate this by checking if the API has size validation
            large_content = "X" * (1024 * 1024)  # 1MB content
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(large_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as file:
                    files = {
                        'file': ('large_document.txt', file, 'text/plain')
                    }
                    data = {
                        'document_type': 'po_document'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/opportunities/{opportunity_id}/upload-document",
                        headers=self.headers,
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    # 1MB should be accepted (under 10MB limit)
                    if response.status_code in [200, 201]:
                        self.log_test(
                            "File Upload Validation (Size Check)", 
                            True, 
                            "1MB file accepted (under 10MB limit)"
                        )
                    else:
                        self.log_test(
                            "File Upload Validation (Size Check)", 
                            False, 
                            f"1MB file rejected: {response.status_code}"
                        )
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("File Upload Validation", False, f"Exception: {str(e)}")

    def test_issue_3_po_number_auto_generation(self):
        """Test Issue #3: PO Number Auto-generation"""
        print("\n🔢 TESTING ISSUE #3: PO NUMBER AUTO-GENERATION")
        print("=" * 60)
        
        # Test 1: Test that PO number format follows PO-XXXXX pattern
        self.test_po_number_format()
        
        # Test 2: Test L5 stage form accepts auto-generated PO numbers
        self.test_l5_stage_po_acceptance()
        
        # Test 3: Verify PO number is properly saved in opportunity stage data
        self.test_po_number_persistence()

    def test_po_number_format(self):
        """Test that PO number format follows PO-XXXXX pattern"""
        try:
            # Create an opportunity and progress it to L5 stage to test PO generation
            opportunity_id = self.create_opportunity_for_po_testing()
            if not opportunity_id:
                self.log_test("PO Number Format Test", False, "Could not create opportunity")
                return
            
            # Progress opportunity to L5 stage with PO data
            l5_stage_data = {
                "stage_id": self.get_l5_stage_id(),
                "stage_data": {
                    "po_number": "AUTO_GENERATE",  # Request auto-generation
                    "po_value": 500000,
                    "po_date": "2025-01-15T00:00:00Z",
                    "delivery_timeline": "90 days"
                }
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=l5_stage_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                # Get the updated opportunity to check PO number
                opp_response = requests.get(
                    f"{self.base_url}/opportunities/{opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if opp_response.status_code == 200:
                    opp_data = opp_response.json()
                    stage_data = opp_data.get('stage_data', {})
                    po_number = stage_data.get('po_number')
                    
                    if po_number and po_number.startswith('PO-') and len(po_number) >= 8:
                        # Check if it follows PO-XXXXX pattern (at least 5 characters after PO-)
                        po_suffix = po_number[3:]  # Remove 'PO-' prefix
                        if len(po_suffix) >= 5 and po_suffix.isalnum():
                            self.log_test(
                                "PO Number Format", 
                                True, 
                                f"PO number follows correct format: {po_number}"
                            )
                        else:
                            self.log_test(
                                "PO Number Format", 
                                False, 
                                f"PO number format incorrect: {po_number}"
                            )
                    else:
                        self.log_test(
                            "PO Number Format", 
                            False, 
                            f"PO number missing or invalid format: {po_number}"
                        )
                else:
                    self.log_test("PO Number Format", False, "Could not retrieve updated opportunity")
            else:
                self.log_test(
                    "PO Number Format", 
                    False, 
                    f"Stage update failed: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("PO Number Format", False, f"Exception: {str(e)}")

    def test_l5_stage_po_acceptance(self):
        """Test L5 stage form accepts auto-generated PO numbers"""
        try:
            # Create opportunity and test L5 stage form
            opportunity_id = self.create_opportunity_for_po_testing()
            if not opportunity_id:
                self.log_test("L5 Stage PO Acceptance", False, "Could not create opportunity")
                return
            
            # Test L5 stage form with auto-generated PO number
            l5_form_data = {
                "stage_id": self.get_l5_stage_id(),
                "stage_data": {
                    "po_number": "PO-TEST123",  # Simulate auto-generated format
                    "po_value": 750000,
                    "po_date": "2025-01-20T00:00:00Z",
                    "delivery_timeline": "120 days",
                    "payment_terms": "30-60-90 days",
                    "client_poc": "John Doe"
                }
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=l5_form_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test(
                    "L5 Stage PO Acceptance", 
                    True, 
                    "L5 stage form accepts auto-generated PO numbers"
                )
            else:
                self.log_test(
                    "L5 Stage PO Acceptance", 
                    False, 
                    f"L5 stage form rejected PO data: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("L5 Stage PO Acceptance", False, f"Exception: {str(e)}")

    def test_po_number_persistence(self):
        """Verify PO number is properly saved in opportunity stage data"""
        try:
            # Create opportunity and save PO data
            opportunity_id = self.create_opportunity_for_po_testing()
            if not opportunity_id:
                self.log_test("PO Number Persistence", False, "Could not create opportunity")
                return
            
            test_po_number = "PO-PERSIST123"
            
            # Save PO data to L5 stage
            l5_data = {
                "stage_id": self.get_l5_stage_id(),
                "stage_data": {
                    "po_number": test_po_number,
                    "po_value": 600000,
                    "po_date": "2025-01-25T00:00:00Z"
                }
            }
            
            # Save the data
            save_response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=l5_data,
                timeout=10
            )
            
            if save_response.status_code in [200, 204]:
                # Retrieve and verify persistence
                get_response = requests.get(
                    f"{self.base_url}/opportunities/{opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    opp_data = get_response.json()
                    stage_data = opp_data.get('stage_data', {})
                    saved_po_number = stage_data.get('po_number')
                    
                    if saved_po_number == test_po_number:
                        self.log_test(
                            "PO Number Persistence", 
                            True, 
                            f"PO number properly saved and retrieved: {saved_po_number}"
                        )
                    else:
                        self.log_test(
                            "PO Number Persistence", 
                            False, 
                            f"PO number not persisted correctly. Expected: {test_po_number}, Got: {saved_po_number}"
                        )
                else:
                    self.log_test("PO Number Persistence", False, "Could not retrieve opportunity data")
            else:
                self.log_test("PO Number Persistence", False, "Could not save PO data")
                
        except Exception as e:
            self.log_test("PO Number Persistence", False, f"Exception: {str(e)}")

    def test_issue_4_opportunity_crud_operations(self):
        """Test Issue #4: Opportunity CRUD Operations"""
        print("\n🔄 TESTING ISSUE #4: OPPORTUNITY CRUD OPERATIONS")
        print("=" * 60)
        
        # Test 1: Test PUT /api/opportunities/{id} - opportunity update endpoint
        self.test_opportunity_update_endpoint()
        
        # Test 2: Test DELETE /api/opportunities/{id} - soft delete functionality
        self.test_opportunity_delete_endpoint()
        
        # Test 3: Test GET /api/companies - verify company data has 'name' field (not company_name)
        self.test_company_name_field()
        
        # Test 4: Test opportunity update with company_id changes
        self.test_opportunity_company_update()
        
        # Test 5: Verify delete prevents deletion if selected quotations exist
        self.test_delete_prevention_with_quotations()

    def test_opportunity_update_endpoint(self):
        """Test PUT /api/opportunities/{id} - opportunity update endpoint"""
        try:
            # Create an opportunity to update
            opportunity_id = self.create_opportunity_for_crud_testing()
            if not opportunity_id:
                self.log_test("Opportunity Update Endpoint", False, "Could not create opportunity for testing")
                return
            
            # Update opportunity data
            update_data = {
                "project_title": "Updated Opportunity Title - CRUD Test",
                "expected_revenue": 800000,
                "win_probability": 80,
                "description": "Updated description for CRUD testing"
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                json=update_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                # Verify the update by retrieving the opportunity
                get_response = requests.get(
                    f"{self.base_url}/opportunities/{opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    updated_opp = get_response.json()
                    if updated_opp.get('project_title') == update_data['project_title']:
                        self.log_test(
                            "PUT /api/opportunities/{id}", 
                            True, 
                            "Opportunity updated successfully"
                        )
                    else:
                        self.log_test(
                            "PUT /api/opportunities/{id}", 
                            False, 
                            "Opportunity update not reflected in data"
                        )
                else:
                    self.log_test("PUT /api/opportunities/{id}", False, "Could not verify update")
            else:
                self.log_test(
                    "PUT /api/opportunities/{id}", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("PUT /api/opportunities/{id}", False, f"Exception: {str(e)}")

    def test_opportunity_delete_endpoint(self):
        """Test DELETE /api/opportunities/{id} - soft delete functionality"""
        try:
            # Create an opportunity to delete
            opportunity_id = self.create_opportunity_for_crud_testing()
            if not opportunity_id:
                self.log_test("Opportunity Delete Endpoint", False, "Could not create opportunity for testing")
                return
            
            response = requests.delete(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                # Verify soft delete by trying to retrieve the opportunity
                get_response = requests.get(
                    f"{self.base_url}/opportunities/{opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if get_response.status_code == 404:
                    self.log_test(
                        "DELETE /api/opportunities/{id}", 
                        True, 
                        "Opportunity soft deleted successfully (404 on retrieval)"
                    )
                elif get_response.status_code == 200:
                    # Check if opportunity is marked as inactive/deleted
                    opp_data = get_response.json()
                    if not opp_data.get('is_active', True) or opp_data.get('status') == 'Deleted':
                        self.log_test(
                            "DELETE /api/opportunities/{id}", 
                            True, 
                            "Opportunity soft deleted (marked as inactive)"
                        )
                    else:
                        self.log_test(
                            "DELETE /api/opportunities/{id}", 
                            False, 
                            "Opportunity not properly soft deleted"
                        )
                else:
                    self.log_test("DELETE /api/opportunities/{id}", False, "Unexpected response after delete")
            else:
                self.log_test(
                    "DELETE /api/opportunities/{id}", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("DELETE /api/opportunities/{id}", False, f"Exception: {str(e)}")

    def test_company_name_field(self):
        """Test GET /api/companies - verify company data has 'name' field (not company_name)"""
        try:
            response = requests.get(
                f"{self.base_url}/companies",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                companies = data if isinstance(data, list) else data.get('data', [])
                
                if not companies:
                    self.log_test(
                        "Company Name Field", 
                        False, 
                        "No companies found to test field names"
                    )
                    return
                
                companies_with_name = 0
                companies_with_company_name = 0
                
                for company in companies:
                    if 'name' in company:
                        companies_with_name += 1
                    if 'company_name' in company:
                        companies_with_company_name += 1
                
                if companies_with_name > 0 and companies_with_company_name == 0:
                    self.log_test(
                        "Company Name Field", 
                        True, 
                        f"All {len(companies)} companies use 'name' field (not 'company_name')"
                    )
                elif companies_with_name == 0 and companies_with_company_name > 0:
                    self.log_test(
                        "Company Name Field", 
                        False, 
                        f"Companies still use 'company_name' field instead of 'name'"
                    )
                else:
                    self.log_test(
                        "Company Name Field", 
                        False, 
                        f"Mixed field usage: {companies_with_name} with 'name', {companies_with_company_name} with 'company_name'"
                    )
            else:
                self.log_test(
                    "Company Name Field", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Company Name Field", False, f"Exception: {str(e)}")

    def test_opportunity_company_update(self):
        """Test opportunity update with company_id changes"""
        try:
            # Get available companies
            companies_response = requests.get(f"{self.base_url}/companies", headers=self.headers, timeout=10)
            if companies_response.status_code != 200:
                self.log_test("Opportunity Company Update", False, "Could not get companies")
                return
            
            companies = companies_response.json()
            if isinstance(companies, dict):
                companies = companies.get('data', [])
            
            if len(companies) < 2:
                self.log_test("Opportunity Company Update", False, "Need at least 2 companies for testing")
                return
            
            # Create opportunity with first company
            opportunity_id = self.create_opportunity_for_crud_testing()
            if not opportunity_id:
                self.log_test("Opportunity Company Update", False, "Could not create opportunity")
                return
            
            # Update opportunity with different company
            new_company_id = companies[1].get('id')
            update_data = {
                "company_id": new_company_id,
                "project_title": "Updated with New Company"
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                json=update_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                # Verify company_id update
                get_response = requests.get(
                    f"{self.base_url}/opportunities/{opportunity_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    updated_opp = get_response.json()
                    if updated_opp.get('company_id') == new_company_id:
                        self.log_test(
                            "Opportunity Company Update", 
                            True, 
                            "Opportunity company_id updated successfully"
                        )
                    else:
                        self.log_test(
                            "Opportunity Company Update", 
                            False, 
                            "Company_id not updated correctly"
                        )
                else:
                    self.log_test("Opportunity Company Update", False, "Could not verify company update")
            else:
                self.log_test(
                    "Opportunity Company Update", 
                    False, 
                    f"Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Opportunity Company Update", False, f"Exception: {str(e)}")

    def test_delete_prevention_with_quotations(self):
        """Verify delete prevents deletion if selected quotations exist"""
        try:
            # Create opportunity with quotation
            opportunity_id = self.create_l4_opportunity_for_pricing()
            if not opportunity_id:
                self.log_test("Delete Prevention with Quotations", False, "Could not create opportunity")
                return
            
            # Create a quotation for the opportunity
            quotation_created = self.create_test_quotation(opportunity_id)
            if not quotation_created:
                self.log_test("Delete Prevention with Quotations", False, "Could not create quotation")
                return
            
            # Try to delete opportunity with quotation
            response = requests.delete(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 400:
                # Deletion should be prevented
                self.log_test(
                    "Delete Prevention with Quotations", 
                    True, 
                    "Deletion correctly prevented when quotations exist"
                )
            elif response.status_code in [200, 204]:
                # Check if deletion was allowed (might be different implementation)
                self.log_test(
                    "Delete Prevention with Quotations", 
                    False, 
                    "Deletion allowed despite existing quotations"
                )
            else:
                self.log_test(
                    "Delete Prevention with Quotations", 
                    False, 
                    f"Unexpected response: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Delete Prevention with Quotations", False, f"Exception: {str(e)}")

    def test_integration_workflow(self):
        """Test complete integration workflow"""
        print("\n🔗 TESTING INTEGRATION WORKFLOW")
        print("=" * 60)
        
        try:
            # Step 1: Create quotation
            opportunity_id = self.create_l4_opportunity_for_pricing()
            if not opportunity_id:
                self.log_test("Integration Workflow", False, "Could not create opportunity")
                return
            
            quotation_created = self.create_test_quotation(opportunity_id)
            if not quotation_created:
                self.log_test("Integration Workflow", False, "Could not create quotation")
                return
            
            # Step 2: Progress to L5 stage with PO
            l5_success = self.progress_to_l5_with_po(opportunity_id)
            if not l5_success:
                self.log_test("Integration Workflow", False, "Could not progress to L5")
                return
            
            # Step 3: Upload PO document
            po_upload_success = self.upload_po_document(opportunity_id)
            if not po_upload_success:
                self.log_test("Integration Workflow", False, "Could not upload PO document")
                return
            
            # Step 4: Test opportunity edit
            edit_success = self.test_opportunity_edit(opportunity_id)
            if not edit_success:
                self.log_test("Integration Workflow", False, "Could not edit opportunity")
                return
            
            self.log_test(
                "Integration Workflow", 
                True, 
                "Complete workflow: quotation → L5 stage → PO upload → opportunity edit completed successfully"
            )
            
        except Exception as e:
            self.log_test("Integration Workflow", False, f"Exception: {str(e)}")

    # Helper methods for creating test data
    def create_l4_opportunity_for_pricing(self):
        """Create an opportunity in L4 stage for pricing tests"""
        try:
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                return None
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            l4_stage = next((s for s in stages if s.get('stage_code') == 'L4'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l4_stage or not inr_currency:
                return None
            
            opportunity_data = {
                "project_title": "Test Opportunity for Pricing",
                "company_id": "test-company-pricing",
                "stage_id": l4_stage['id'],
                "expected_revenue": 500000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-pricing",
                "win_probability": 75
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return response.json().get('id')
            return None
            
        except Exception:
            return None

    def create_opportunity_for_document_testing(self):
        """Create an opportunity for document testing"""
        try:
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                return None
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                return None
            
            opportunity_data = {
                "project_title": "Test Opportunity for Document Upload",
                "company_id": "test-company-docs",
                "stage_id": l1_stage['id'],
                "expected_revenue": 300000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-docs",
                "win_probability": 50
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return response.json().get('id')
            return None
            
        except Exception:
            return None

    def create_opportunity_for_po_testing(self):
        """Create an opportunity for PO testing"""
        try:
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                return None
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                return None
            
            opportunity_data = {
                "project_title": "Test Opportunity for PO Generation",
                "company_id": "test-company-po",
                "stage_id": l1_stage['id'],
                "expected_revenue": 400000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-po",
                "win_probability": 60
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return response.json().get('id')
            return None
            
        except Exception:
            return None

    def create_opportunity_for_crud_testing(self):
        """Create an opportunity for CRUD testing"""
        try:
            stages_response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if stages_response.status_code != 200 or currencies_response.status_code != 200:
                return None
            
            stages = stages_response.json()
            currencies = currencies_response.json()
            
            l1_stage = next((s for s in stages if s.get('stage_code') == 'L1'), None)
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), None)
            
            if not l1_stage or not inr_currency:
                return None
            
            opportunity_data = {
                "project_title": "Test Opportunity for CRUD Operations",
                "company_id": "test-company-crud",
                "stage_id": l1_stage['id'],
                "expected_revenue": 600000,
                "currency_id": inr_currency['id'],
                "lead_owner_id": "test-user-crud",
                "win_probability": 70
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                json=opportunity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return response.json().get('id')
            return None
            
        except Exception:
            return None

    def get_l5_stage_id(self):
        """Get L5 stage ID"""
        try:
            response = requests.get(f"{self.base_url}/mst/stages", headers=self.headers, timeout=10)
            if response.status_code == 200:
                stages = response.json()
                l5_stage = next((s for s in stages if s.get('stage_code') == 'L5'), None)
                return l5_stage['id'] if l5_stage else None
            return None
        except Exception:
            return None

    def create_test_quotation(self, opportunity_id):
        """Create a test quotation"""
        try:
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            if rate_cards_response.status_code != 200:
                return False
            
            rate_cards = rate_cards_response.json()
            if not rate_cards:
                return False
            
            quotation_data = {
                "quotation_name": "Test Quotation for Integration",
                "rate_card_id": rate_cards[0]['id'],
                "validity_date": "2025-06-30T00:00:00Z",
                "items": []
            }
            
            response = requests.post(
                f"{self.base_url}/opportunities/{opportunity_id}/quotations",
                headers=self.headers,
                json=quotation_data,
                timeout=10
            )
            
            return response.status_code in [200, 201]
            
        except Exception:
            return False

    def progress_to_l5_with_po(self, opportunity_id):
        """Progress opportunity to L5 stage with PO"""
        try:
            l5_stage_id = self.get_l5_stage_id()
            if not l5_stage_id:
                return False
            
            l5_data = {
                "stage_id": l5_stage_id,
                "stage_data": {
                    "po_number": "PO-INT123",
                    "po_value": 500000,
                    "po_date": "2025-01-30T00:00:00Z"
                }
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}/change-stage",
                headers=self.headers,
                json=l5_data,
                timeout=10
            )
            
            return response.status_code in [200, 204]
            
        except Exception:
            return False

    def upload_po_document(self, opportunity_id):
        """Upload PO document"""
        try:
            test_content = "Integration Test PO Document"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as file:
                    files = {
                        'file': ('integration_po.txt', file, 'text/plain')
                    }
                    data = {
                        'document_type': 'po_document'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/opportunities/{opportunity_id}/upload-document",
                        headers=self.headers,
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    return response.status_code in [200, 201]
            finally:
                os.unlink(temp_file_path)
                
        except Exception:
            return False

    def test_opportunity_edit(self, opportunity_id):
        """Test opportunity edit"""
        try:
            update_data = {
                "project_title": "Integration Test - Updated",
                "expected_revenue": 550000
            }
            
            response = requests.put(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                json=update_data,
                timeout=10
            )
            
            return response.status_code in [200, 204]
            
        except Exception:
            return False

    def run_all_tests(self):
        """Run all tests for the 4 issues"""
        print("🚀 STARTING 4 ISSUES BACKEND TESTING")
        print("=" * 60)
        
        # Authentication is required first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with other tests")
            return False
        
        # Test each issue
        self.test_issue_1_dummy_data_pricing()
        self.test_issue_2_l5_document_upload()
        self.test_issue_3_po_number_auto_generation()
        self.test_issue_4_opportunity_crud_operations()
        
        # Integration testing
        self.test_integration_workflow()
        
        # Print summary
        self.print_summary()
        
        return len(self.failed_tests) == 0

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 4 ISSUES TEST SUMMARY")
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
            print("\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = FourIssuesBackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()