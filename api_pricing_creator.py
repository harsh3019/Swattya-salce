#!/usr/bin/env python3
"""
API-based Pricing Data Creator
Creates sales prices and purchase costs using backend APIs
"""

import asyncio
import requests
import json
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://1b435344-f8f5-4a8b-98d4-64db783ac8b5.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "sawayatta_erp"

class PricingDataCreator:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        
    def authenticate(self):
        """Authenticate and get token"""
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
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def create_sales_prices_directly(self):
        """Create sales prices directly in MongoDB since no API endpoint exists"""
        print("\n💰 Creating sales prices directly in database...")
        
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        try:
            # Get master data from API
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            products_response = requests.get(f"{self.base_url}/mst/products", headers=self.headers, timeout=10)
            currencies_response = requests.get(f"{self.base_url}/mst/currencies", headers=self.headers, timeout=10)
            
            if not all([rate_cards_response.status_code == 200, products_response.status_code == 200, currencies_response.status_code == 200]):
                print("❌ Failed to get master data from API")
                return False
            
            rate_cards = rate_cards_response.json()
            products = products_response.json()
            currencies = currencies_response.json()
            
            if not rate_cards or not products or not currencies:
                print("❌ No master data available")
                return False
            
            rate_card = rate_cards[0]
            inr_currency = next((c for c in currencies if c.get('code') == 'INR'), currencies[0])
            
            print(f"Using rate card: {rate_card['name']}")
            print(f"Found {len(products)} products")
            print(f"Using currency: {inr_currency.get('name', 'Unknown')}")
            
            # Create sales prices data
            sales_prices_data = []
            product_pricing = [
                ("CRM", 25000.00, 150000.00),
                ("ERP", 45000.00, 500000.00), 
                ("Mobile", 8000.00, 80000.00),
                ("Web", 15000.00, 120000.00),
                ("Cloud", 20000.00, 200000.00)
            ]
            
            for keyword, recurring_price, onetime_price in product_pricing:
                # Find matching product
                product = next((p for p in products if keyword.lower() in p.get('name', '').lower()), None)
                if product:
                    sales_price = {
                        "id": str(uuid.uuid4()),
                        "rate_card_id": rate_card['id'],
                        "product_id": product['id'],
                        "currency_id": inr_currency['id'],
                        "recurring_sale_price": recurring_price,
                        "one_time_sale_price": onetime_price,
                        "effective_from": datetime.utcnow(),
                        "effective_to": None,
                        "is_active": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "created_by": "system"
                    }
                    sales_prices_data.append(sales_price)
                    print(f"   ✅ Prepared sales price for {product['name']}: ₹{recurring_price}/month, ₹{onetime_price} one-time")
            
            # Create purchase costs data
            purchase_costs_data = []
            cost_data = [
                ("CRM", 12000.00, "License"),
                ("ERP", 25000.00, "License"),
                ("Mobile", 4000.00, "Development"),
                ("Web", 8000.00, "Development"),
                ("Cloud", 10000.00, "Service")
            ]
            
            for keyword, cost, cost_type in cost_data:
                product = next((p for p in products if keyword.lower() in p.get('name', '').lower()), None)
                if product:
                    purchase_cost = {
                        "id": str(uuid.uuid4()),
                        "product_id": product['id'],
                        "purchase_cost": cost,
                        "purchase_date": datetime.utcnow() - timedelta(days=30),
                        "currency_id": inr_currency['id'],
                        "cost_type": cost_type,
                        "remark": f"{product['name']} {cost_type.lower()} cost",
                        "is_active": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "created_by": "system"
                    }
                    purchase_costs_data.append(purchase_cost)
                    print(f"   ✅ Prepared purchase cost for {product['name']}: ₹{cost} ({cost_type})")
            
            # Clear existing data and insert new
            await db.mst_sales_prices.delete_many({})
            await db.mst_purchase_costs.delete_many({})
            
            if sales_prices_data:
                await db.mst_sales_prices.insert_many(sales_prices_data)
                print(f"\n✅ Inserted {len(sales_prices_data)} sales prices")
            
            if purchase_costs_data:
                await db.mst_purchase_costs.insert_many(purchase_costs_data)
                print(f"✅ Inserted {len(purchase_costs_data)} purchase costs")
            
            # Update products with primary category
            primary_categories_response = requests.get(f"{self.base_url}/mst/primary-categories", headers=self.headers, timeout=10)
            if primary_categories_response.status_code == 200:
                categories = primary_categories_response.json()
                if categories:
                    sw_category = categories[0]  # Use first category
                    
                    # Update all products to have primary category
                    for product in products:
                        await db.mst_products.update_one(
                            {"id": product['id']},
                            {"$set": {
                                "primary_category_id": sw_category['id'],
                                "category_id": sw_category['id'],  # Also set category_id for compatibility
                                "unit": "License",
                                "updated_at": datetime.utcnow()
                            }}
                        )
                    print(f"✅ Updated {len(products)} products with primary category")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating pricing data: {str(e)}")
            return False
        finally:
            client.close()
    
    def verify_pricing_data(self):
        """Verify pricing data through API"""
        print("\n🔍 Verifying pricing data...")
        
        try:
            # Get rate cards and check sales prices
            rate_cards_response = requests.get(f"{self.base_url}/mst/rate-cards", headers=self.headers, timeout=10)
            if rate_cards_response.status_code == 200:
                rate_cards = rate_cards_response.json()
                if rate_cards:
                    rate_card_id = rate_cards[0]['id']
                    
                    # Try to get sales prices
                    sales_prices_response = requests.get(
                        f"{self.base_url}/mst/sales-prices/{rate_card_id}", 
                        headers=self.headers, 
                        timeout=10
                    )
                    
                    if sales_prices_response.status_code == 200:
                        sales_prices = sales_prices_response.json()
                        print(f"✅ Found {len(sales_prices)} sales prices via API")
                        return len(sales_prices) > 0
                    else:
                        print(f"❌ Sales prices API returned: {sales_prices_response.status_code}")
                        return False
            return False
            
        except Exception as e:
            print(f"❌ Error verifying pricing data: {str(e)}")
            return False

async def main():
    print("🌱 API-BASED PRICING DATA CREATOR")
    print("="*50)
    
    creator = PricingDataCreator()
    
    if not creator.authenticate():
        return
    
    success = await creator.create_sales_prices_directly()
    
    if success:
        print("\n🔍 Verification...")
        if creator.verify_pricing_data():
            print("\n🎉 Pricing data creation completed successfully!")
            print("✅ Sales prices available via API")
            print("✅ Purchase costs created in database")
            print("✅ Products updated with primary categories")
            print("\nSystem ready for quotation creation with proper pricing!")
        else:
            print("\n⚠️ Data created but verification failed")
    else:
        print("\n❌ Pricing data creation failed!")

if __name__ == "__main__":
    asyncio.run(main())