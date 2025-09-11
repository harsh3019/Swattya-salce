#!/usr/bin/env python3
"""
Direct Database Pricing Data Seeder
Creates sales prices and purchase costs directly in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timedelta
import os

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "sawayatta_erp"

async def create_comprehensive_pricing_data():
    """Create comprehensive pricing data including primary categories, products, sales prices, and purchase costs"""
    print("💰 CREATING COMPREHENSIVE PRICING DATA")
    print("="*50)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Get existing data
        existing_rate_cards = await db.rate_cards.find({"is_active": True}).to_list(length=None)
        existing_products = await db.products.find({"is_active": True}).to_list(length=None)
        existing_primary_categories = await db.primary_categories.find({"is_active": True}).to_list(length=None)
        existing_currencies = await db.currencies.find().to_list(length=None)
        
        if not existing_rate_cards:
            print("❌ No rate cards found")
            return False
        
        rate_card = existing_rate_cards[0]
        inr_currency = next((c for c in existing_currencies if c.get('code') == 'INR'), None)
        
        if not inr_currency:
            print("❌ INR currency not found")
            return False
        
        # Update products with primary category associations
        if existing_primary_categories and existing_products:
            sw_category = existing_primary_categories[0]  # Software Development
            hw_category = existing_primary_categories[1] if len(existing_primary_categories) > 1 else existing_primary_categories[0]  # Hardware
            cs_category = existing_primary_categories[2] if len(existing_primary_categories) > 2 else existing_primary_categories[0]  # Consulting
            
            product_category_mapping = {
                'CRM': sw_category['id'],
                'ERP': sw_category['id'], 
                'Mobile': sw_category['id'],
                'Web': sw_category['id'],
                'Cloud': cs_category['id']
            }
            
            for product in existing_products:
                category_id = sw_category['id']  # Default to software
                for key, cat_id in product_category_mapping.items():
                    if key.lower() in product.get('name', '').lower():
                        category_id = cat_id
                        break
                
                await db.products.update_one(
                    {"id": product['id']},
                    {"$set": {
                        "primary_category_id": category_id,
                        "unit": "License",
                        "updated_at": datetime.utcnow()
                    }}
                )
            print(f"✅ Updated {len(existing_products)} products with categories")
        
        # Create comprehensive sales prices
        sales_prices_data = [
            # CRM System
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in existing_products if 'CRM' in p.get('name', '')), existing_products[0]['id']),
                "currency_id": inr_currency['id'],
                "recurring_sale_price": 25000.00,
                "one_time_sale_price": 150000.00,
                "effective_from": datetime.utcnow(),
                "effective_to": None,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # ERP Solution
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in existing_products if 'ERP' in p.get('name', '')), existing_products[1]['id'] if len(existing_products) > 1 else existing_products[0]['id']),
                "currency_id": inr_currency['id'],
                "recurring_sale_price": 45000.00,
                "one_time_sale_price": 500000.00,
                "effective_from": datetime.utcnow(),
                "effective_to": None,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # Mobile Application
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in existing_products if 'Mobile' in p.get('name', '')), existing_products[2]['id'] if len(existing_products) > 2 else existing_products[0]['id']),
                "currency_id": inr_currency['id'],
                "recurring_sale_price": 8000.00,
                "one_time_sale_price": 80000.00,
                "effective_from": datetime.utcnow(),
                "effective_to": None,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # Web Portal
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in existing_products if 'Web' in p.get('name', '')), existing_products[3]['id'] if len(existing_products) > 3 else existing_products[0]['id']),
                "currency_id": inr_currency['id'],
                "recurring_sale_price": 15000.00,
                "one_time_sale_price": 120000.00,
                "effective_from": datetime.utcnow(),
                "effective_to": None,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # Cloud Migration
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in existing_products if 'Cloud' in p.get('name', '')), existing_products[4]['id'] if len(existing_products) > 4 else existing_products[0]['id']),
                "currency_id": inr_currency['id'],
                "recurring_sale_price": 20000.00,
                "one_time_sale_price": 200000.00,
                "effective_from": datetime.utcnow(),
                "effective_to": None,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            }
        ]
        
        # Create comprehensive purchase costs
        purchase_costs_data = [
            # CRM System
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in existing_products if 'CRM' in p.get('name', '')), existing_products[0]['id']),
                "purchase_cost": 12000.00,
                "purchase_date": datetime.utcnow() - timedelta(days=30),
                "currency_id": inr_currency['id'],
                "cost_type": "License",
                "remark": "CRM system license cost from vendor",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # ERP Solution
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in existing_products if 'ERP' in p.get('name', '')), existing_products[1]['id'] if len(existing_products) > 1 else existing_products[0]['id']),
                "purchase_cost": 25000.00,
                "purchase_date": datetime.utcnow() - timedelta(days=60),
                "currency_id": inr_currency['id'],
                "cost_type": "License",
                "remark": "ERP solution enterprise license cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # Mobile Application
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in existing_products if 'Mobile' in p.get('name', '')), existing_products[2]['id'] if len(existing_products) > 2 else existing_products[0]['id']),
                "purchase_cost": 4000.00,
                "purchase_date": datetime.utcnow() - timedelta(days=15),
                "currency_id": inr_currency['id'],
                "cost_type": "Development",
                "remark": "Mobile app development platform cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # Web Portal  
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in existing_products if 'Web' in p.get('name', '')), existing_products[3]['id'] if len(existing_products) > 3 else existing_products[0]['id']),
                "purchase_cost": 8000.00,
                "purchase_date": datetime.utcnow() - timedelta(days=45),
                "currency_id": inr_currency['id'],
                "cost_type": "Development",
                "remark": "Web portal development framework cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            # Cloud Migration
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in existing_products if 'Cloud' in p.get('name', '')), existing_products[4]['id'] if len(existing_products) > 4 else existing_products[0]['id']),
                "purchase_cost": 10000.00,
                "purchase_date": datetime.utcnow() - timedelta(days=90),
                "currency_id": inr_currency['id'],
                "cost_type": "Service",
                "remark": "Cloud migration service provider cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            }
        ]
        
        # Delete existing sales prices and purchase costs to avoid duplicates
        await db.sales_prices.delete_many({})
        await db.purchase_costs.delete_many({})
        
        # Insert new data
        await db.sales_prices.insert_many(sales_prices_data)
        print(f"✅ Inserted {len(sales_prices_data)} sales prices")
        
        await db.purchase_costs.insert_many(purchase_costs_data)
        print(f"✅ Inserted {len(purchase_costs_data)} purchase costs")
        
        # Verify data
        sales_count = await db.sales_prices.count_documents({"is_active": True})
        costs_count = await db.purchase_costs.count_documents({"is_active": True})
        
        print(f"📊 Final verification:")
        print(f"   • Sales prices: {sales_count}")
        print(f"   • Purchase costs: {costs_count}")
        print(f"   • Rate cards: {len(existing_rate_cards)}")
        print(f"   • Products: {len(existing_products)}")
        print(f"   • Primary categories: {len(existing_primary_categories)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating pricing data: {str(e)}")
        return False
        
    finally:
        client.close()

async def main():
    print("🌱 COMPREHENSIVE PRICING DATA SEEDER")
    print("="*50)
    success = await create_comprehensive_pricing_data()
    if success:
        print("\n🎉 Pricing data creation completed successfully!")
        print("System now ready for:")
        print("• Quotation creation with proper pricing")
        print("• Profitability calculations") 
        print("• Rate card integrations")
        print("• Purchase cost tracking")
    else:
        print("\n❌ Pricing data creation failed!")

if __name__ == "__main__":
    asyncio.run(main())