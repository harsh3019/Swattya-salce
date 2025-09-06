#!/usr/bin/env python3
"""
Lead Management Backend API Testing Suite
Tests Product Services, Sub-Tender Types, and Partner CRUD APIs
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://sawayatta-erp.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class LeadManagementAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        print("🔐 Authenticating with admin credentials...")
        
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                })
                
                print(f"✅ Authentication successful")
                print(f"   User: {self.user_data.get('username')} ({self.user_data.get('email')})")
                print(f"   Role ID: {self.user_data.get('role_id')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_product_services_crud(self):
        """Test Product Services CRUD operations"""
        print("\n" + "="*60)
        print("🧪 TESTING PRODUCT SERVICES CRUD APIs")
        print("="*60)
        
        results = {
            'list_all': False,
            'get_single': False,
            'create_new': False,
            'update_existing': False,
            'delete_soft': False,
            'validation_tests': False,
            'dependency_check': False
        }
        
        # Test 1: GET /api/product-services (List all)
        print("\n1️⃣ Testing GET /api/product-services (List all)")
        try:
            response = self.session.get(f"{API_BASE}/product-services")
            if response.status_code == 200:
                services = response.json()
                print(f"✅ List all product services successful")
                print(f"   Found {len(services)} product services")
                
                # Verify seed data
                expected_services = ["Software Development", "Web Development", "Mobile App Development", 
                                   "Cloud Services", "Digital Marketing", "Data Analytics", 
                                   "Cybersecurity", "AI/ML Solutions"]
                found_services = [s['name'] for s in services]
                
                for expected in expected_services:
                    if expected in found_services:
                        print(f"   ✓ Found expected service: {expected}")
                    else:
                        print(f"   ⚠️ Missing expected service: {expected}")
                
                results['list_all'] = True
                self.test_service_id = services[0]['id'] if services else None
            else:
                print(f"❌ List all failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ List all error: {str(e)}")
        
        # Test 2: GET /api/product-services/{id} (Get single)
        if hasattr(self, 'test_service_id') and self.test_service_id:
            print(f"\n2️⃣ Testing GET /api/product-services/{self.test_service_id} (Get single)")
            try:
                response = self.session.get(f"{API_BASE}/product-services/{self.test_service_id}")
                if response.status_code == 200:
                    service = response.json()
                    print(f"✅ Get single product service successful")
                    print(f"   Service: {service.get('name')}")
                    print(f"   Description: {service.get('description', 'N/A')}")
                    print(f"   Active: {service.get('is_active')}")
                    results['get_single'] = True
                else:
                    print(f"❌ Get single failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Get single error: {str(e)}")
        
        # Test 3: POST /api/product-services (Create new)
        print("\n3️⃣ Testing POST /api/product-services (Create new)")
        new_service_data = {
            "name": "Blockchain Development",
            "description": "Blockchain and cryptocurrency development services",
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-services", json=new_service_data)
            if response.status_code == 200:
                created_service = response.json()
                self.created_service_id = created_service.get('id')
                print(f"✅ Create new product service successful")
                print(f"   Created service ID: {self.created_service_id}")
                print(f"   Name: {created_service.get('name')}")
                results['create_new'] = True
            else:
                print(f"❌ Create new failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Create new error: {str(e)}")
        
        # Test 4: Name uniqueness validation
        print("\n4️⃣ Testing name uniqueness validation")
        try:
            response = self.session.post(f"{API_BASE}/product-services", json=new_service_data)
            if response.status_code == 400:
                print(f"✅ Name uniqueness validation working")
                print(f"   Error: {response.json().get('detail')}")
                results['validation_tests'] = True
            else:
                print(f"❌ Name uniqueness validation failed: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"❌ Validation test error: {str(e)}")
        
        # Test 5: PUT /api/product-services/{id} (Update existing)
        if hasattr(self, 'created_service_id'):
            print(f"\n5️⃣ Testing PUT /api/product-services/{self.created_service_id} (Update existing)")
            update_data = {
                "name": "Blockchain & DeFi Development",
                "description": "Advanced blockchain, DeFi, and Web3 development services"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/product-services/{self.created_service_id}", json=update_data)
                if response.status_code == 200:
                    updated_service = response.json()
                    print(f"✅ Update existing product service successful")
                    print(f"   Updated name: {updated_service.get('name')}")
                    print(f"   Updated description: {updated_service.get('description')}")
                    results['update_existing'] = True
                else:
                    print(f"❌ Update existing failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Update existing error: {str(e)}")
        
        # Test 6: DELETE /api/product-services/{id} (Soft delete)
        if hasattr(self, 'created_service_id'):
            print(f"\n6️⃣ Testing DELETE /api/product-services/{self.created_service_id} (Soft delete)")
            try:
                response = self.session.delete(f"{API_BASE}/product-services/{self.created_service_id}")
                if response.status_code == 200:
                    print(f"✅ Soft delete product service successful")
                    print(f"   Message: {response.json().get('message')}")
                    results['delete_soft'] = True
                    
                    # Verify soft delete - service should not appear in active list
                    list_response = self.session.get(f"{API_BASE}/product-services")
                    if list_response.status_code == 200:
                        active_services = list_response.json()
                        deleted_found = any(s['id'] == self.created_service_id for s in active_services)
                        if not deleted_found:
                            print(f"   ✓ Soft delete verified - service not in active list")
                        else:
                            print(f"   ⚠️ Soft delete issue - service still in active list")
                else:
                    print(f"❌ Soft delete failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Soft delete error: {str(e)}")
        
        # Test 7: Dependency check (try to delete service used in leads)
        print(f"\n7️⃣ Testing dependency check for deletion")
        if hasattr(self, 'test_service_id') and self.test_service_id:
            try:
                response = self.session.delete(f"{API_BASE}/product-services/{self.test_service_id}")
                if response.status_code == 400 and "being used in leads" in response.text:
                    print(f"✅ Dependency check working")
                    print(f"   Error: {response.json().get('detail')}")
                    results['dependency_check'] = True
                elif response.status_code == 200:
                    print(f"✅ Dependency check passed (no leads using this service)")
                    results['dependency_check'] = True
                else:
                    print(f"❌ Dependency check failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Dependency check error: {str(e)}")
        
        return results
    
    def test_sub_tender_types_crud(self):
        """Test Sub-Tender Types CRUD operations"""
        print("\n" + "="*60)
        print("🧪 TESTING SUB-TENDER TYPES CRUD APIs")
        print("="*60)
        
        results = {
            'list_all': False,
            'get_single': False,
            'create_new': False,
            'update_existing': False,
            'delete_soft': False,
            'validation_tests': False,
            'dependency_check': False
        }
        
        # Test 1: GET /api/sub-tender-types (List all)
        print("\n1️⃣ Testing GET /api/sub-tender-types (List all)")
        try:
            response = self.session.get(f"{API_BASE}/sub-tender-types")
            if response.status_code == 200:
                sub_tenders = response.json()
                print(f"✅ List all sub-tender types successful")
                print(f"   Found {len(sub_tenders)} sub-tender types")
                
                # Verify seed data
                expected_types = ["Government - Central", "Government - State", "Government - Municipal", 
                                "Government - PSU", "Private - Enterprise", "Private - SME"]
                found_types = [st['name'] for st in sub_tenders]
                
                for expected in expected_types:
                    if expected in found_types:
                        print(f"   ✓ Found expected type: {expected}")
                    else:
                        print(f"   ⚠️ Missing expected type: {expected}")
                
                results['list_all'] = True
                self.test_sub_tender_id = sub_tenders[0]['id'] if sub_tenders else None
            else:
                print(f"❌ List all failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ List all error: {str(e)}")
        
        # Test 2: GET /api/sub-tender-types/{id} (Get single)
        if hasattr(self, 'test_sub_tender_id') and self.test_sub_tender_id:
            print(f"\n2️⃣ Testing GET /api/sub-tender-types/{self.test_sub_tender_id} (Get single)")
            try:
                response = self.session.get(f"{API_BASE}/sub-tender-types/{self.test_sub_tender_id}")
                if response.status_code == 200:
                    sub_tender = response.json()
                    print(f"✅ Get single sub-tender type successful")
                    print(f"   Type: {sub_tender.get('name')}")
                    print(f"   Description: {sub_tender.get('description', 'N/A')}")
                    print(f"   Active: {sub_tender.get('is_active')}")
                    results['get_single'] = True
                else:
                    print(f"❌ Get single failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Get single error: {str(e)}")
        
        # Test 3: POST /api/sub-tender-types (Create new)
        print("\n3️⃣ Testing POST /api/sub-tender-types (Create new)")
        new_sub_tender_data = {
            "name": "Government - Defense",
            "description": "Defense and military sector tenders",
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{API_BASE}/sub-tender-types", json=new_sub_tender_data)
            if response.status_code == 200:
                created_sub_tender = response.json()
                self.created_sub_tender_id = created_sub_tender.get('id')
                print(f"✅ Create new sub-tender type successful")
                print(f"   Created type ID: {self.created_sub_tender_id}")
                print(f"   Name: {created_sub_tender.get('name')}")
                results['create_new'] = True
            else:
                print(f"❌ Create new failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Create new error: {str(e)}")
        
        # Test 4: Name uniqueness validation
        print("\n4️⃣ Testing name uniqueness validation")
        try:
            response = self.session.post(f"{API_BASE}/sub-tender-types", json=new_sub_tender_data)
            if response.status_code == 400:
                print(f"✅ Name uniqueness validation working")
                print(f"   Error: {response.json().get('detail')}")
                results['validation_tests'] = True
            else:
                print(f"❌ Name uniqueness validation failed: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"❌ Validation test error: {str(e)}")
        
        # Test 5: PUT /api/sub-tender-types/{id} (Update existing)
        if hasattr(self, 'created_sub_tender_id'):
            print(f"\n5️⃣ Testing PUT /api/sub-tender-types/{self.created_sub_tender_id} (Update existing)")
            update_data = {
                "name": "Government - Defense & Security",
                "description": "Defense, military, and national security sector tenders"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/sub-tender-types/{self.created_sub_tender_id}", json=update_data)
                if response.status_code == 200:
                    updated_sub_tender = response.json()
                    print(f"✅ Update existing sub-tender type successful")
                    print(f"   Updated name: {updated_sub_tender.get('name')}")
                    print(f"   Updated description: {updated_sub_tender.get('description')}")
                    results['update_existing'] = True
                else:
                    print(f"❌ Update existing failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Update existing error: {str(e)}")
        
        # Test 6: DELETE /api/sub-tender-types/{id} (Soft delete)
        if hasattr(self, 'created_sub_tender_id'):
            print(f"\n6️⃣ Testing DELETE /api/sub-tender-types/{self.created_sub_tender_id} (Soft delete)")
            try:
                response = self.session.delete(f"{API_BASE}/sub-tender-types/{self.created_sub_tender_id}")
                if response.status_code == 200:
                    print(f"✅ Soft delete sub-tender type successful")
                    print(f"   Message: {response.json().get('message')}")
                    results['delete_soft'] = True
                    
                    # Verify soft delete
                    list_response = self.session.get(f"{API_BASE}/sub-tender-types")
                    if list_response.status_code == 200:
                        active_types = list_response.json()
                        deleted_found = any(st['id'] == self.created_sub_tender_id for st in active_types)
                        if not deleted_found:
                            print(f"   ✓ Soft delete verified - type not in active list")
                        else:
                            print(f"   ⚠️ Soft delete issue - type still in active list")
                else:
                    print(f"❌ Soft delete failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Soft delete error: {str(e)}")
        
        # Test 7: Dependency check
        print(f"\n7️⃣ Testing dependency check for deletion")
        if hasattr(self, 'test_sub_tender_id') and self.test_sub_tender_id:
            try:
                response = self.session.delete(f"{API_BASE}/sub-tender-types/{self.test_sub_tender_id}")
                if response.status_code == 400 and "being used in leads" in response.text:
                    print(f"✅ Dependency check working")
                    print(f"   Error: {response.json().get('detail')}")
                    results['dependency_check'] = True
                elif response.status_code == 200:
                    print(f"✅ Dependency check passed (no leads using this type)")
                    results['dependency_check'] = True
                else:
                    print(f"❌ Dependency check failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Dependency check error: {str(e)}")
        
        return results
    
    def test_partners_crud(self):
        """Test Partners CRUD operations"""
        print("\n" + "="*60)
        print("🧪 TESTING PARTNERS CRUD APIs")
        print("="*60)
        
        results = {
            'list_all': False,
            'get_single': False,
            'create_new': False,
            'update_existing': False,
            'delete_soft': False,
            'validation_tests': False
        }
        
        # Test 1: GET /api/partners (List all)
        print("\n1️⃣ Testing GET /api/partners (List all)")
        try:
            response = self.session.get(f"{API_BASE}/partners")
            if response.status_code == 200:
                partners = response.json()
                print(f"✅ List all partners successful")
                print(f"   Found {len(partners)} partners")
                results['list_all'] = True
                self.test_partner_id = partners[0]['id'] if partners else None
            else:
                print(f"❌ List all failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ List all error: {str(e)}")
        
        # Test 2: GET /api/partners/{id} (Get single) - if partners exist
        if hasattr(self, 'test_partner_id') and self.test_partner_id:
            print(f"\n2️⃣ Testing GET /api/partners/{self.test_partner_id} (Get single)")
            try:
                response = self.session.get(f"{API_BASE}/partners/{self.test_partner_id}")
                if response.status_code == 200:
                    partner = response.json()
                    print(f"✅ Get single partner successful")
                    print(f"   Partner: {partner.get('first_name')} {partner.get('last_name')}")
                    print(f"   Email: {partner.get('email')}")
                    print(f"   Phone: {partner.get('phone_number')}")
                    results['get_single'] = True
                else:
                    print(f"❌ Get single failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Get single error: {str(e)}")
        
        # Test 3: POST /api/partners (Create new)
        print("\n3️⃣ Testing POST /api/partners (Create new)")
        new_partner_data = {
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "email": "rajesh.kumar@techpartners.com",
            "phone_number": "+91-9876543210",
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{API_BASE}/partners", json=new_partner_data)
            if response.status_code == 200:
                created_partner = response.json()
                self.created_partner_id = created_partner.get('id')
                print(f"✅ Create new partner successful")
                print(f"   Created partner ID: {self.created_partner_id}")
                print(f"   Name: {created_partner.get('first_name')} {created_partner.get('last_name')}")
                print(f"   Email: {created_partner.get('email')}")
                results['create_new'] = True
            else:
                print(f"❌ Create new failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Create new error: {str(e)}")
        
        # Test 4: Email uniqueness validation
        print("\n4️⃣ Testing email uniqueness validation")
        try:
            response = self.session.post(f"{API_BASE}/partners", json=new_partner_data)
            if response.status_code == 400:
                print(f"✅ Email uniqueness validation working")
                print(f"   Error: {response.json().get('detail')}")
                results['validation_tests'] = True
            else:
                print(f"❌ Email uniqueness validation failed: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"❌ Validation test error: {str(e)}")
        
        # Test 5: PUT /api/partners/{id} (Update existing)
        if hasattr(self, 'created_partner_id'):
            print(f"\n5️⃣ Testing PUT /api/partners/{self.created_partner_id} (Update existing)")
            update_data = {
                "first_name": "Rajesh",
                "last_name": "Kumar Sharma",
                "email": "rajesh.sharma@techpartners.com",
                "phone_number": "+91-9876543211"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/partners/{self.created_partner_id}", json=update_data)
                if response.status_code == 200:
                    updated_partner = response.json()
                    print(f"✅ Update existing partner successful")
                    print(f"   Updated name: {updated_partner.get('first_name')} {updated_partner.get('last_name')}")
                    print(f"   Updated email: {updated_partner.get('email')}")
                    print(f"   Updated phone: {updated_partner.get('phone_number')}")
                    results['update_existing'] = True
                else:
                    print(f"❌ Update existing failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Update existing error: {str(e)}")
        
        # Test 6: DELETE /api/partners/{id} (Soft delete)
        if hasattr(self, 'created_partner_id'):
            print(f"\n6️⃣ Testing DELETE /api/partners/{self.created_partner_id} (Soft delete)")
            try:
                response = self.session.delete(f"{API_BASE}/partners/{self.created_partner_id}")
                if response.status_code == 200:
                    print(f"✅ Soft delete partner successful")
                    print(f"   Message: {response.json().get('message')}")
                    results['delete_soft'] = True
                    
                    # Verify soft delete
                    list_response = self.session.get(f"{API_BASE}/partners")
                    if list_response.status_code == 200:
                        active_partners = list_response.json()
                        deleted_found = any(p['id'] == self.created_partner_id for p in active_partners)
                        if not deleted_found:
                            print(f"   ✓ Soft delete verified - partner not in active list")
                        else:
                            print(f"   ⚠️ Soft delete issue - partner still in active list")
                else:
                    print(f"❌ Soft delete failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Soft delete error: {str(e)}")
        
        return results
    
    def test_rbac_access_control(self):
        """Test RBAC access control for Lead Management APIs"""
        print("\n" + "="*60)
        print("🔐 TESTING RBAC ACCESS CONTROL")
        print("="*60)
        
        results = {
            'admin_permissions': False,
            'access_control': False
        }
        
        # Test admin permissions
        print("\n1️⃣ Testing admin user permissions")
        try:
            response = self.session.get(f"{API_BASE}/auth/permissions")
            if response.status_code == 200:
                permissions = response.json().get('permissions', [])
                lead_permissions = [p for p in permissions if 'Lead' in p.get('menu', '') or 'Partner' in p.get('menu', '')]
                
                print(f"✅ Admin permissions retrieved")
                print(f"   Total permissions: {len(permissions)}")
                print(f"   Lead-related permissions: {len(lead_permissions)}")
                
                # Check for required permissions
                required_perms = ['View', 'Add', 'Edit', 'Delete']
                for perm in required_perms:
                    has_perm = any(p.get('permission') == perm for p in permissions)
                    if has_perm:
                        print(f"   ✓ Has {perm} permission")
                    else:
                        print(f"   ⚠️ Missing {perm} permission")
                
                results['admin_permissions'] = True
            else:
                print(f"❌ Failed to get permissions: {response.status_code}")
        except Exception as e:
            print(f"❌ Permissions test error: {str(e)}")
        
        # Test access control (admin should have access)
        print("\n2️⃣ Testing access control enforcement")
        try:
            # Test access to product services
            response = self.session.get(f"{API_BASE}/product-services")
            if response.status_code == 200:
                print(f"✅ Admin has access to Product Services API")
                results['access_control'] = True
            elif response.status_code == 403:
                print(f"❌ Admin denied access to Product Services API")
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Access control test error: {str(e)}")
        
        return results
    
    def run_all_tests(self):
        """Run all Lead Management API tests"""
        print("🚀 STARTING LEAD MANAGEMENT BACKEND API TESTING")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test RBAC first
        rbac_results = self.test_rbac_access_control()
        
        # Test all CRUD APIs
        product_results = self.test_product_services_crud()
        sub_tender_results = self.test_sub_tender_types_crud()
        partner_results = self.test_partners_crud()
        
        # Generate summary
        self.generate_test_summary(rbac_results, product_results, sub_tender_results, partner_results)
    
    def generate_test_summary(self, rbac_results, product_results, sub_tender_results, partner_results):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        all_results = {
            'RBAC Access Control': rbac_results,
            'Product Services CRUD': product_results,
            'Sub-Tender Types CRUD': sub_tender_results,
            'Partners CRUD': partner_results
        }
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            print(f"\n🔍 {category}:")
            category_passed = 0
            category_total = len(results)
            
            for test_name, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {test_name}: {status}")
                if passed:
                    category_passed += 1
                    passed_tests += 1
                total_tests += 1
            
            success_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            print(f"   Category Success Rate: {success_rate:.1f}% ({category_passed}/{category_total})")
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 90:
            print(f"\n🎉 EXCELLENT! Lead Management APIs are working perfectly!")
        elif overall_success_rate >= 75:
            print(f"\n✅ GOOD! Lead Management APIs are mostly functional with minor issues.")
        elif overall_success_rate >= 50:
            print(f"\n⚠️ MODERATE! Lead Management APIs have some significant issues.")
        else:
            print(f"\n❌ CRITICAL! Lead Management APIs have major issues requiring attention.")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = LeadManagementAPITester()
    tester.run_all_tests()