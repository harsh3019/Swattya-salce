#!/usr/bin/env python3
"""
Company Data Inheritance Testing - Leads to Opportunities
Testing company data flow from leads through conversion to opportunities
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://sawayatta-erp-2.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class CompanyInheritanceTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate as admin user"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", True, "Admin login successful")
                return True
            else:
                self.log_result("Authentication", False, f"Login failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_company_master_data(self):
        """Test 1: GET /api/companies - verify company master data exists"""
        try:
            response = self.session.get(f"{BACKEND_URL}/companies")
            if response.status_code == 200:
                companies = response.json()
                if isinstance(companies, list) and len(companies) > 0:
                    self.log_result("Company Master Data", True, 
                                  f"Found {len(companies)} companies in master data",
                                  {"sample_company": companies[0] if companies else None})
                    return companies
                else:
                    self.log_result("Company Master Data", False, 
                                  "No companies found in master data", 
                                  {"response": companies})
                    return []
            else:
                self.log_result("Company Master Data", False, 
                              f"Companies API failed: {response.status_code}", 
                              {"response": response.text})
                return []
        except Exception as e:
            self.log_result("Company Master Data", False, f"Error accessing companies: {str(e)}")
            return []
    
    def test_leads_company_data(self):
        """Test 2: GET /api/leads - check if leads have company_id field populated"""
        try:
            response = self.session.get(f"{BACKEND_URL}/leads")
            if response.status_code == 200:
                data = response.json()
                # Handle paginated response format
                if isinstance(data, dict) and 'leads' in data:
                    leads = data['leads']
                elif isinstance(data, list):
                    leads = data
                else:
                    self.log_result("Leads Company Data", False, "Invalid leads response format", {"response": data})
                    return []
                
                if leads:
                    leads_with_company = [lead for lead in leads if lead.get('company_id')]
                    total_leads = len(leads)
                    company_leads = len(leads_with_company)
                    
                    self.log_result("Leads Company Data", company_leads > 0, 
                                  f"Found {company_leads}/{total_leads} leads with company_id",
                                  {
                                      "total_leads": total_leads,
                                      "leads_with_company": company_leads,
                                      "sample_lead": leads_with_company[0] if leads_with_company else leads[0] if leads else None
                                  })
                    return leads
                else:
                    self.log_result("Leads Company Data", False, "No leads found in system")
                    return []
            else:
                self.log_result("Leads Company Data", False, 
                              f"Leads API failed: {response.status_code}", 
                              {"response": response.text})
                return []
        except Exception as e:
            self.log_result("Leads Company Data", False, f"Error accessing leads: {str(e)}")
            return []
    
    def create_test_lead_with_company(self, companies):
        """Test 3: Create a new lead with company_id"""
        if not companies:
            self.log_result("Create Test Lead", False, "No companies available for lead creation")
            return None
            
        try:
            # Get required master data first
            product_services = self.session.get(f"{BACKEND_URL}/product-services").json()
            sub_tender_types = self.session.get(f"{BACKEND_URL}/sub-tender-types").json()
            users = self.session.get(f"{BACKEND_URL}/users").json()
            
            if not product_services or not sub_tender_types or not users:
                self.log_result("Create Test Lead", False, "Missing required master data for lead creation")
                return None
            
            # Create test lead with company_id
            test_lead = {
                "tender_type": "Tender",
                "billing_type": "Fixed Price",
                "sub_tender_type_id": sub_tender_types[0]["id"],
                "project_title": f"Company Inheritance Test Lead - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "company_id": companies[0]["id"],  # Use first company
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website",
                "product_service_id": product_services[0]["id"],
                "expected_orc": 500000.0,
                "revenue": 500000.0,
                "lead_owner": users[0]["id"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/leads", json=test_lead)
            if response.status_code == 200 or response.status_code == 201:
                created_lead = response.json()
                lead_id = created_lead.get("id")
                
                # Verify company_id is properly set
                if created_lead.get("company_id") == companies[0]["id"]:
                    self.log_result("Create Test Lead", True, 
                                  f"Lead created successfully with company_id: {lead_id}",
                                  {
                                      "lead_id": lead_id,
                                      "company_id": created_lead.get("company_id"),
                                      "company_name": companies[0].get("company_name")
                                  })
                    return created_lead
                else:
                    self.log_result("Create Test Lead", False, 
                                  "Lead created but company_id not properly set",
                                  {
                                      "expected_company_id": companies[0]["id"],
                                      "actual_company_id": created_lead.get("company_id")
                                  })
                    return created_lead
            else:
                self.log_result("Create Test Lead", False, 
                              f"Lead creation failed: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Create Test Lead", False, f"Error creating lead: {str(e)}")
            return None
    
    def approve_and_convert_lead(self, lead):
        """Test 4: Approve lead and convert to opportunity"""
        if not lead:
            return None
            
        try:
            lead_id = lead["id"]
            
            # Step 1: Approve the lead
            approve_response = self.session.post(f"{BACKEND_URL}/leads/{lead_id}/status", 
                                               params={"status": "approved"})
            
            if approve_response.status_code != 200:
                self.log_result("Lead Approval", False, 
                              f"Lead approval failed: {approve_response.status_code}",
                              {"response": approve_response.text})
                return None
            
            self.log_result("Lead Approval", True, f"Lead {lead_id} approved successfully")
            
            # Step 2: Convert lead to opportunity
            convert_response = self.session.post(f"{BACKEND_URL}/leads/{lead_id}/convert",
                                               params={"opportunity_date": datetime.now().isoformat()})
            
            if convert_response.status_code == 200:
                conversion_result = convert_response.json()
                opportunity_id = conversion_result.get("opportunity_id")
                
                if opportunity_id:
                    self.log_result("Lead to Opportunity Conversion", True, 
                                  f"Lead converted to opportunity: {opportunity_id}",
                                  {
                                      "lead_id": lead_id,
                                      "opportunity_id": opportunity_id,
                                      "original_company_id": lead.get("company_id")
                                  })
                    return opportunity_id
                else:
                    self.log_result("Lead to Opportunity Conversion", False, 
                                  "Conversion succeeded but no opportunity_id returned",
                                  {"response": conversion_result})
                    return None
            else:
                self.log_result("Lead to Opportunity Conversion", False, 
                              f"Lead conversion failed: {convert_response.status_code}",
                              {"response": convert_response.text})
                return None
        except Exception as e:
            self.log_result("Lead to Opportunity Conversion", False, f"Error in conversion: {str(e)}")
            return None
    
    def test_opportunity_company_inheritance(self, opportunity_id, original_company_id, companies):
        """Test 5: Verify opportunity has company_id and company_name resolved"""
        if not opportunity_id:
            return False
            
        try:
            # Get the specific opportunity
            response = self.session.get(f"{BACKEND_URL}/opportunities/{opportunity_id}")
            if response.status_code == 200:
                opportunity = response.json()
                
                # Check if company_id is inherited
                opp_company_id = opportunity.get("company_id")
                if opp_company_id == original_company_id:
                    self.log_result("Opportunity Company ID Inheritance", True, 
                                  f"Company ID properly inherited: {opp_company_id}")
                else:
                    self.log_result("Opportunity Company ID Inheritance", False, 
                                  f"Company ID not inherited correctly",
                                  {
                                      "expected": original_company_id,
                                      "actual": opp_company_id
                                  })
                
                # Check if company name is resolved
                company_name = opportunity.get("company_name")
                if company_name:
                    # Find the expected company name
                    expected_company = next((c for c in companies if c["id"] == original_company_id), None)
                    expected_name = expected_company["company_name"] if expected_company else None
                    
                    if company_name == expected_name:
                        self.log_result("Opportunity Company Name Resolution", True, 
                                      f"Company name properly resolved: {company_name}")
                    else:
                        self.log_result("Opportunity Company Name Resolution", False, 
                                      f"Company name resolution mismatch",
                                      {
                                          "expected": expected_name,
                                          "actual": company_name
                                      })
                else:
                    self.log_result("Opportunity Company Name Resolution", False, 
                                  "Company name not resolved in opportunity",
                                  {"opportunity_data": opportunity})
                
                return True
            else:
                self.log_result("Opportunity Company Inheritance", False, 
                              f"Failed to get opportunity: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Opportunity Company Inheritance", False, f"Error testing inheritance: {str(e)}")
            return False
    
    def test_opportunities_list_company_resolution(self):
        """Test 6: GET /api/opportunities - verify opportunities display company names"""
        try:
            response = self.session.get(f"{BACKEND_URL}/opportunities")
            if response.status_code == 200:
                opportunities = response.json()
                if isinstance(opportunities, list) and len(opportunities) > 0:
                    # Check how many opportunities have company information
                    opps_with_company_id = [opp for opp in opportunities if opp.get('company_id')]
                    opps_with_company_name = [opp for opp in opportunities if opp.get('company_name')]
                    
                    total_opps = len(opportunities)
                    company_id_count = len(opps_with_company_id)
                    company_name_count = len(opps_with_company_name)
                    
                    self.log_result("Opportunities Company Resolution", 
                                  company_name_count > 0,
                                  f"Company resolution: {company_name_count}/{total_opps} opportunities have company names, {company_id_count}/{total_opps} have company IDs",
                                  {
                                      "total_opportunities": total_opps,
                                      "with_company_id": company_id_count,
                                      "with_company_name": company_name_count,
                                      "sample_opportunity": opportunities[0] if opportunities else None
                                  })
                    return opportunities
                else:
                    self.log_result("Opportunities Company Resolution", False, 
                                  "No opportunities found for testing company resolution")
                    return []
            else:
                self.log_result("Opportunities Company Resolution", False, 
                              f"Opportunities API failed: {response.status_code}",
                              {"response": response.text})
                return []
        except Exception as e:
            self.log_result("Opportunities Company Resolution", False, f"Error testing opportunities: {str(e)}")
            return []
    
    def run_comprehensive_test(self):
        """Run all company inheritance tests"""
        print("🔍 COMPANY DATA INHERITANCE TESTING - LEADS TO OPPORTUNITIES")
        print("=" * 70)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test company master data
        companies = self.test_company_master_data()
        
        # Step 3: Test existing leads company data
        leads = self.test_leads_company_data()
        
        # Step 4: Create test lead with company
        test_lead = self.create_test_lead_with_company(companies)
        
        # Step 5: Approve and convert lead
        opportunity_id = self.approve_and_convert_lead(test_lead)
        
        # Step 6: Test opportunity company inheritance
        if test_lead and opportunity_id:
            self.test_opportunity_company_inheritance(opportunity_id, test_lead.get("company_id"), companies)
        
        # Step 7: Test opportunities list company resolution
        self.test_opportunities_list_company_resolution()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = CompanyInheritanceTest()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)