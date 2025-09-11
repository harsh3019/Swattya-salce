#!/usr/bin/env python3
"""
Quick Lead and Contact Seeder Using Existing Companies
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

class QuickSeeder:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.companies = []
        self.created_contacts = []
        self.created_leads = []
        
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
    
    def get_existing_data(self):
        """Get existing companies and master data"""
        print("\n📊 Getting existing companies and master data...")
        
        try:
            # Get companies
            companies_response = requests.get(f"{self.base_url}/companies", headers=self.headers, timeout=10)
            if companies_response.status_code == 200:
                self.companies = companies_response.json()
                print(f"   ✅ Found {len(self.companies)} existing companies")
            
            # Get master data
            endpoints = {
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
                    self.master_data[key] = []
            
            return True
            
        except Exception as e:
            print(f"❌ Error getting existing data: {str(e)}")
            return False
    
    def create_contacts(self):
        """Create contacts for existing companies"""
        print("\n👥 Creating contacts...")
        
        if not self.companies:
            print("❌ No companies available")
            return False
        
        # Get designations
        designations_response = requests.get(f"{self.base_url}/designations", headers=self.headers, timeout=10)
        designations = designations_response.json() if designations_response.status_code == 200 else []
        designation_id = designations[0]['id'] if designations else "default-designation"
        
        contact_templates = [
            {
                "salutation": "Mr.",
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "email": "rajesh.kumar@techcorp.com",
                "primary_phone": "+91-9876543210",
                "designation_id": designation_id,
                "is_spoc": True,
                "is_technical": True,
                "is_commercial": False
            },
            {
                "salutation": "Ms.",
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": "priya.sharma@innovatetech.com",
                "primary_phone": "+91-9876543211",
                "designation_id": designation_id,
                "is_spoc": False,
                "is_technical": False,
                "is_commercial": True
            },
            {
                "salutation": "Dr.",
                "first_name": "Amit", 
                "last_name": "Patel",
                "email": "amit.patel@digitalsolutions.com",
                "primary_phone": "+91-9876543212",
                "designation_id": designation_id,
                "is_spoc": True,
                "is_technical": True,
                "is_commercial": True
            },
            {
                "salutation": "Mrs.",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@globalsystems.com",
                "primary_phone": "+1-555-0123",
                "designation_id": designation_id,
                "is_spoc": True,
                "is_technical": False,
                "is_commercial": True
            }
        ]
        
        for i, contact_template in enumerate(contact_templates):
            if i < len(self.companies):
                contact_data = {
                    **contact_template,
                    "company_id": self.companies[i]['id']
                }
                
                try:
                    response = requests.post(
                        f"{self.base_url}/contacts",
                        headers=self.headers,
                        json=contact_data,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        self.created_contacts.append(data)
                        print(f"   ✅ Created contact: {contact_data['first_name']} {contact_data['last_name']}")
                    else:
                        print(f"   ❌ Failed to create contact {contact_data['first_name']}: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Exception creating contact: {str(e)}")
        
        print(f"\n   📊 Total contacts created: {len(self.created_contacts)}")
        return len(self.created_contacts) > 0
    
    def create_leads(self):
        """Create leads using existing companies"""
        print("\n📋 Creating leads...")
        
        if not self.companies:
            print("❌ No companies available")
            return False
        
        product_service_id = self.master_data['product_services'][0]['id'] if self.master_data.get('product_services') else "default-product"
        sub_tender_type_id = self.master_data['sub_tender_types'][0]['id'] if self.master_data.get('sub_tender_types') else "default-sub-tender"
        
        lead_templates = [
            {
                "tender_type": "Tender",
                "billing_type": "postpaid",
                "project_title": "Enterprise CRM System Implementation Project",
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website Inquiry",
                "expected_orc": 1500000,
                "revenue": 1500000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Pre-Tender",
                "billing_type": "prepaid",
                "project_title": "Digital Transformation & ERP Deployment",
                "state": "Karnataka",
                "lead_subtype": "Expansion",
                "source": "Partner Referral",
                "expected_orc": 2500000,
                "revenue": 2500000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Tender",
                "billing_type": "postpaid",
                "project_title": "Mobile Application Development Suite",
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Cold Outreach",
                "expected_orc": 800000,
                "revenue": 800000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Pre-Tender",
                "billing_type": "prepaid",
                "project_title": "Cloud Migration and Infrastructure Setup",
                "state": "Karnataka",
                "lead_subtype": "Upgrade",
                "source": "Trade Show",
                "expected_orc": 3000000,
                "revenue": 3000000,
                "lead_owner": "admin"
            }
        ]
        
        for i, lead_template in enumerate(lead_templates):
            if i < len(self.companies):
                lead_data = {
                    **lead_template,
                    "company_id": self.companies[i]['id'],
                    "sub_tender_type_id": sub_tender_type_id,
                    "product_service_id": product_service_id
                }
                
                try:
                    response = requests.post(
                        f"{self.base_url}/leads",
                        headers=self.headers,
                        json=lead_data,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        self.created_leads.append(data)
                        print(f"   ✅ Created lead: {lead_data['project_title']}")
                        
                        # Auto-approve the lead
                        lead_id = data.get('id')
                        if lead_id:
                            approve_response = requests.post(
                                f"{self.base_url}/leads/{lead_id}/status",
                                headers=self.headers,
                                json={"status": "approved"},
                                timeout=10
                            )
                            if approve_response.status_code in [200, 201]:
                                print(f"      ✅ Auto-approved lead: {lead_id}")
                            
                    else:
                        print(f"   ❌ Failed to create lead {lead_data['project_title']}: {response.status_code}")
                        print(f"      Response: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"   ❌ Exception creating lead: {str(e)}")
        
        print(f"\n   📊 Total leads created: {len(self.created_leads)}")
        return len(self.created_leads) > 0
    
    def convert_leads(self):
        """Convert leads to opportunities"""
        print("\n🎯 Converting leads to opportunities...")
        
        opportunities_created = 0
        for lead in self.created_leads:
            try:
                lead_id = lead.get('id')
                if not lead_id:
                    continue
                
                conversion_date = datetime.now().isoformat()
                response = requests.post(
                    f"{self.base_url}/leads/{lead_id}/convert",
                    headers=self.headers,
                    params={"opportunity_date": conversion_date},
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    opportunity_id = data.get('opportunity_id')
                    opportunities_created += 1
                    print(f"   ✅ Converted to opportunity: {opportunity_id}")
                else:
                    print(f"   ❌ Failed to convert lead {lead_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Exception converting lead: {str(e)}")
        
        print(f"\n   📊 Total opportunities created: {opportunities_created}")
        return opportunities_created > 0
    
    def run_backend_pricing_seeder(self):
        """Run the backend pricing seeder now that we have data"""
        print("\n💰 Running backend pricing seeder...")
        try:
            import subprocess
            result = subprocess.run(["python", "backend_pricing_seeder.py"], 
                                  capture_output=True, text=True, timeout=30)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        except Exception as e:
            print(f"   ❌ Error running pricing seeder: {str(e)}")
    
    def display_summary(self):
        """Display summary"""
        print("\n" + "="*60)
        print("🎉 QUICK DATA SEEDING COMPLETED!")
        print("="*60)
        
        print(f"✅ Companies Found: {len(self.companies)}")
        print(f"✅ Contacts Created: {len(self.created_contacts)}")
        print(f"✅ Leads Created: {len(self.created_leads)}")
        
        print(f"\n🎯 System now ready for:")
        print("   • Quotation creation and testing")
        print("   • Opportunity editing functionality") 
        print("   • Lead-to-opportunity conversion")
        print("   • Stage management (L1-L8)")
        print("="*60)

def main():
    print("🚀 QUICK DATA SEEDING FOR SAWAYATTA ERP")
    print("="*50)
    
    seeder = QuickSeeder()
    
    if not seeder.authenticate():
        sys.exit(1)
    
    if not seeder.get_existing_data():
        sys.exit(1)
    
    seeder.create_contacts()
    
    if seeder.create_leads():
        seeder.convert_leads()
    
    seeder.run_backend_pricing_seeder()
    
    seeder.display_summary()
    print("\n🎉 System ready for testing!")

if __name__ == "__main__":
    main()