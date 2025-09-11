#!/usr/bin/env python3
"""
Lead-to-Opportunity Conversion Test
Testing the lead conversion workflow to create opportunities
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

class LeadConversionTester:
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
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
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
                    f"User: {user_data.get('username')}, Role ID: {user_data.get('role_id')}"
                )
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def check_existing_opportunities(self):
        """Check if there are existing opportunities in the database"""
        print("\n🎯 CHECKING EXISTING OPPORTUNITIES")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and object responses
                opportunities = data.get('opportunities', []) if isinstance(data, dict) else data
                count = len(opportunities)
                
                self.log_test(
                    "Existing Opportunities Check", 
                    True, 
                    f"Found {count} existing opportunities"
                )
                
                if count > 0:
                    print("   📋 Existing Opportunities:")
                    for i, opp in enumerate(opportunities[:5]):  # Show first 5
                        opp_id = opp.get('opportunity_id', opp.get('id', 'Unknown'))
                        title = opp.get('project_title', opp.get('name', 'Unknown'))
                        stage = opp.get('current_stage', opp.get('stage', 'Unknown'))
                        print(f"      {i+1}. {opp_id}: {title} (Stage: {stage})")
                
                return opportunities
            else:
                self.log_test("Existing Opportunities Check", False, f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Existing Opportunities Check", False, f"Exception: {str(e)}")
            return []
    
    def check_existing_leads(self):
        """Check if there are existing leads that can be converted"""
        print("\n📋 CHECKING EXISTING LEADS")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/leads",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and object responses
                leads = data.get('leads', []) if isinstance(data, dict) else data
                count = len(leads)
                
                self.log_test(
                    "Existing Leads Check", 
                    True, 
                    f"Found {count} existing leads"
                )
                
                if count > 0:
                    print("   📋 Existing Leads:")
                    approved_leads = []
                    for i, lead in enumerate(leads[:10]):  # Show first 10
                        lead_id = lead.get('lead_id', lead.get('id', 'Unknown'))
                        title = lead.get('project_title', lead.get('title', 'Unknown'))
                        status = lead.get('status', 'Unknown')
                        converted = lead.get('converted_to_opportunity', False)
                        
                        print(f"      {i+1}. {lead_id}: {title} (Status: {status}, Converted: {converted})")
                        
                        if status == 'approved' and not converted:
                            approved_leads.append(lead)
                    
                    print(f"   ✅ Found {len(approved_leads)} approved leads ready for conversion")
                    return leads, approved_leads
                else:
                    return [], []
            else:
                self.log_test("Existing Leads Check", False, f"Status: {response.status_code}")
                return [], []
                
        except Exception as e:
            self.log_test("Existing Leads Check", False, f"Exception: {str(e)}")
            return [], []
    
    def create_test_lead(self):
        """Create a test lead for conversion"""
        print("\n🏗️  CREATING TEST LEAD")
        print("=" * 50)
        
        try:
            # Get required master data
            companies_response = requests.get(f"{self.base_url}/companies", headers=self.headers, timeout=10)
            product_services_response = requests.get(f"{self.base_url}/product-services", headers=self.headers, timeout=10)
            sub_tender_types_response = requests.get(f"{self.base_url}/sub-tender-types", headers=self.headers, timeout=10)
            
            if companies_response.status_code != 200:
                self.log_test("Create Test Lead (Setup)", False, "Could not get companies data")
                return None
            
            companies = companies_response.json()
            product_services = product_services_response.json() if product_services_response.status_code == 200 else []
            sub_tender_types = sub_tender_types_response.json() if sub_tender_types_response.status_code == 200 else []
            
            if not companies:
                self.log_test("Create Test Lead (Setup)", False, "No companies available")
                return None
            
            # Create lead data
            lead_data = {
                "tender_type": "Tender",
                "billing_type": "Fixed Price",
                "sub_tender_type_id": sub_tender_types[0]['id'] if sub_tender_types else "default-sub-tender",
                "project_title": "Test Lead for Opportunity Conversion",
                "company_id": companies[0]['id'],
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website",
                "product_service_id": product_services[0]['id'] if product_services else "default-product",
                "expected_orc": 500000,
                "revenue": 500000,
                "lead_owner": "admin"
            }
            
            response = requests.post(
                f"{self.base_url}/leads",
                headers=self.headers,
                json=lead_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                lead_id = data.get('lead_id', data.get('id'))
                
                self.log_test(
                    "Create Test Lead", 
                    True, 
                    f"Created lead with ID: {lead_id}"
                )
                return data
            else:
                self.log_test("Create Test Lead", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Lead", False, f"Exception: {str(e)}")
            return None
    
    def approve_lead(self, lead_id):
        """Approve a lead so it can be converted"""
        print(f"\n✅ APPROVING LEAD {lead_id}")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.base_url}/leads/{lead_id}/status",
                headers=self.headers,
                json={"status": "approved"},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test(
                    f"Approve Lead {lead_id}", 
                    True, 
                    "Lead approved successfully"
                )
                return True
            else:
                self.log_test(f"Approve Lead {lead_id}", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(f"Approve Lead {lead_id}", False, f"Exception: {str(e)}")
            return False
    
    def convert_lead_to_opportunity(self, lead_id):
        """Convert an approved lead to opportunity"""
        print(f"\n🔄 CONVERTING LEAD {lead_id} TO OPPORTUNITY")
        print("=" * 50)
        
        try:
            # Convert lead with opportunity_date parameter
            opportunity_date = datetime.now().strftime("%Y-%m-%d")
            
            response = requests.post(
                f"{self.base_url}/leads/{lead_id}/convert",
                headers=self.headers,
                params={"opportunity_date": opportunity_date},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                opportunity_id = data.get('opportunity_id')
                
                self.log_test(
                    f"Convert Lead {lead_id}", 
                    True, 
                    f"Successfully converted to opportunity: {opportunity_id}"
                )
                return opportunity_id
            else:
                self.log_test(f"Convert Lead {lead_id}", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test(f"Convert Lead {lead_id}", False, f"Exception: {str(e)}")
            return None
    
    def verify_opportunity_creation(self, opportunity_id):
        """Verify that the opportunity was created successfully"""
        print(f"\n🔍 VERIFYING OPPORTUNITY {opportunity_id}")
        print("=" * 50)
        
        try:
            # Check if opportunity appears in opportunities list
            list_response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if list_response.status_code == 200:
                data = list_response.json()
                opportunities = data.get('opportunities', []) if isinstance(data, dict) else data
                
                # Look for our opportunity
                found_opportunity = None
                for opp in opportunities:
                    if opp.get('opportunity_id') == opportunity_id or opp.get('id') == opportunity_id:
                        found_opportunity = opp
                        break
                
                if found_opportunity:
                    self.log_test(
                        f"Verify Opportunity in List", 
                        True, 
                        f"Opportunity {opportunity_id} found in opportunities list"
                    )
                    
                    # Test individual opportunity access
                    self.test_individual_opportunity_access(opportunity_id)
                    
                    return True
                else:
                    self.log_test(f"Verify Opportunity in List", False, f"Opportunity {opportunity_id} not found in list")
                    return False
            else:
                self.log_test(f"Verify Opportunity in List", False, f"Could not get opportunities list: {list_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(f"Verify Opportunity {opportunity_id}", False, f"Exception: {str(e)}")
            return False
    
    def test_individual_opportunity_access(self, opportunity_id):
        """Test accessing individual opportunity by ID"""
        try:
            response = requests.get(
                f"{self.base_url}/opportunities/{opportunity_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                project_title = data.get('project_title', data.get('name', 'Unknown'))
                stage = data.get('current_stage', data.get('stage', 'Unknown'))
                
                self.log_test(
                    f"Individual Opportunity Access", 
                    True, 
                    f"Successfully accessed {opportunity_id}: {project_title} (Stage: {stage})"
                )
            else:
                self.log_test(f"Individual Opportunity Access", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test(f"Individual Opportunity Access", False, f"Exception: {str(e)}")
    
    def test_specific_opportunity_ids(self):
        """Test the specific opportunity IDs mentioned in the review request"""
        print("\n🔍 TESTING SPECIFIC OPPORTUNITY IDs FROM REVIEW REQUEST")
        print("=" * 60)
        
        specific_ids = ["POT-RA6G5J6I", "OPP-IGDMLHW", "OPP-712984"]
        
        for opp_id in specific_ids:
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{opp_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    project_title = data.get('project_title', data.get('name', 'Unknown'))
                    
                    self.log_test(
                        f"Access {opp_id}", 
                        True, 
                        f"✅ ACCESSIBLE - {project_title}"
                    )
                elif response.status_code == 404:
                    self.log_test(f"Access {opp_id}", False, "❌ 404 NOT FOUND - Opportunity does not exist in database")
                else:
                    self.log_test(f"Access {opp_id}", False, f"❌ ERROR - Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Access {opp_id}", False, f"❌ EXCEPTION - {str(e)}")
    
    def run_complete_test(self):
        """Run the complete lead-to-opportunity conversion test"""
        print("🚀 STARTING LEAD-TO-OPPORTUNITY CONVERSION TEST")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed")
            return False
        
        # Step 2: Check existing opportunities
        existing_opportunities = self.check_existing_opportunities()
        
        # Step 3: Check existing leads
        all_leads, approved_leads = self.check_existing_leads()
        
        # Step 4: Test specific opportunity IDs from review request
        self.test_specific_opportunity_ids()
        
        # Step 5: Create and convert a lead if needed
        if len(approved_leads) == 0:
            print("\n📝 No approved leads found, creating test lead...")
            test_lead = self.create_test_lead()
            
            if test_lead:
                lead_id = test_lead.get('id')
                
                # Approve the lead
                if self.approve_lead(lead_id):
                    # Convert to opportunity
                    opportunity_id = self.convert_lead_to_opportunity(lead_id)
                    
                    if opportunity_id:
                        # Verify the conversion
                        self.verify_opportunity_creation(opportunity_id)
        else:
            print(f"\n✅ Found {len(approved_leads)} approved leads, converting first one...")
            lead_to_convert = approved_leads[0]
            lead_id = lead_to_convert.get('id')
            
            opportunity_id = self.convert_lead_to_opportunity(lead_id)
            if opportunity_id:
                self.verify_opportunity_creation(opportunity_id)
        
        # Print summary
        self.print_summary()
        
        return self.passed_tests > (self.total_tests * 0.7)  # 70% success rate
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 LEAD-TO-OPPORTUNITY CONVERSION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 70:
            print("\n🎉 LEAD-TO-OPPORTUNITY CONVERSION WORKING!")
        else:
            print(f"\n⚠️  CONVERSION ISSUES DETECTED")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(result)

def main():
    """Main function"""
    tester = LeadConversionTester()
    success = tester.run_complete_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()