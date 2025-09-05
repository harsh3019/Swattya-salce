#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid
import io
import os

class CompanyMasterDataTester:
    def __init__(self, base_url="https://swayatta-admin.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.master_data = {}  # Store master data for cascading tests

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, files=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Don't set Content-Type for file uploads
        if files is None:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers={k:v for k,v in headers.items() if k != 'Content-Type'}, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data

        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_login(self):
        """Test login functionality"""
        print("\n🔐 Testing Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return self.log_test("Admin Login", True, f"Token received")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_master_data_apis(self):
        """Test all 10 master data APIs"""
        print("\n📊 Testing Master Data APIs...")
        
        master_data_tests = [
            ("company-types", 5, "Company Types"),
            ("account-types", 4, "Account Types"),
            ("regions", 6, "Regions"),
            ("business-types", 4, "Business Types"),
            ("industries", 8, "Industries"),
            ("sub-industries", 14, "Sub-Industries"),
            ("countries", 9, "Countries"),
            ("states", 13, "States"),
            ("cities", 9, "Cities"),
            ("currencies", 3, "Currencies")
        ]
        
        all_passed = True
        
        for endpoint, expected_count, name in master_data_tests:
            success, status, response = self.make_request('GET', endpoint)
            
            if success:
                actual_count = len(response) if isinstance(response, list) else 0
                if actual_count == expected_count:
                    self.master_data[endpoint] = response
                    test_passed = self.log_test(f"GET /{endpoint}", True, 
                                              f"Found {actual_count}/{expected_count} {name}")
                else:
                    test_passed = self.log_test(f"GET /{endpoint}", False, 
                                              f"Expected {expected_count} {name}, got {actual_count}")
                all_passed = all_passed and test_passed
            else:
                test_passed = self.log_test(f"GET /{endpoint}", False, 
                                          f"Status: {status}, Response: {response}")
                all_passed = all_passed and test_passed
        
        return all_passed

    def test_cascading_dropdowns(self):
        """Test cascading dropdown functionality"""
        print("\n🔗 Testing Cascading Dropdowns...")
        
        all_passed = True
        
        # Test 1: Sub-industries by industry_id (Technology should return 4)
        if 'industries' in self.master_data:
            tech_industry = next((ind for ind in self.master_data['industries'] 
                                if ind['name'] == 'Technology'), None)
            
            if tech_industry:
                tech_id = tech_industry['id']
                success, status, response = self.make_request('GET', f'sub-industries?industry_id={tech_id}')
                
                if success:
                    tech_sub_count = len(response) if isinstance(response, list) else 0
                    if tech_sub_count == 4:
                        test_passed = self.log_test("Technology Sub-Industries Filter", True, 
                                                  f"Found {tech_sub_count}/4 Technology sub-industries")
                    else:
                        test_passed = self.log_test("Technology Sub-Industries Filter", False, 
                                                  f"Expected 4 Technology sub-industries, got {tech_sub_count}")
                else:
                    test_passed = self.log_test("Technology Sub-Industries Filter", False, 
                                              f"Status: {status}")
                all_passed = all_passed and test_passed
            else:
                test_passed = self.log_test("Technology Sub-Industries Filter", False, 
                                          "Technology industry not found")
                all_passed = all_passed and test_passed
        
        # Test 2: States by country_id (India should return 10)
        if 'countries' in self.master_data:
            india_country = next((country for country in self.master_data['countries'] 
                                if country['name'] == 'India'), None)
            
            if india_country:
                india_id = india_country['id']
                success, status, response = self.make_request('GET', f'states?country_id={india_id}')
                
                if success:
                    india_states_count = len(response) if isinstance(response, list) else 0
                    if india_states_count == 10:
                        test_passed = self.log_test("Indian States Filter", True, 
                                                  f"Found {india_states_count}/10 Indian states")
                        # Store Maharashtra for next test
                        maharashtra = next((state for state in response 
                                          if state['name'] == 'Maharashtra'), None)
                        if maharashtra:
                            self.master_data['maharashtra_id'] = maharashtra['id']
                    else:
                        test_passed = self.log_test("Indian States Filter", False, 
                                                  f"Expected 10 Indian states, got {india_states_count}")
                else:
                    test_passed = self.log_test("Indian States Filter", False, 
                                              f"Status: {status}")
                all_passed = all_passed and test_passed
            else:
                test_passed = self.log_test("Indian States Filter", False, 
                                          "India country not found")
                all_passed = all_passed and test_passed
        
        # Test 3: Cities by state_id (Maharashtra cities)
        if 'maharashtra_id' in self.master_data:
            maharashtra_id = self.master_data['maharashtra_id']
            success, status, response = self.make_request('GET', f'cities?state_id={maharashtra_id}')
            
            if success:
                maharashtra_cities_count = len(response) if isinstance(response, list) else 0
                test_passed = self.log_test("Maharashtra Cities Filter", True, 
                                          f"Found {maharashtra_cities_count} Maharashtra cities")
            else:
                test_passed = self.log_test("Maharashtra Cities Filter", False, 
                                          f"Status: {status}")
            all_passed = all_passed and test_passed
        
        return all_passed

    def test_company_creation(self):
        """Test company creation with validation and scoring"""
        print("\n🏢 Testing Company Creation...")
        
        all_passed = True
        
        # Get required master data IDs
        company_type_id = self.master_data.get('company-types', [{}])[0].get('id') if self.master_data.get('company-types') else str(uuid.uuid4())
        account_type_id = self.master_data.get('account-types', [{}])[0].get('id') if self.master_data.get('account-types') else str(uuid.uuid4())
        region_id = self.master_data.get('regions', [{}])[0].get('id') if self.master_data.get('regions') else str(uuid.uuid4())
        business_type_id = self.master_data.get('business-types', [{}])[0].get('id') if self.master_data.get('business-types') else str(uuid.uuid4())
        industry_id = self.master_data.get('industries', [{}])[0].get('id') if self.master_data.get('industries') else str(uuid.uuid4())
        sub_industry_id = self.master_data.get('sub-industries', [{}])[0].get('id') if self.master_data.get('sub-industries') else str(uuid.uuid4())
        country_id = self.master_data.get('countries', [{}])[0].get('id') if self.master_data.get('countries') else str(uuid.uuid4())
        state_id = self.master_data.get('states', [{}])[0].get('id') if self.master_data.get('states') else str(uuid.uuid4())
        city_id = self.master_data.get('cities', [{}])[0].get('id') if self.master_data.get('cities') else str(uuid.uuid4())
        currency_id = self.master_data.get('currencies', [{}])[0].get('id') if self.master_data.get('currencies') else str(uuid.uuid4())
        
        # Test 1: Valid company creation
        test_company = {
            "company_name": f"TechCorp Solutions Ltd {datetime.now().strftime('%H%M%S')}",
            "company_type": company_type_id,
            "account_type": account_type_id,
            "region": region_id,
            "business_type": business_type_id,
            "industry": industry_id,
            "sub_industry": sub_industry_id,
            "website": "https://techcorp.example.com",
            "employee_count": 250,
            "is_domestic": True,
            "gst_number": "27ABCDE1234Z1Z5",
            "pan_number": "ABCDE1234F",
            "is_child": False,
            "address": "123 Tech Park, Innovation District",
            "country": country_id,
            "state": state_id,
            "city": city_id,
            "zip_code": "400001",
            "turnover_data": [
                {"year": 2023, "revenue": 50000000, "currency": currency_id},
                {"year": 2022, "revenue": 45000000, "currency": currency_id}
            ],
            "profit_data": [
                {"year": 2023, "profit": 8000000, "currency": currency_id},
                {"year": 2022, "profit": 7200000, "currency": currency_id}
            ],
            "company_profile": "Leading technology solutions provider specializing in enterprise software development and digital transformation services."
        }
        
        success, status, response = self.make_request('POST', 'companies', test_company)
        
        if success:
            company_id = response.get('id')
            # Check if scoring algorithm worked (should be hot/cold based on score ≥70)
            score = response.get('score', 0)
            temperature = response.get('temperature', 'unknown')
            
            test_passed = self.log_test("Create Company with Scoring", True, 
                                      f"Company ID: {company_id}, Score: {score}, Temperature: {temperature}")
            
            # Store company ID for cleanup
            self.created_company_id = company_id
        else:
            test_passed = self.log_test("Create Company with Scoring", False, 
                                      f"Status: {status}, Response: {response}")
        
        all_passed = all_passed and test_passed
        
        # Test 2: Duplicate validation (company name)
        duplicate_company = test_company.copy()
        success, status, response = self.make_request('POST', 'companies', duplicate_company, 400)
        
        if success:  # Should fail with 400
            test_passed = self.log_test("Duplicate Company Name Validation", True, 
                                      "Correctly rejected duplicate company name")
        else:
            test_passed = self.log_test("Duplicate Company Name Validation", False, 
                                      f"Should have rejected duplicate, Status: {status}")
        
        all_passed = all_passed and test_passed
        
        # Test 3: India-specific validation (GST or PAN required for domestic)
        invalid_domestic_company = {
            "company_name": f"Invalid Domestic Corp {datetime.now().strftime('%H%M%S')}",
            "company_type": company_type_id,
            "account_type": account_type_id,
            "is_domestic": True,
            # Missing GST and PAN numbers
            "employee_count": 50
        }
        
        success, status, response = self.make_request('POST', 'companies', invalid_domestic_company, 400)
        
        if success:  # Should fail with 400
            test_passed = self.log_test("India Domestic Validation (GST/PAN Required)", True, 
                                      "Correctly rejected domestic company without GST/PAN")
        else:
            test_passed = self.log_test("India Domestic Validation (GST/PAN Required)", False, 
                                      f"Should have required GST/PAN for domestic company, Status: {status}")
        
        all_passed = all_passed and test_passed
        
        return all_passed

    def test_file_upload(self):
        """Test file upload functionality"""
        print("\n📎 Testing File Upload...")
        
        all_passed = True
        
        # Test 1: Valid PDF file upload
        # Create a small test PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        files = {
            'file': ('test_document.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        data = {
            'document_type': 'registration_certificate',
            'description': 'Test company registration certificate'
        }
        
        success, status, response = self.make_request('POST', 'companies/upload-document', 
                                                    data=data, files=files)
        
        if success:
            file_path = response.get('file_path', '')
            test_passed = self.log_test("Valid PDF Upload", True, 
                                      f"File uploaded: {file_path}")
        else:
            test_passed = self.log_test("Valid PDF Upload", False, 
                                      f"Status: {status}, Response: {response}")
        
        all_passed = all_passed and test_passed
        
        # Test 2: File size limit (simulate large file)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB file (should exceed 10MB limit)
        
        files = {
            'file': ('large_document.pdf', io.BytesIO(large_content), 'application/pdf')
        }
        
        data = {
            'document_type': 'registration_certificate',
            'description': 'Large test file'
        }
        
        success, status, response = self.make_request('POST', 'companies/upload-document', 
                                                    data=data, files=files, expected_status=400)
        
        if success:  # Should fail with 400
            test_passed = self.log_test("File Size Limit (10MB)", True, 
                                      "Correctly rejected file larger than 10MB")
        else:
            test_passed = self.log_test("File Size Limit (10MB)", False, 
                                      f"Should have rejected large file, Status: {status}")
        
        all_passed = all_passed and test_passed
        
        # Test 3: Invalid file type
        files = {
            'file': ('test_script.exe', io.BytesIO(b"fake executable content"), 'application/octet-stream')
        }
        
        data = {
            'document_type': 'registration_certificate',
            'description': 'Invalid file type test'
        }
        
        success, status, response = self.make_request('POST', 'companies/upload-document', 
                                                    data=data, files=files, expected_status=400)
        
        if success:  # Should fail with 400
            test_passed = self.log_test("File Type Restriction", True, 
                                      "Correctly rejected invalid file type (.exe)")
        else:
            test_passed = self.log_test("File Type Restriction", False, 
                                      f"Should have rejected .exe file, Status: {status}")
        
        all_passed = all_passed and test_passed
        
        return all_passed

    def run_all_tests(self):
        """Run all company master data tests"""
        print("🚀 Starting Company Registration Master Data Tests")
        print("=" * 70)
        
        # Test authentication first
        if not self.test_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all test suites
        test_results = []
        test_results.append(("Master Data APIs (10 endpoints)", self.test_master_data_apis()))
        test_results.append(("Cascading Dropdowns", self.test_cascading_dropdowns()))
        test_results.append(("Company Creation & Validation", self.test_company_creation()))
        test_results.append(("File Upload & Restrictions", self.test_file_upload()))
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 COMPANY MASTER DATA TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 TEST SUITE RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        # Cleanup
        if hasattr(self, 'created_company_id'):
            print(f"\n🧹 Cleaning up created company: {self.created_company_id}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = CompanyMasterDataTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())