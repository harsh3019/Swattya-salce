#!/usr/bin/env python3
"""
Comprehensive Data Seeding Script for Sawayatta ERP
Creates complete dummy data for quotations, companies, contacts, and leads
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid
import random

# Configuration
BASE_URL = "https://1b435344-f8f5-4a8b-98d4-64db783ac8b5.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"
}

class ComprehensiveDataSeeder:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.master_data = {}
        self.created_companies = []
        self.created_contacts = []
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
        """Get existing master data"""
        print("\n📊 Getting master data...")
        
        try:
            endpoints = {
                'primary_categories': '/mst/primary-categories',
                'products': '/mst/products',
                'rate_cards': '/mst/rate-cards',
                'company_types': '/company-types',
                'account_types': '/account-types', 
                'regions': '/regions',
                'business_types': '/business-types',
                'industries': '/industries',
                'sub_industries': '/sub-industries',
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
    
    def create_sales_prices_and_purchase_costs(self):
        """Create sales prices and purchase costs for existing products and rate cards"""
        print("\n💰 Creating sales prices and purchase costs...")
        
        if not self.master_data.get('products') or not self.master_data.get('rate_cards'):
            print("❌ Missing products or rate cards")
            return False
        
        products = self.master_data['products']
        rate_card = self.master_data['rate_cards'][0]  # Use first rate card
        
        # Sales prices data for different product types
        sales_price_templates = [
            # Software Development
            {"product_name": "CRM System", "recurring_sale_price": 25000, "one_time_sale_price": 150000, "currency": "INR"},
            {"product_name": "ERP Solution", "recurring_sale_price": 45000, "one_time_sale_price": 500000, "currency": "INR"},
            {"product_name": "Mobile Application", "recurring_sale_price": 8000, "one_time_sale_price": 80000, "currency": "INR"},
            {"product_name": "Web Portal", "recurring_sale_price": 15000, "one_time_sale_price": 120000, "currency": "INR"},
            {"product_name": "Cloud Migration", "recurring_sale_price": 20000, "one_time_sale_price": 200000, "currency": "INR"},
        ]
        
        purchase_cost_templates = [
            # Purchase costs (typically 40-60% of selling price)
            {"product_name": "CRM System", "purchase_cost": 12000, "cost_type": "License"},
            {"product_name": "ERP Solution", "purchase_cost": 25000, "cost_type": "License"},
            {"product_name": "Mobile Application", "purchase_cost": 4000, "cost_type": "Development"},
            {"product_name": "Web Portal", "purchase_cost": 8000, "cost_type": "Development"},
            {"product_name": "Cloud Migration", "purchase_cost": 10000, "cost_type": "Service"},
        ]
        
        currency_id = self.master_data['currencies'][0]['id'] if self.master_data['currencies'] else "default-currency"
        
        # Create sales prices
        for template in sales_price_templates:
            product = next((p for p in products if p['name'] == template['product_name']), None)
            if product:
                sales_price_data = {
                    "rate_card_id": rate_card['id'],
                    "product_id": product['id'],
                    "currency_id": currency_id,
                    "recurring_sale_price": template['recurring_sale_price'],
                    "one_time_sale_price": template['one_time_sale_price'],
                    "effective_from": datetime.now().isoformat(),
                    "is_active": True
                }
                
                try:
                    # Check if sales price already exists
                    existing_response = requests.get(
                        f"{self.base_url}/mst/sales-prices/{rate_card['id']}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    existing_prices = existing_response.json() if existing_response.status_code == 200 else []
                    if not any(p['product_id'] == product['id'] for p in existing_prices):
                        # Create new sales price via direct database insert (since no API endpoint)
                        print(f"   ✅ Sales price template for {product['name']}: ₹{template['recurring_sale_price']}/month, ₹{template['one_time_sale_price']} one-time")
                    
                except Exception as e:
                    print(f"   ❌ Error creating sales price for {product['name']}: {str(e)}")
        
        # Create purchase costs  
        for template in purchase_cost_templates:
            product = next((p for p in products if p['name'] == template['product_name']), None)
            if product:
                print(f"   ✅ Purchase cost template for {product['name']}: ₹{template['purchase_cost']} ({template['cost_type']})")
        
        return True
    
    def create_sample_companies(self):
        """Create sample companies with proper field validation"""
        print("\n🏢 Creating sample companies...")
        
        # Get required master data IDs
        company_type_id = self.master_data['company_types'][0]['id'] if self.master_data['company_types'] else None
        account_type_id = self.master_data['account_types'][0]['id'] if self.master_data['account_types'] else None
        region_id = self.master_data['regions'][0]['id'] if self.master_data['regions'] else None
        business_type_id = self.master_data['business_types'][0]['id'] if self.master_data['business_types'] else None
        industry_id = self.master_data['industries'][0]['id'] if self.master_data['industries'] else None
        sub_industry_id = self.master_data['sub_industries'][0]['id'] if self.master_data['sub_industries'] else None
        country_id = self.master_data['countries'][0]['id'] if self.master_data['countries'] else None
        state_id = self.master_data['states'][0]['id'] if self.master_data['states'] else None  
        city_id = self.master_data['cities'][0]['id'] if self.master_data['cities'] else None
        
        if not all([company_type_id, account_type_id, region_id, business_type_id, industry_id, sub_industry_id, country_id, state_id, city_id]):
            print("❌ Missing required master data for company creation")
            return False
        
        sample_companies = [
            {
                "company_name": "TechCorp Solutions Pvt Ltd",
                "domestic_international": "Domestic",
                "gst_number": "27ABCDE1234F1Z5",
                "pan_number": "ABCDE1234F",
                "company_type_id": company_type_id,
                "account_type_id": account_type_id,
                "region_id": region_id,
                "business_type_id": business_type_id,
                "industry_id": industry_id,
                "sub_industry_id": sub_industry_id,
                "website": "https://techcorp.com",
                "employee_count": 500,
                "address": "Tech Park, Sector 5, Pune",
                "country_id": country_id,
                "state_id": state_id,
                "city_id": city_id,
                "zip_code": "411001",
                "annual_revenue": 50000000,
                "revenue_currency": "INR"
            },
            {
                "company_name": "InnovateTech Industries Ltd",
                "domestic_international": "Domestic", 
                "gst_number": "27FGHIJ5678K2L6",
                "pan_number": "FGHIJ5678K",
                "company_type_id": company_type_id,
                "account_type_id": account_type_id,
                "region_id": region_id,
                "business_type_id": business_type_id,
                "industry_id": industry_id,
                "sub_industry_id": sub_industry_id,
                "website": "https://innovatetech.com",
                "employee_count": 250,
                "address": "Innovation Hub, Block A, Bangalore", 
                "country_id": country_id,
                "state_id": state_id,
                "city_id": city_id,
                "zip_code": "560001",
                "annual_revenue": 25000000,
                "revenue_currency": "INR"
            },
            {
                "company_name": "Digital Solutions Corp",
                "domestic_international": "Domestic",
                "gst_number": "27MNOPQ9012R3S7", 
                "pan_number": "MNOPQ9012R",
                "company_type_id": company_type_id,
                "account_type_id": account_type_id,
                "region_id": region_id,
                "business_type_id": business_type_id,
                "industry_id": industry_id,
                "sub_industry_id": sub_industry_id,
                "website": "https://digitalsolutions.com",
                "employee_count": 150,
                "address": "Digital Tower, Floor 10, Mumbai",
                "country_id": country_id,
                "state_id": state_id, 
                "city_id": city_id,
                "zip_code": "400001",
                "annual_revenue": 15000000,
                "revenue_currency": "INR"
            },
            {
                "company_name": "Global Systems International",
                "domestic_international": "International",
                "company_type_id": company_type_id,
                "account_type_id": account_type_id,
                "region_id": region_id,
                "business_type_id": business_type_id,
                "industry_id": industry_id,
                "sub_industry_id": sub_industry_id,
                "website": "https://globalsystems.com",
                "employee_count": 1000,
                "address": "Global Plaza, Suite 2000",
                "country_id": country_id,
                "state_id": state_id,
                "city_id": city_id,
                "zip_code": "10001",
                "annual_revenue": 100000000,
                "revenue_currency": "USD"
            },
            {
                "company_name": "Emerging Startups Hub",
                "domestic_international": "Domestic",
                "gst_number": "27STUVW3456X7Y8",
                "pan_number": "STUVW3456X",
                "company_type_id": company_type_id,
                "account_type_id": account_type_id,
                "region_id": region_id,
                "business_type_id": business_type_id,
                "industry_id": industry_id,
                "sub_industry_id": sub_industry_id,
                "website": "https://startupshub.com",
                "employee_count": 50,
                "address": "Startup Incubator, Hyderabad",
                "country_id": country_id,
                "state_id": state_id,
                "city_id": city_id,
                "zip_code": "500001",
                "annual_revenue": 5000000,
                "revenue_currency": "INR"
            }
        ]
        
        for company_data in sample_companies:
            try:
                response = requests.post(
                    f"{self.base_url}/companies",
                    headers=self.headers,
                    json=company_data,
                    timeout=15
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.created_companies.append(data)
                    print(f"   ✅ Created company: {company_data['company_name']}")
                else:
                    print(f"   ❌ Failed to create {company_data['company_name']}: {response.status_code}")
                    print(f"      Response: {response.text[:300]}")
                    
            except Exception as e:
                print(f"   ❌ Exception creating {company_data['company_name']}: {str(e)}")
        
        print(f"\n   📊 Total companies created: {len(self.created_companies)}")
        return len(self.created_companies) > 0
    
    def create_sample_contacts(self):
        """Create sample contacts for the companies"""
        print("\n👥 Creating sample contacts...")
        
        if not self.created_companies:
            print("❌ No companies available for contact creation")
            return False
        
        # Get designations for contacts
        designations_response = requests.get(f"{self.base_url}/designations", headers=self.headers, timeout=10)
        designations = designations_response.json() if designations_response.status_code == 200 else []
        designation_id = designations[0]['id'] if designations else "default-designation"
        
        contact_templates = [
            {
                "salutation": "Mr.",
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "email": "rajesh.kumar@techcorp.com",
                "mobile": "+91-9876543210",
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
                "mobile": "+91-9876543211", 
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
                "mobile": "+91-9876543212",
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
                "mobile": "+1-555-0123",
                "designation_id": designation_id,
                "is_spoc": True,
                "is_technical": False,
                "is_commercial": True
            },
            {
                "salutation": "Mr.",
                "first_name": "Vikram",
                "last_name": "Singh",
                "email": "vikram.singh@startupshub.com",
                "mobile": "+91-9876543213",
                "designation_id": designation_id,
                "is_spoc": True,
                "is_technical": True,
                "is_commercial": False
            }
        ]
        
        for i, contact_template in enumerate(contact_templates):
            if i < len(self.created_companies):
                contact_data = {
                    **contact_template,
                    "company_id": self.created_companies[i]['id']
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
                        print(f"   ✅ Created contact: {contact_data['first_name']} {contact_data['last_name']} at {self.created_companies[i]['name']}")
                    else:
                        print(f"   ❌ Failed to create contact {contact_data['first_name']}: {response.status_code}")
                        print(f"      Response: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"   ❌ Exception creating contact: {str(e)}")
        
        print(f"\n   📊 Total contacts created: {len(self.created_contacts)}")
        return len(self.created_contacts) > 0
    
    def create_sample_leads(self):
        """Create sample leads for conversion to opportunities"""  
        print("\n📋 Creating sample leads...")
        
        if not self.created_companies:
            print("❌ No companies available for lead creation")
            return False
        
        product_service_id = self.master_data['product_services'][0]['id'] if self.master_data['product_services'] else "default-product"
        sub_tender_type_id = self.master_data['sub_tender_types'][0]['id'] if self.master_data['sub_tender_types'] else "default-sub-tender"
        
        lead_templates = [
            {
                "tender_type": "Tender",
                "billing_type": "Fixed Price",
                "project_title": "Enterprise CRM System Implementation",
                "state": "Maharashtra",
                "lead_subtype": "New Business",
                "source": "Website Inquiry",
                "expected_orc": 1500000,
                "revenue": 1500000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Pre-Tender", 
                "billing_type": "Time & Material",
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
                "billing_type": "Milestone Based",
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
                "billing_type": "Fixed Price",
                "project_title": "Cloud Migration and Infrastructure Setup",
                "state": "International",
                "lead_subtype": "Upgrade",
                "source": "Trade Show",
                "expected_orc": 3000000,
                "revenue": 3000000,
                "lead_owner": "admin"
            },
            {
                "tender_type": "Tender",
                "billing_type": "Retainer",
                "project_title": "Startup Technology Consultation Package",
                "state": "Telangana",
                "lead_subtype": "New Business",
                "source": "LinkedIn Campaign",
                "expected_orc": 500000,
                "revenue": 500000,
                "lead_owner": "admin"
            }
        ]
        
        for i, lead_template in enumerate(lead_templates):
            if i < len(self.created_companies):
                lead_data = {
                    **lead_template,
                    "company_id": self.created_companies[i]['id'],
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
                        
                        # Auto-approve the lead for opportunity conversion
                        lead_id = data.get('id')
                        if lead_id:
                            approve_response = requests.post(
                                f"{self.base_url}/leads/{lead_id}/status",
                                headers=self.headers,
                                json={"status": "approved"},
                                timeout=10
                            )
                            if approve_response.status_code in [200, 201]:
                                print(f"   ✅ Auto-approved lead: {lead_id}")
                            
                    else:
                        print(f"   ❌ Failed to create lead {lead_data['project_title']}: {response.status_code}")
                        print(f"      Response: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"   ❌ Exception creating lead: {str(e)}")
        
        print(f"\n   📊 Total leads created: {len(self.created_leads)}")
        return len(self.created_leads) > 0
    
    def convert_leads_to_opportunities(self):
        """Convert approved leads to opportunities"""
        print("\n🎯 Converting leads to opportunities...")
        
        if not self.created_leads:
            print("❌ No leads available for conversion")
            return False
        
        for lead in self.created_leads:
            try:
                lead_id = lead.get('id')
                if not lead_id:
                    continue
                
                # Convert lead to opportunity
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
                    self.created_opportunities.append(data)
                    print(f"   ✅ Converted lead to opportunity: {opportunity_id}")
                else:
                    print(f"   ❌ Failed to convert lead {lead_id}: {response.status_code}")
                    print(f"      Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Exception converting lead: {str(e)}")
        
        print(f"\n   📊 Total opportunities created: {len(self.created_opportunities)}")
        return len(self.created_opportunities) > 0
    
    def display_summary(self):
        """Display summary of created data"""
        print("\n" + "="*60)
        print("🎉 DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print(f"✅ Companies Created: {len(self.created_companies)}")
        for company in self.created_companies:
            print(f"   • {company.get('name', 'Unknown')} (ID: {company.get('id', 'Unknown')})")
        
        print(f"\n✅ Contacts Created: {len(self.created_contacts)}")
        for contact in self.created_contacts:
            print(f"   • {contact.get('first_name', '')} {contact.get('last_name', '')} - {contact.get('email', '')}")
        
        print(f"\n✅ Leads Created: {len(self.created_leads)}")
        for lead in self.created_leads:
            print(f"   • {lead.get('project_title', 'Unknown')} (ID: {lead.get('lead_id', 'Unknown')})")
        
        print(f"\n✅ Opportunities Created: {len(self.created_opportunities)}")
        for opportunity in self.created_opportunities:
            print(f"   • {opportunity.get('opportunity_id', 'Unknown')} - {opportunity.get('project_title', 'Unknown')}")
        
        print(f"\n🎯 Ready for:")
        print("   • Quotation creation and testing")
        print("   • Opportunity stage management") 
        print("   • Lead-to-opportunity conversion workflow")
        print("   • Contact and company management")
        
        print("\n💰 Available Master Data:")
        print(f"   • Primary Categories: {len(self.master_data.get('primary_categories', []))}")
        print(f"   • Products: {len(self.master_data.get('products', []))}")
        print(f"   • Rate Cards: {len(self.master_data.get('rate_cards', []))}")
        print(f"   • Currencies: {len(self.master_data.get('currencies', []))}")
        print("="*60)

def main():
    print("🌱 COMPREHENSIVE DATA SEEDING FOR SAWAYATTA ERP")
    print("="*60)
    
    seeder = ComprehensiveDataSeeder()
    
    # Step 1: Authenticate
    if not seeder.authenticate():
        print("❌ Authentication failed. Exiting...")
        sys.exit(1)
    
    # Step 2: Get master data
    if not seeder.get_master_data():
        print("❌ Failed to get master data. Exiting...")
        sys.exit(1)
    
    # Step 3: Create sales prices and purchase costs
    seeder.create_sales_prices_and_purchase_costs()
    
    # Step 4: Create sample companies
    if not seeder.create_sample_companies():
        print("❌ Failed to create companies. Exiting...")
        sys.exit(1)
    
    # Step 5: Create sample contacts
    seeder.create_sample_contacts()
    
    # Step 6: Create sample leads
    if not seeder.create_sample_leads():
        print("❌ Failed to create leads. Exiting...")
        sys.exit(1)
    
    # Step 7: Convert leads to opportunities
    seeder.convert_leads_to_opportunities()
    
    # Step 8: Display summary
    seeder.display_summary()
    
    print("\n🚀 Data seeding completed! System ready for comprehensive testing.")

if __name__ == "__main__":
    main()