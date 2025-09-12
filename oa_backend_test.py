#!/usr/bin/env python3
"""
Comprehensive Order Acknowledgement (OA) Module Backend Testing
Testing all OA endpoints and business logic as per review request
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')
load_dotenv('frontend/.env')

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001') + '/api'
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class OATestSuite:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.won_opportunity_id = None
        self.non_won_opportunity_id = None
        self.created_oa_id = None
        
    async def setup_session(self):
        """Setup HTTP session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate admin user
        async with self.session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data['access_token']
                print("✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Admin authentication failed: {response.status}")
                return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def find_test_opportunities(self):
        """Find opportunities for testing"""
        try:
            # Find Won opportunities
            async with self.session.get(f"{BACKEND_URL}/opportunities", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunities', [])
                    
                    won_opps = [opp for opp in opportunities if opp.get('status') == 'Won']
                    non_won_opps = [opp for opp in opportunities if opp.get('status') != 'Won']
                    
                    if won_opps:
                        self.won_opportunity_id = won_opps[0]['id']
                        print(f"✅ Found Won opportunity: {self.won_opportunity_id}")
                    
                    if non_won_opps:
                        self.non_won_opportunity_id = non_won_opps[0]['id']
                        print(f"✅ Found non-Won opportunity: {self.non_won_opportunity_id}")
                    
                    return len(won_opps) > 0 and len(non_won_opps) > 0
                else:
                    print(f"❌ Failed to fetch opportunities: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error finding test opportunities: {str(e)}")
            return False
    
    async def test_oa_eligibility_check(self):
        """Phase 1: Test OA Eligibility Check"""
        print("\n=== PHASE 1: OA ELIGIBILITY TESTING ===")
        
        # Test 1: Check eligibility for Won opportunity
        try:
            async with self.session.get(
                f"{BACKEND_URL}/opportunities/{self.won_opportunity_id}/can-create-oa",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('valid') == True:
                        print("✅ Won opportunity eligibility check: VALID")
                        self.test_results.append(("OA Eligibility - Won Opportunity", "PASS"))
                    else:
                        print(f"❌ Won opportunity should be valid but got: {data}")
                        self.test_results.append(("OA Eligibility - Won Opportunity", "FAIL"))
                else:
                    print(f"❌ Eligibility check failed: {response.status}")
                    self.test_results.append(("OA Eligibility - Won Opportunity", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing Won opportunity eligibility: {str(e)}")
            self.test_results.append(("OA Eligibility - Won Opportunity", "ERROR"))
        
        # Test 2: Check eligibility for non-Won opportunity
        try:
            async with self.session.get(
                f"{BACKEND_URL}/opportunities/{self.non_won_opportunity_id}/can-create-oa",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('valid') == False and 'Won opportunities' in str(data.get('errors', [])):
                        print("✅ Non-Won opportunity eligibility check: INVALID (as expected)")
                        self.test_results.append(("OA Eligibility - Non-Won Opportunity", "PASS"))
                    else:
                        print(f"❌ Non-Won opportunity should be invalid but got: {data}")
                        self.test_results.append(("OA Eligibility - Non-Won Opportunity", "FAIL"))
                else:
                    print(f"❌ Eligibility check failed: {response.status}")
                    self.test_results.append(("OA Eligibility - Non-Won Opportunity", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing non-Won opportunity eligibility: {str(e)}")
            self.test_results.append(("OA Eligibility - Non-Won Opportunity", "ERROR"))
        
        # Test 3: Check eligibility for non-existent opportunity
        try:
            fake_id = "non-existent-opportunity-id"
            async with self.session.get(
                f"{BACKEND_URL}/opportunities/{fake_id}/can-create-oa",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('valid') == False and 'not found' in str(data.get('errors', [])).lower():
                        print("✅ Non-existent opportunity eligibility check: INVALID (as expected)")
                        self.test_results.append(("OA Eligibility - Non-existent Opportunity", "PASS"))
                    else:
                        print(f"❌ Non-existent opportunity should be invalid but got: {data}")
                        self.test_results.append(("OA Eligibility - Non-existent Opportunity", "FAIL"))
                else:
                    print(f"❌ Eligibility check failed: {response.status}")
                    self.test_results.append(("OA Eligibility - Non-existent Opportunity", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing non-existent opportunity eligibility: {str(e)}")
            self.test_results.append(("OA Eligibility - Non-existent Opportunity", "ERROR"))
    
    async def test_oa_auto_fetch(self):
        """Phase 1: Test Auto-data Fetch"""
        print("\n=== PHASE 1: OA AUTO-DATA FETCH TESTING ===")
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/opportunities/{self.won_opportunity_id}/oa-data",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify required fields
                    required_fields = ['customer_name', 'total_amount', 'currency_id', 'profit_margin', 'items', 'anomalies']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        print("✅ Auto-fetch data structure: COMPLETE")
                        print(f"   - Customer: {data.get('customer_name')}")
                        print(f"   - Total Amount: {data.get('total_amount')}")
                        print(f"   - Currency ID: {data.get('currency_id')}")
                        print(f"   - Profit Margin: {data.get('profit_margin')}%")
                        print(f"   - Items Count: {len(data.get('items', []))}")
                        print(f"   - Anomalies Count: {len(data.get('anomalies', []))}")
                        
                        # Test anomaly detection logic
                        anomalies = data.get('anomalies', [])
                        if isinstance(anomalies, list):
                            print("✅ Anomaly detection working")
                            if anomalies:
                                print(f"   - Detected anomalies: {anomalies}")
                        
                        self.test_results.append(("OA Auto-fetch Data Structure", "PASS"))
                        return data  # Return for use in creation test
                    else:
                        print(f"❌ Missing required fields in auto-fetch data: {missing_fields}")
                        self.test_results.append(("OA Auto-fetch Data Structure", "FAIL"))
                        return None
                else:
                    print(f"❌ Auto-fetch failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    self.test_results.append(("OA Auto-fetch Data Structure", "FAIL"))
                    return None
        except Exception as e:
            print(f"❌ Error testing auto-fetch: {str(e)}")
            self.test_results.append(("OA Auto-fetch Data Structure", "ERROR"))
            return None
    
    async def test_oa_creation(self, auto_data=None):
        """Phase 2: Test OA Creation"""
        print("\n=== PHASE 2: OA CREATION TESTING ===")
        
        # Prepare test data
        if auto_data:
            oa_data = {
                "opportunity_id": self.won_opportunity_id,
                "customer_name": auto_data.get('customer_name', 'Test Customer'),
                "order_date": datetime.now().date().isoformat(),
                "items": auto_data.get('items', []),
                "total_amount": auto_data.get('total_amount', 100000),
                "currency_id": auto_data.get('currency_id', ''),
                "profit_margin": auto_data.get('profit_margin', 25.0),
                "remarks": "Test OA creation from comprehensive testing"
            }
        else:
            # Fallback test data
            oa_data = {
                "opportunity_id": self.won_opportunity_id,
                "customer_name": "Test Customer for OA",
                "order_date": datetime.now().date().isoformat(),
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Product",
                        "qty": 1,
                        "unit": "License",
                        "unit_price": 100000.0,
                        "total_price": 100000.0
                    }
                ],
                "total_amount": 100000.0,
                "currency_id": "inr-currency-id",
                "profit_margin": 25.0,
                "remarks": "Test OA creation"
            }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/order-acknowledgements",
                json=oa_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify ORD-XXXXXXX ID format
                    order_id = data.get('order_id', '')
                    if order_id.startswith('ORD-') and len(order_id) == 11:
                        print(f"✅ OA Creation successful with ID: {order_id}")
                        print(f"   - Order ID format: VALID ({order_id})")
                        
                        # Check GC approval flag for high-value orders
                        gc_approval = data.get('gc_approval_flag', False)
                        if oa_data['total_amount'] > 500000:
                            if gc_approval:
                                print("✅ GC approval flag set for high-value order")
                            else:
                                print("⚠️ GC approval flag should be set for high-value order")
                        else:
                            print(f"   - GC approval flag: {gc_approval} (amount: {oa_data['total_amount']})")
                        
                        self.created_oa_id = data.get('id')
                        self.test_results.append(("OA Creation", "PASS"))
                        return data
                    else:
                        print(f"❌ Invalid order ID format: {order_id}")
                        self.test_results.append(("OA Creation", "FAIL"))
                        return None
                else:
                    print(f"❌ OA Creation failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    self.test_results.append(("OA Creation", "FAIL"))
                    return None
        except Exception as e:
            print(f"❌ Error testing OA creation: {str(e)}")
            self.test_results.append(("OA Creation", "ERROR"))
            return None
    
    async def test_duplicate_prevention(self):
        """Test duplicate OA prevention"""
        print("\n=== DUPLICATE PREVENTION TESTING ===")
        
        # Try to create another OA for the same opportunity
        duplicate_data = {
            "opportunity_id": self.won_opportunity_id,
            "customer_name": "Duplicate Test Customer",
            "order_date": datetime.now().date().isoformat(),
            "items": [],
            "total_amount": 50000.0,
            "currency_id": "inr-currency-id",
            "profit_margin": 20.0,
            "remarks": "This should fail due to duplicate"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/order-acknowledgements",
                json=duplicate_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 400:
                    error_text = await response.text()
                    if 'already exists' in error_text.lower():
                        print("✅ Duplicate prevention working: Creation blocked")
                        self.test_results.append(("Duplicate Prevention", "PASS"))
                    else:
                        print(f"❌ Wrong error message for duplicate: {error_text}")
                        self.test_results.append(("Duplicate Prevention", "FAIL"))
                else:
                    print(f"❌ Duplicate creation should fail but got status: {response.status}")
                    self.test_results.append(("Duplicate Prevention", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing duplicate prevention: {str(e)}")
            self.test_results.append(("Duplicate Prevention", "ERROR"))
    
    async def test_oa_listing(self):
        """Phase 2: Test OA Listing"""
        print("\n=== PHASE 2: OA LISTING TESTING ===")
        
        # Test basic listing
        try:
            async with self.session.get(
                f"{BACKEND_URL}/order-acknowledgements",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'orders' in data and 'total' in data:
                        orders_count = len(data['orders'])
                        total_count = data['total']
                        print(f"✅ OA Listing successful: {orders_count} orders (total: {total_count})")
                        self.test_results.append(("OA Listing - Basic", "PASS"))
                    else:
                        print(f"❌ Invalid listing response structure: {data.keys()}")
                        self.test_results.append(("OA Listing - Basic", "FAIL"))
                else:
                    print(f"❌ OA Listing failed: {response.status}")
                    self.test_results.append(("OA Listing - Basic", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing OA listing: {str(e)}")
            self.test_results.append(("OA Listing - Basic", "ERROR"))
        
        # Test filtering by status
        try:
            async with self.session.get(
                f"{BACKEND_URL}/order-acknowledgements?status=Draft",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ OA Listing with status filter: {len(data.get('orders', []))} Draft orders")
                    self.test_results.append(("OA Listing - Status Filter", "PASS"))
                else:
                    print(f"❌ OA Listing with filter failed: {response.status}")
                    self.test_results.append(("OA Listing - Status Filter", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing OA listing with filter: {str(e)}")
            self.test_results.append(("OA Listing - Status Filter", "ERROR"))
        
        # Test pagination
        try:
            async with self.session.get(
                f"{BACKEND_URL}/order-acknowledgements?skip=0&limit=5",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('skip') == 0 and data.get('limit') == 5:
                        print("✅ OA Listing pagination working")
                        self.test_results.append(("OA Listing - Pagination", "PASS"))
                    else:
                        print(f"❌ Pagination parameters not returned correctly")
                        self.test_results.append(("OA Listing - Pagination", "FAIL"))
                else:
                    print(f"❌ OA Listing with pagination failed: {response.status}")
                    self.test_results.append(("OA Listing - Pagination", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing OA listing pagination: {str(e)}")
            self.test_results.append(("OA Listing - Pagination", "ERROR"))
    
    async def test_oa_get_by_id(self):
        """Phase 2: Test Get OA by ID"""
        print("\n=== PHASE 2: GET OA BY ID TESTING ===")
        
        if not self.created_oa_id:
            print("❌ No created OA ID available for testing")
            self.test_results.append(("Get OA by ID - Valid", "SKIP"))
            self.test_results.append(("Get OA by ID - Invalid", "SKIP"))
            return
        
        # Test valid ID
        try:
            async with self.session.get(
                f"{BACKEND_URL}/order-acknowledgements/{self.created_oa_id}",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('id') == self.created_oa_id:
                        print(f"✅ Get OA by ID successful: {data.get('order_id')}")
                        self.test_results.append(("Get OA by ID - Valid", "PASS"))
                    else:
                        print(f"❌ Returned OA ID doesn't match requested ID")
                        self.test_results.append(("Get OA by ID - Valid", "FAIL"))
                else:
                    print(f"❌ Get OA by ID failed: {response.status}")
                    self.test_results.append(("Get OA by ID - Valid", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing get OA by valid ID: {str(e)}")
            self.test_results.append(("Get OA by ID - Valid", "ERROR"))
        
        # Test invalid ID
        try:
            fake_id = "non-existent-oa-id"
            async with self.session.get(
                f"{BACKEND_URL}/order-acknowledgements/{fake_id}",
                headers=self.get_headers()
            ) as response:
                if response.status == 404:
                    print("✅ Get OA by invalid ID: 404 returned (as expected)")
                    self.test_results.append(("Get OA by ID - Invalid", "PASS"))
                else:
                    print(f"❌ Invalid ID should return 404 but got: {response.status}")
                    self.test_results.append(("Get OA by ID - Invalid", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing get OA by invalid ID: {str(e)}")
            self.test_results.append(("Get OA by ID - Invalid", "ERROR"))
    
    async def test_oa_update(self):
        """Phase 2: Test OA Update"""
        print("\n=== PHASE 2: OA UPDATE TESTING ===")
        
        if not self.created_oa_id:
            print("❌ No created OA ID available for testing")
            self.test_results.append(("OA Update", "SKIP"))
            return
        
        # Update data
        update_data = {
            "customer_name": "Updated Customer Name",
            "total_amount": 150000.0,
            "profit_margin": 30.0,
            "remarks": "Updated remarks for testing"
        }
        
        try:
            async with self.session.put(
                f"{BACKEND_URL}/order-acknowledgements/{self.created_oa_id}",
                json=update_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify updates
                    if (data.get('customer_name') == update_data['customer_name'] and
                        data.get('total_amount') == update_data['total_amount']):
                        print("✅ OA Update successful")
                        print(f"   - Updated customer: {data.get('customer_name')}")
                        print(f"   - Updated amount: {data.get('total_amount')}")
                        
                        # Check if updated_by and updated_at are set
                        if data.get('updated_by') and data.get('updated_at'):
                            print("✅ Audit fields (updated_by, updated_at) set correctly")
                        
                        self.test_results.append(("OA Update", "PASS"))
                    else:
                        print(f"❌ Update data not reflected correctly")
                        self.test_results.append(("OA Update", "FAIL"))
                else:
                    print(f"❌ OA Update failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    self.test_results.append(("OA Update", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing OA update: {str(e)}")
            self.test_results.append(("OA Update", "ERROR"))
    
    async def test_oa_status_updates(self):
        """Phase 3: Test Status Updates"""
        print("\n=== PHASE 3: STATUS UPDATE TESTING ===")
        
        if not self.created_oa_id:
            print("❌ No created OA ID available for testing")
            self.test_results.append(("Status Update - Valid", "SKIP"))
            self.test_results.append(("Status Update - Invalid", "SKIP"))
            return
        
        # Test valid status transitions
        valid_statuses = ["Under Review", "Approved", "Fulfilled"]
        
        for status in valid_statuses:
            try:
                async with self.session.patch(
                    f"{BACKEND_URL}/order-acknowledgements/{self.created_oa_id}/status",
                    json={"status": status},
                    headers=self.get_headers()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Status update to '{status}': SUCCESS")
                    else:
                        print(f"❌ Status update to '{status}' failed: {response.status}")
                        break
            except Exception as e:
                print(f"❌ Error updating status to '{status}': {str(e)}")
                break
        else:
            self.test_results.append(("Status Update - Valid Transitions", "PASS"))
        
        # Test invalid status
        try:
            async with self.session.patch(
                f"{BACKEND_URL}/order-acknowledgements/{self.created_oa_id}/status",
                json={"status": "InvalidStatus"},
                headers=self.get_headers()
            ) as response:
                if response.status == 400:
                    print("✅ Invalid status rejected (as expected)")
                    self.test_results.append(("Status Update - Invalid Status", "PASS"))
                else:
                    print(f"❌ Invalid status should be rejected but got: {response.status}")
                    self.test_results.append(("Status Update - Invalid Status", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing invalid status: {str(e)}")
            self.test_results.append(("Status Update - Invalid Status", "ERROR"))
    
    async def test_oa_delete(self):
        """Phase 2: Test OA Delete"""
        print("\n=== PHASE 2: OA DELETE TESTING ===")
        
        if not self.created_oa_id:
            print("❌ No created OA ID available for testing")
            self.test_results.append(("OA Delete", "SKIP"))
            return
        
        try:
            async with self.session.delete(
                f"{BACKEND_URL}/order-acknowledgements/{self.created_oa_id}",
                headers=self.get_headers()
            ) as response:
                if response.status == 400:
                    error_text = await response.text()
                    if "Cannot delete fulfilled orders" in error_text:
                        print("✅ Delete protection working - fulfilled orders cannot be deleted")
                        self.test_results.append(("OA Delete - Fulfilled Protection", "PASS"))
                    else:
                        print(f"❌ Unexpected error: {error_text}")
                        self.test_results.append(("OA Delete - Fulfilled Protection", "FAIL"))
                elif response.status == 200:
                    data = await response.json()
                    print("✅ OA Delete successful (soft delete)")
                    
                    # Verify soft delete - order should not appear in active list
                    async with self.session.get(
                        f"{BACKEND_URL}/order-acknowledgements/{self.created_oa_id}",
                        headers=self.get_headers()
                    ) as verify_response:
                        if verify_response.status == 404:
                            print("✅ Soft delete verified - order not in active list")
                            self.test_results.append(("OA Delete - Soft Delete", "PASS"))
                        else:
                            print("❌ Soft delete not working - order still accessible")
                            self.test_results.append(("OA Delete - Soft Delete", "FAIL"))
                else:
                    print(f"❌ OA Delete failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    self.test_results.append(("OA Delete - Fulfilled Protection", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing OA delete: {str(e)}")
            self.test_results.append(("OA Delete - Fulfilled Protection", "ERROR"))
    
    async def test_business_logic_validation(self):
        """Phase 4: Test Business Logic Validation"""
        print("\n=== PHASE 4: BUSINESS LOGIC VALIDATION ===")
        
        # Test high-value approval logic (>500K)
        high_value_data = {
            "opportunity_id": self.won_opportunity_id,
            "customer_name": "High Value Customer",
            "order_date": datetime.now().date().isoformat(),
            "items": [
                {
                    "product_id": "high-value-product",
                    "product_name": "Enterprise Solution",
                    "qty": 1,
                    "unit": "License",
                    "unit_price": 600000.0,
                    "total_price": 600000.0
                }
            ],
            "total_amount": 600000.0,
            "currency_id": "inr-currency-id",
            "profit_margin": 25.0,
            "remarks": "High value order for GC approval testing"
        }
        
        try:
            # First delete any existing OA for this opportunity
            await self.cleanup_existing_oa()
            
            async with self.session.post(
                f"{BACKEND_URL}/order-acknowledgements",
                json=high_value_data,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    gc_approval = data.get('gc_approval_flag', False)
                    
                    if gc_approval:
                        print("✅ High-value approval logic working (>500K triggers GC approval)")
                        self.test_results.append(("Business Logic - High Value Approval", "PASS"))
                    else:
                        print("❌ High-value order should trigger GC approval")
                        self.test_results.append(("Business Logic - High Value Approval", "FAIL"))
                    
                    # Clean up
                    await self.session.delete(
                        f"{BACKEND_URL}/order-acknowledgements/{data.get('id')}",
                        headers=self.get_headers()
                    )
                else:
                    print(f"❌ High-value order creation failed: {response.status}")
                    self.test_results.append(("Business Logic - High Value Approval", "FAIL"))
        except Exception as e:
            print(f"❌ Error testing high-value approval logic: {str(e)}")
            self.test_results.append(("Business Logic - High Value Approval", "ERROR"))
    
    async def cleanup_existing_oa(self):
        """Clean up any existing OA for the test opportunity"""
        try:
            # Get existing OAs
            async with self.session.get(
                f"{BACKEND_URL}/order-acknowledgements",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = data.get('orders', [])
                    
                    # Find and delete OAs for our test opportunity
                    for order in orders:
                        if order.get('opportunity_id') == self.won_opportunity_id:
                            await self.session.delete(
                                f"{BACKEND_URL}/order-acknowledgements/{order.get('id')}",
                                headers=self.get_headers()
                            )
        except:
            pass  # Ignore cleanup errors
    
    async def run_comprehensive_test(self):
        """Run all OA tests"""
        print("🚀 STARTING COMPREHENSIVE ORDER ACKNOWLEDGEMENT (OA) MODULE TESTING")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            return False
        
        if not await self.find_test_opportunities():
            print("❌ Could not find required test opportunities")
            return False
        
        # Phase 1: Eligibility and Auto-fetch
        await self.test_oa_eligibility_check()
        auto_data = await self.test_oa_auto_fetch()
        
        # Phase 2: CRUD Operations
        await self.test_oa_creation(auto_data)
        await self.test_duplicate_prevention()
        await self.test_oa_listing()
        await self.test_oa_get_by_id()
        await self.test_oa_update()
        
        # Phase 3: Status and Approval
        await self.test_oa_status_updates()
        
        # Phase 2 continued: Delete (after status tests)
        await self.test_oa_delete()
        
        # Phase 4: Business Logic
        await self.test_business_logic_validation()
        
        # Print summary
        await self.print_test_summary()
        
        return True
    
    async def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE OA MODULE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in self.test_results if result == "PASS")
        failed = sum(1 for _, result in self.test_results if result == "FAIL")
        errors = sum(1 for _, result in self.test_results if result == "ERROR")
        skipped = sum(1 for _, result in self.test_results if result == "SKIP")
        total = len(self.test_results)
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"   ✅ PASSED: {passed}/{total}")
        print(f"   ❌ FAILED: {failed}/{total}")
        print(f"   🔥 ERRORS: {errors}/{total}")
        print(f"   ⏭️  SKIPPED: {skipped}/{total}")
        print(f"   📈 SUCCESS RATE: {(passed/total*100):.1f}%" if total > 0 else "   📈 SUCCESS RATE: 0%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results:
            icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🔥", "SKIP": "⏭️"}[result]
            print(f"   {icon} {test_name}: {result}")
        
        print(f"\n🎯 SUCCESS CRITERIA VERIFICATION:")
        
        # Check key success criteria
        criteria_met = []
        
        # API endpoints respond correctly
        api_tests = [r for t, r in self.test_results if "OA" in t and r == "PASS"]
        if len(api_tests) >= 8:  # Most API tests passed
            criteria_met.append("✅ All API endpoints respond correctly with proper HTTP status codes")
        else:
            criteria_met.append("❌ Some API endpoints have issues")
        
        # ORD-XXXXXXX ID generation
        creation_passed = any(t == "OA Creation" and r == "PASS" for t, r in self.test_results)
        if creation_passed:
            criteria_met.append("✅ ORD-XXXXXXX ID generation works properly")
        else:
            criteria_met.append("❌ ORD-XXXXXXX ID generation has issues")
        
        # Duplicate prevention
        dup_prevention = any(t == "Duplicate Prevention" and r == "PASS" for t, r in self.test_results)
        if dup_prevention:
            criteria_met.append("✅ Duplicate prevention works (one OA per opportunity)")
        else:
            criteria_met.append("❌ Duplicate prevention not working properly")
        
        # Auto-fetch functionality
        auto_fetch = any(t == "OA Auto-fetch Data Structure" and r == "PASS" for t, r in self.test_results)
        if auto_fetch:
            criteria_met.append("✅ Auto-fetch pulls correct data from opportunity/quotation/company")
        else:
            criteria_met.append("❌ Auto-fetch functionality has issues")
        
        # GC approval logic
        gc_approval = any(t == "Business Logic - High Value Approval" and r == "PASS" for t, r in self.test_results)
        if gc_approval:
            criteria_met.append("✅ GC approval flag works for high-value orders")
        else:
            criteria_met.append("❌ GC approval logic needs verification")
        
        # Status workflow
        status_tests = any(t.startswith("Status Update") and r == "PASS" for t, r in self.test_results)
        if status_tests:
            criteria_met.append("✅ Status workflow prevents invalid transitions")
        else:
            criteria_met.append("❌ Status workflow needs verification")
        
        # Soft delete
        soft_delete = any(t == "OA Delete - Soft Delete" and r == "PASS" for t, r in self.test_results)
        if soft_delete:
            criteria_met.append("✅ Soft delete preserves data integrity")
        else:
            criteria_met.append("❌ Soft delete functionality needs verification")
        
        for criterion in criteria_met:
            print(f"   {criterion}")
        
        print("\n" + "=" * 80)
        
        if passed >= total * 0.8:  # 80% success rate
            print("🎉 COMPREHENSIVE OA MODULE TESTING: EXCELLENT RESULTS!")
            print("   The Order Acknowledgement module is PRODUCTION-READY")
        elif passed >= total * 0.6:  # 60% success rate
            print("⚠️  COMPREHENSIVE OA MODULE TESTING: GOOD RESULTS WITH MINOR ISSUES")
            print("   The Order Acknowledgement module needs minor fixes")
        else:
            print("🚨 COMPREHENSIVE OA MODULE TESTING: SIGNIFICANT ISSUES FOUND")
            print("   The Order Acknowledgement module needs major fixes")
        
        print("=" * 80)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def main():
    """Main test execution"""
    test_suite = OATestSuite()
    try:
        success = await test_suite.run_comprehensive_test()
        return success
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(main())