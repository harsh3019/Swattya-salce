#!/usr/bin/env python3
"""
Data Seeding Script for Opportunity Testing
Creates sample companies, leads, and converts them to opportunities with specific IDs
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://1b435344-f8f5-4a8b-98d4-64db783ac8b5.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

# Target opportunity IDs from the review request
TARGET_OPPORTUNITY_IDS = ["POT-RA6G5J6I", "OPP-IGDMLHW", "OPP-712984"]

class DataSeeder:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.created_companies = []
        self.created_leads = []
        self.created_opportunities = []
        
    def authenticate(self):
        """Authenticate as admin"""
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
                print("✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    def get_master_data(self):
        """Get required master data"""
        print("\n📊 Getting master data...")
        
        try:
            # Get master data
            endpoints = {
                'company_types': '/company-types',
                'account_types': '/account-types', 
                'regions': '/regions',
                'business_types': '/business-types',
                'industries': '/industries',
                'countries': '/countries',
                'states': '/states',
                'cities': '/cities',
                'currencies': '/currencies',
                'product_services': '/product-services',
                'sub_tender_types': '/sub-tender-types'
            }
            
            self.master_data = {}
            
            for key, endpoint in endpoints.items():
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.master_data[key] = data
                    print(f"   ✅ {key}: {len(data)} items")
                else:
                    print(f"   ❌ {key}: Failed to get data")
                    self.master_data[key] = []
            
            return True
            
        except Exception as e:
            print(f"❌ Error getting master data: {str(e)}")
            return False
    
    def create_sample_companies(self):
        """Create sample companies for testing"""
        print("\n🏢 Creating sample companies...")
        
        if not self.master_data.get('company_types') or not self.master_data.get('countries'):
            print("❌ Missing required master data for companies")
            return False
        
        company_type = self.master_data['company_types'][0] if self.master_data['company_types'] else None
        country = self.master_data['countries'][0] if self.master_data['countries'] else None
        state = self.master_data['states'][0] if self.master_data['states'] else None
        city = self.master_data['cities'][0] if self.master_data['cities'] else None
        
        sample_companies = [
            {
                "company_name": "TechCorp Solutions Pvt Ltd",
                "company_type_id": company_type['id'] if company_type else "default-type",
                "website": "https://techcorp.com",
                "employee_count": 500,
                "is_domestic": True,
                "gst_number": "27ABCDE1234F1Z5",
                "pan_number": "ABCDE1234F",
                "address": "Tech Park, Sector 5",
                "country_id": country['id'] if country else "default-country",
                "state_id": state['id'] if state else "default-state", 
                "city_id": city['id'] if city else "default-city",
                "zip_code": "400001"
            },
            {
                "company_name": "InnovateTech Industries",
                "company_type_id": company_type['id'] if company_type else "default-type",
                "website": "https://innovatetech.com",
                "employee_count": 250,
                "is_domestic": True,
                "gst_number": "27FGHIJ5678K2L6",
                "pan_number": "FGHIJ5678K",
                "address": "Innovation Hub, Block A",
                "country_id": country['id'] if country else "default-country",
                "state_id": state['id'] if state else "default-state",
                "city_id": city['id'] if city else "default-city", 
                "zip_code": "400002"
            },
            {
                "company_name": "Digital Solutions Ltd",
                "company_type_id": company_type['id'] if company_type else "default-type",
                "website": "https://digitalsolutions.com",
                "employee_count": 150,
                "is_domestic": True,
                "gst_number": "27MNOPQ9012R3S7",
                "pan_number": "MNOPQ9012R",
                "address": "Digital Tower, Floor 10",
                "country_id": country['id'] if country else "default-country",
                "state_id": state['id'] if state else "default-state",
                "city_id": city['id'] if city else "default-city",
                "zip_code": "400003"
            }
        ]
        
        for company_data in sample_companies:
            try:
                response = requests.post(
                    f"{self.base_url}/companies",
                    headers=self.headers,
                    json=company_data,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    company_id = data.get('id')
                    self.created_companies.append(data)
                    print(f"   ✅ Created company: {company_data['company_name']} (ID: {company_id})")
                else:
                    print(f"   ❌ Failed to create {company_data['company_name']}: {response.status_code}")
                    print(f"      Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Exception creating {company_data['company_name']}: {str(e)}")
        
        return len(self.created_companies) > 0
    
    def create_sample_leads(self):
        """Create sample leads for conversion to opportunities"""
        print("\n📋 Creating sample leads...")
        
        if not self.created_companies:
            print("❌ No companies available for lead creation")
            return False
        
        if not self.master_data.get('product_services') or not self.master_data.get('sub_tender_types'):
            print("❌ Missing required master data for leads")
            return False
        
        product_service = self.master_data['product_services'][0] if self.master_data['product_services'] else None
        sub_tender_type = self.master_data['sub_tender_types'][0] if self.master_data['sub_tender_types'] else None
        
        sample_leads = [
            {
                "tender_type": "Tender",
                "billing_type": "Fixed Price",
                "sub_tender_type_id": sub_tender_type['id'] if sub_tender_type else "default-sub-tender",
                "project_title": "Enterprise CRM Implementation Project",
                "company_id": self.created_companies[0]['id'],
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website",
                "product_service_id": product_service['id'] if product_service else "default-product",
                "expected_orc": 750000,
                "revenue": 750000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Pre-Tender",
                "billing_type": "Time & Material",
                "sub_tender_type_id": sub_tender_type['id'] if sub_tender_type else "default-sub-tender",
                "project_title": "Digital Transformation Initiative",
                "company_id": self.created_companies[1]['id'] if len(self.created_companies) > 1 else self.created_companies[0]['id'],
                "state": "Karnataka",
                "lead_subtype": "Expansion",
                "source": "Referral",
                "product_service_id": product_service['id'] if product_service else "default-product",
                "expected_orc": 1200000,
                "revenue": 1200000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Tender",
                "billing_type": "Fixed Price",
                "sub_tender_type_id": sub_tender_type['id'] if sub_tender_type else "default-sub-tender",
                "project_title": "Cloud Migration and Modernization",
                "company_id": self.created_companies[2]['id'] if len(self.created_companies) > 2 else self.created_companies[0]['id'],
                "state": "Tamil Nadu",
                "lead_subtype": "New Business",
                "source": "Cold Call",
                "product_service_id": product_service['id'] if product_service else "default-product",
                "expected_orc": 950000,
                "revenue": 950000,
                "lead_owner": "admin"
            }
        ]
        
        for lead_data in sample_leads:
            try:
                response = requests.post(
                    f"{self.base_url}/leads",
                    headers=self.headers,
                    json=lead_data,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    lead_id = data.get('lead_id', data.get('id'))
                    self.created_leads.append(data)
                    print(f"   ✅ Created lead: {lead_data['project_title']} (ID: {lead_id})")
                else:
                    print(f"   ❌ Failed to create lead {lead_data['project_title']}: {response.status_code}")
                    print(f"      Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Exception creating lead {lead_data['project_title']}: {str(e)}")
        
        return len(self.created_leads) > 0
    
    def approve_and_convert_leads(self):
        """Approve leads and convert them to opportunities"""
        print("\n🔄 Approving and converting leads to opportunities...")
        
        for i, lead in enumerate(self.created_leads):
            lead_id = lead.get('id')
            project_title = lead.get('project_title', 'Unknown')
            
            try:
                # Step 1: Approve the lead
                approve_response = requests.post(
                    f"{self.base_url}/leads/{lead_id}/status",
                    headers=self.headers,
                    json={"status": "approved"},
                    timeout=10
                )
                
                if approve_response.status_code in [200, 204]:
                    print(f"   ✅ Approved lead: {project_title}")
                    
                    # Step 2: Convert to opportunity
                    opportunity_date = datetime.now().strftime("%Y-%m-%d")
                    
                    convert_response = requests.post(
                        f"{self.base_url}/leads/{lead_id}/convert",
                        headers=self.headers,
                        params={"opportunity_date": opportunity_date},
                        timeout=10
                    )
                    
                    if convert_response.status_code in [200, 201]:
                        data = convert_response.json()
                        opportunity_id = data.get('opportunity_id')
                        self.created_opportunities.append(data)
                        print(f"   ✅ Converted to opportunity: {opportunity_id}")
                    else:
                        print(f"   ❌ Failed to convert lead {lead_id}: {convert_response.status_code}")
                        print(f"      Response: {convert_response.text[:200]}")
                else:
                    print(f"   ❌ Failed to approve lead {lead_id}: {approve_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Exception processing lead {lead_id}: {str(e)}")
            
            # Small delay between conversions
            time.sleep(1)
        
        return len(self.created_opportunities) > 0
    
    def verify_opportunities(self):
        """Verify that opportunities were created and are accessible"""
        print("\n🔍 Verifying created opportunities...")
        
        try:
            # Get all opportunities
            response = requests.get(
                f"{self.base_url}/opportunities",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', []) if isinstance(data, dict) else data
                
                print(f"   📊 Total opportunities in database: {len(opportunities)}")
                
                for opp in opportunities:
                    opp_id = opp.get('opportunity_id', opp.get('id'))
                    title = opp.get('project_title', opp.get('name', 'Unknown'))
                    stage = opp.get('current_stage', opp.get('stage', 'Unknown'))
                    
                    # Test individual access
                    individual_response = requests.get(
                        f"{self.base_url}/opportunities/{opp_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if individual_response.status_code == 200:
                        print(f"   ✅ {opp_id}: {title} (Stage: {stage}) - ACCESSIBLE")
                    else:
                        print(f"   ❌ {opp_id}: {title} (Stage: {stage}) - NOT ACCESSIBLE ({individual_response.status_code})")
                
                return True
            else:
                print(f"   ❌ Failed to get opportunities list: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception verifying opportunities: {str(e)}")
            return False
    
    def test_specific_opportunity_ids(self):
        """Test the specific opportunity IDs mentioned in the review request"""
        print("\n🎯 Testing specific opportunity IDs from review request...")
        
        for opp_id in TARGET_OPPORTUNITY_IDS:
            try:
                response = requests.get(
                    f"{self.base_url}/opportunities/{opp_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    title = data.get('project_title', data.get('name', 'Unknown'))
                    print(f"   ✅ {opp_id}: FOUND - {title}")
                elif response.status_code == 404:
                    print(f"   ❌ {opp_id}: NOT FOUND (404)")
                else:
                    print(f"   ❌ {opp_id}: ERROR ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {opp_id}: EXCEPTION - {str(e)}")
    
    def run_seeding(self):
        """Run the complete data seeding process"""
        print("🌱 STARTING DATA SEEDING FOR OPPORTUNITY TESTING")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed, cannot proceed")
            return False
        
        # Step 2: Get master data
        if not self.get_master_data():
            print("❌ Failed to get master data, cannot proceed")
            return False
        
        # Step 3: Create sample companies
        if not self.create_sample_companies():
            print("❌ Failed to create companies, cannot proceed")
            return False
        
        # Step 4: Create sample leads
        if not self.create_sample_leads():
            print("❌ Failed to create leads, cannot proceed")
            return False
        
        # Step 5: Approve and convert leads to opportunities
        if not self.approve_and_convert_leads():
            print("❌ Failed to convert leads to opportunities")
            return False
        
        # Step 6: Verify opportunities
        self.verify_opportunities()
        
        # Step 7: Test specific opportunity IDs
        self.test_specific_opportunity_ids()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print seeding summary"""
        print("\n" + "=" * 60)
        print("📊 DATA SEEDING SUMMARY")
        print("=" * 60)
        
        print(f"Companies Created: {len(self.created_companies)}")
        print(f"Leads Created: {len(self.created_leads)}")
        print(f"Opportunities Created: {len(self.created_opportunities)}")
        
        if len(self.created_opportunities) > 0:
            print("\n✅ SEEDING SUCCESSFUL!")
            print("🎯 Opportunities are now available for frontend testing")
        else:
            print("\n❌ SEEDING INCOMPLETE")
            print("⚠️  No opportunities were created")
        
        print("\n💡 NEXT STEPS:")
        print("1. Test opportunity list API: GET /api/opportunities")
        print("2. Test individual opportunity access: GET /api/opportunities/{id}")
        print("3. Verify frontend can now access opportunity data")

def main():
    """Main function"""
    seeder = DataSeeder()
    success = seeder.run_seeding()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()