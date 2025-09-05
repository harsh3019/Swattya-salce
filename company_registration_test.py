#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class CompanyRegistrationTester:
    def __init__(self, base_url="https://swayatta-admin.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {}  # Track created items for cleanup
        self.master_data = {}  # Store master data for testing

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            return success, response.status_code, response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}
        except json.JSONDecodeError:
            return False, response.status_code, {"error": "Invalid JSON response"}

    def test_login(self):
        """Test admin login functionality"""
        print("\n🔐 Testing Admin Authentication...")
        
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return self.log_test("Admin Login", True, f"Token received")
        else:
            return self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")

    def test_master_data_endpoints(self):
        """Test all master data endpoints with admin authentication"""
        print("\n📊 Testing Master Data Endpoints...")
        
        master_endpoints = [
            ("company-types", "Company Types"),
            ("account-types", "Account Types"),
            ("regions", "Regions"),
            ("business-types", "Business Types"),
            ("industries", "Industries"),
            ("sub-industries", "Sub Industries"),
            ("countries", "Countries"),
            ("states", "States"),
            ("cities", "Cities"),
            ("currencies", "Currencies")
        ]
        
        all_passed = True
        
        for endpoint, name in master_endpoints:
            success, status, response = self.make_request('GET', endpoint)
            if success:
                count = len(response) if isinstance(response, list) else 0
                self.master_data[endpoint] = response
                test_passed = self.log_test(f"GET {name}", True, f"Found {count} records")
            else:
                test_passed = self.log_test(f"GET {name}", False, f"Status: {status}")
                all_passed = False
            
            if not test_passed:
                all_passed = False
        
        return all_passed

    def test_filtered_master_data(self):
        """Test master data endpoints with filters"""
        print("\n🔍 Testing Filtered Master Data...")
        
        all_passed = True
        
        # Test sub-industries with industry filter
        if 'industries' in self.master_data and self.master_data['industries']:
            industry_id = self.master_data['industries'][0]['id']
            success, status, response = self.make_request('GET', f'sub-industries?industry_id={industry_id}')
            if success:
                count = len(response) if isinstance(response, list) else 0
                test_passed = self.log_test("GET Sub-Industries with filter", True, f"Found {count} records for industry")
            else:
                test_passed = self.log_test("GET Sub-Industries with filter", False, f"Status: {status}")
            all_passed = all_passed and test_passed
        
        # Test states with country filter
        if 'countries' in self.master_data and self.master_data['countries']:
            country_id = self.master_data['countries'][0]['id']
            success, status, response = self.make_request('GET', f'states?country_id={country_id}')
            if success:
                count = len(response) if isinstance(response, list) else 0
                test_passed = self.log_test("GET States with filter", True, f"Found {count} records for country")
            else:
                test_passed = self.log_test("GET States with filter", False, f"Status: {status}")
            all_passed = all_passed and test_passed
        
        # Test cities with state filter
        if 'states' in self.master_data and self.master_data['states']:
            state_id = self.master_data['states'][0]['id']
            success, status, response = self.make_request('GET', f'cities?state_id={state_id}')
            if success:
                count = len(response) if isinstance(response, list) else 0
                test_passed = self.log_test("GET Cities with filter", True, f"Found {count} records for state")
            else:
                test_passed = self.log_test("GET Cities with filter", False, f"Status: {status}")
            all_passed = all_passed and test_passed
        
        return all_passed

    def test_company_rbac(self):
        """Test RBAC for company endpoints"""
        print("\n🔒 Testing Company RBAC...")
        
        all_passed = True
        
        # Test GET companies (should work for admin)
        success, status, response = self.make_request('GET', 'companies')
        if success:
            count = len(response) if isinstance(response, list) else 0
            test_passed = self.log_test("GET Companies (Admin)", True, f"Found {count} companies")
        else:
            test_passed = self.log_test("GET Companies (Admin)", False, f"Status: {status}")
        all_passed = all_passed and test_passed
        
        return all_passed

    def create_test_company_data(self):
        """Create test company data using master data"""
        if not all(key in self.master_data for key in ['company-types', 'account-types', 'regions', 
                                                      'business-types', 'industries', 'sub-industries',
                                                      'countries', 'states', 'cities']):
            return None
        
        # Get first available IDs from master data
        company_type_id = self.master_data['company-types'][0]['id'] if self.master_data['company-types'] else str(uuid.uuid4())
        account_type_id = self.master_data['account-types'][0]['id'] if self.master_data['account-types'] else str(uuid.uuid4())
        region_id = self.master_data['regions'][0]['id'] if self.master_data['regions'] else str(uuid.uuid4())
        business_type_id = self.master_data['business-types'][0]['id'] if self.master_data['business-types'] else str(uuid.uuid4())
        industry_id = self.master_data['industries'][0]['id'] if self.master_data['industries'] else str(uuid.uuid4())
        sub_industry_id = self.master_data['sub-industries'][0]['id'] if self.master_data['sub-industries'] else str(uuid.uuid4())
        country_id = self.master_data['countries'][0]['id'] if self.master_data['countries'] else str(uuid.uuid4())
        state_id = self.master_data['states'][0]['id'] if self.master_data['states'] else str(uuid.uuid4())
        city_id = self.master_data['cities'][0]['id'] if self.master_data['cities'] else str(uuid.uuid4())
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        return {
            "name": f"TechCorp Solutions Pvt Ltd {timestamp}",
            "domestic_international": "Domestic",
            "gst_number": f"27ABCDE{timestamp}Z1Z5",
            "pan_number": f"ABCDE{timestamp}F",
            "company_type_id": company_type_id,
            "account_type_id": account_type_id,
            "region_id": region_id,
            "business_type_id": business_type_id,
            "industry_id": industry_id,
            "sub_industry_id": sub_industry_id,
            "website": f"https://techcorp{timestamp}.com",
            "is_child": False,
            "employee_count": 150,
            "address": f"Tech Park, Sector 5, Electronic City, Bangalore - 560100",
            "country_id": country_id,
            "state_id": state_id,
            "city_id": city_id,
            "turnover": [
                {
                    "year": 2023,
                    "revenue": 5000000.0,
                    "currency": "INR"
                }
            ],
            "profit": [
                {
                    "year": 2023,
                    "profit": 750000.0,
                    "currency": "INR"
                }
            ],
            "annual_revenue": 5000000.0,
            "revenue_currency": "INR",
            "company_profile": "Leading technology solutions provider specializing in enterprise software development.",
            "valid_gst": True,
            "active_status": True,
            "parent_linkage_valid": True
        }

    def test_company_creation(self):
        """Test company creation with validation"""
        print("\n🏢 Testing Company Creation...")
        
        test_company = self.create_test_company_data()
        if not test_company:
            return self.log_test("Company Creation", False, "Could not create test data - missing master data")
        
        success, status, response = self.make_request('POST', 'companies', test_company)
        if success:
            company_id = response.get('id')
            self.created_items['company_id'] = company_id
            
            # Verify scoring algorithm
            score = response.get('score', 0)
            lead_status = response.get('lead_status', '')
            
            score_test = self.log_test("Company Scoring Algorithm", 
                                     isinstance(score, int) and 0 <= score <= 100,
                                     f"Score: {score}")
            
            lead_status_test = self.log_test("Lead Status Assignment", 
                                           lead_status in ['hot', 'cold'],
                                           f"Status: {lead_status}")
            
            creation_test = self.log_test("Company Creation", True, f"Company ID: {company_id}")
            
            return creation_test and score_test and lead_status_test
        else:
            return self.log_test("Company Creation", False, f"Status: {status}, Response: {response}")

    def test_company_validation(self):
        """Test company validation rules"""
        print("\n✅ Testing Company Validation...")
        
        all_passed = True
        
        # Test duplicate company name validation
        if 'company_id' in self.created_items:
            duplicate_company = self.create_test_company_data()
            if duplicate_company:
                # Use same name as previously created company
                success, status, response = self.make_request('GET', f"companies/{self.created_items['company_id']}")
                if success:
                    duplicate_company['name'] = response.get('name', duplicate_company['name'])
                    
                    success, status, response = self.make_request('POST', 'companies', duplicate_company, 400)
                    test_passed = self.log_test("Duplicate Company Name Validation", success, 
                                              f"Correctly rejected duplicate name")
                    all_passed = all_passed and test_passed
        
        # Test India-specific GST/PAN requirements
        domestic_company_no_gst_pan = self.create_test_company_data()
        if domestic_company_no_gst_pan:
            domestic_company_no_gst_pan['gst_number'] = None
            domestic_company_no_gst_pan['pan_number'] = None
            domestic_company_no_gst_pan['name'] = f"Test No GST PAN {datetime.now().strftime('%H%M%S')}"
            
            success, status, response = self.make_request('POST', 'companies', domestic_company_no_gst_pan, 400)
            test_passed = self.log_test("India GST/PAN Validation", success, 
                                      "Correctly rejected domestic company without GST/PAN")
            all_passed = all_passed and test_passed
        
        return all_passed

    def test_company_scoring_algorithm(self):
        """Test company scoring algorithm with different scenarios"""
        print("\n🎯 Testing Company Scoring Algorithm...")
        
        all_passed = True
        
        # Test high-value company (should get hot status)
        high_value_company = self.create_test_company_data()
        if high_value_company:
            high_value_company['name'] = f"HighValue Corp {datetime.now().strftime('%H%M%S')}"
            high_value_company['annual_revenue'] = 15000000.0  # 15M
            high_value_company['employee_count'] = 1500
            high_value_company['gst_number'] = f"27HIVAL{datetime.now().strftime('%H%M%S')}Z1Z5"
            high_value_company['pan_number'] = f"HIVAL{datetime.now().strftime('%H%M%S')}F"
            
            success, status, response = self.make_request('POST', 'companies', high_value_company)
            if success:
                score = response.get('score', 0)
                lead_status = response.get('lead_status', '')
                
                high_score_test = self.log_test("High Value Company Score", 
                                              score >= 70,
                                              f"Score: {score} (expected >= 70)")
                
                hot_status_test = self.log_test("Hot Lead Status", 
                                              lead_status == 'hot',
                                              f"Status: {lead_status} (expected hot)")
                
                all_passed = all_passed and high_score_test and hot_status_test
                
                # Clean up
                if response.get('id'):
                    self.created_items[f"high_value_company_{response['id']}"] = response['id']
        
        # Test low-value company (should get cold status)
        low_value_company = self.create_test_company_data()
        if low_value_company:
            low_value_company['name'] = f"SmallBiz Corp {datetime.now().strftime('%H%M%S')}"
            low_value_company['annual_revenue'] = 50000.0  # 50K
            low_value_company['employee_count'] = 10
            low_value_company['gst_number'] = f"27SMALL{datetime.now().strftime('%H%M%S')}Z1Z5"
            low_value_company['pan_number'] = f"SMALL{datetime.now().strftime('%H%M%S')}F"
            
            success, status, response = self.make_request('POST', 'companies', low_value_company)
            if success:
                score = response.get('score', 0)
                lead_status = response.get('lead_status', '')
                
                low_score_test = self.log_test("Low Value Company Score", 
                                             score < 70,
                                             f"Score: {score} (expected < 70)")
                
                cold_status_test = self.log_test("Cold Lead Status", 
                                                lead_status == 'cold',
                                                f"Status: {lead_status} (expected cold)")
                
                all_passed = all_passed and low_score_test and cold_status_test
                
                # Clean up
                if response.get('id'):
                    self.created_items[f"low_value_company_{response['id']}"] = response['id']
        
        return all_passed

    def test_company_retrieval(self):
        """Test company retrieval by ID"""
        print("\n📋 Testing Company Retrieval...")
        
        if 'company_id' not in self.created_items:
            return self.log_test("Company Retrieval", False, "No company created for testing")
        
        company_id = self.created_items['company_id']
        success, status, response = self.make_request('GET', f'companies/{company_id}')
        
        if success:
            has_required_fields = all(field in response for field in 
                                    ['id', 'name', 'score', 'lead_status', 'created_at'])
            return self.log_test("Company Retrieval by ID", has_required_fields, 
                               f"Retrieved company with all required fields")
        else:
            return self.log_test("Company Retrieval by ID", False, f"Status: {status}")

    def test_master_data_relationships(self):
        """Test master data relationships"""
        print("\n🔗 Testing Master Data Relationships...")
        
        all_passed = True
        
        # Test states->countries relationship
        if 'states' in self.master_data and self.master_data['states']:
            state = self.master_data['states'][0]
            if 'country_id' in state:
                country_found = any(c['id'] == state['country_id'] 
                                  for c in self.master_data.get('countries', []))
                test_passed = self.log_test("States->Countries Relationship", country_found,
                                          f"State references valid country")
                all_passed = all_passed and test_passed
        
        # Test cities->states relationship
        if 'cities' in self.master_data and self.master_data['cities']:
            city = self.master_data['cities'][0]
            if 'state_id' in city:
                state_found = any(s['id'] == city['state_id'] 
                                for s in self.master_data.get('states', []))
                test_passed = self.log_test("Cities->States Relationship", state_found,
                                          f"City references valid state")
                all_passed = all_passed and test_passed
        
        # Test sub-industries->industries relationship
        if 'sub-industries' in self.master_data and self.master_data['sub-industries']:
            sub_industry = self.master_data['sub-industries'][0]
            if 'industry_id' in sub_industry:
                industry_found = any(i['id'] == sub_industry['industry_id'] 
                                   for i in self.master_data.get('industries', []))
                test_passed = self.log_test("Sub-Industries->Industries Relationship", industry_found,
                                          f"Sub-industry references valid industry")
                all_passed = all_passed and test_passed
        
        return all_passed

    def test_master_data_initialization(self):
        """Verify master data was properly initialized"""
        print("\n🗃️ Testing Master Data Initialization...")
        
        all_passed = True
        
        # Check minimum expected data counts
        expected_minimums = {
            'company-types': 3,
            'account-types': 3,
            'regions': 4,
            'business-types': 4,
            'industries': 4,
            'sub-industries': 8,
            'countries': 5,
            'states': 10,
            'cities': 15,
            'currencies': 3
        }
        
        for endpoint, min_count in expected_minimums.items():
            if endpoint in self.master_data:
                actual_count = len(self.master_data[endpoint])
                test_passed = self.log_test(f"Master Data Count - {endpoint.title()}", 
                                          actual_count >= min_count,
                                          f"Found {actual_count} records (expected >= {min_count})")
                all_passed = all_passed and test_passed
        
        return all_passed

    def cleanup_created_items(self):
        """Clean up created test items"""
        print("\n🧹 Cleaning up test data...")
        
        # Note: Since we don't have delete endpoints for companies in the current implementation,
        # we'll just log what would be cleaned up
        for item_type, item_id in self.created_items.items():
            print(f"   Would clean up {item_type}: {item_id}")

    def run_all_tests(self):
        """Run all company registration tests"""
        print("🚀 Starting Company Registration Backend Tests")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("\n❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all tests
        test_results = []
        test_results.append(("Master Data Endpoints", self.test_master_data_endpoints()))
        test_results.append(("Filtered Master Data", self.test_filtered_master_data()))
        test_results.append(("Master Data Initialization", self.test_master_data_initialization()))
        test_results.append(("Master Data Relationships", self.test_master_data_relationships()))
        test_results.append(("Company RBAC", self.test_company_rbac()))
        test_results.append(("Company Creation", self.test_company_creation()))
        test_results.append(("Company Validation", self.test_company_validation()))
        test_results.append(("Company Scoring Algorithm", self.test_company_scoring_algorithm()))
        test_results.append(("Company Retrieval", self.test_company_retrieval()))
        
        # Cleanup
        self.cleanup_created_items()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 COMPANY REGISTRATION TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 MODULE TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = CompanyRegistrationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())