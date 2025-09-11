#!/usr/bin/env python3
"""
Backend Database Seeder for Sales Prices and Purchase Costs
This script directly inserts data into MongoDB collections
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/sawayatta_erp")

async def seed_sales_prices_and_purchase_costs():
    """Seed sales prices and purchase costs directly into database"""
    print("💰 Seeding Sales Prices and Purchase Costs...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.sawayatta_erp
    
    try:
        # Get existing data
        rate_cards = await db.rate_cards.find({"is_active": True}).to_list(length=None)
        products = await db.products.find({"is_active": True}).to_list(length=None)
        currencies = await db.currencies.find().to_list(length=None)
        
        if not rate_cards or not products or not currencies:
            print("❌ Missing required master data")
            return False
        
        rate_card = rate_cards[0]
        inr_currency = next((c for c in currencies if c.get('code') == 'INR'), currencies[0])
        
        # Sales prices data
        sales_prices_data = [
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in products if 'CRM' in p.get('name', '')), products[0]['id']),
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
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in products if 'ERP' in p.get('name', '')), products[1]['id'] if len(products) > 1 else products[0]['id']),
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
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in products if 'Mobile' in p.get('name', '')), products[2]['id'] if len(products) > 2 else products[0]['id']),
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
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in products if 'Web' in p.get('name', '')), products[3]['id'] if len(products) > 3 else products[0]['id']),
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
            {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card['id'],
                "product_id": next((p['id'] for p in products if 'Cloud' in p.get('name', '')), products[4]['id'] if len(products) > 4 else products[0]['id']),
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
        
        # Purchase costs data  
        purchase_costs_data = [
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in products if 'CRM' in p.get('name', '')), products[0]['id']),
                "purchase_cost": 12000.00,
                "purchase_date": datetime.utcnow(),
                "currency_id": inr_currency['id'],
                "cost_type": "License",
                "remark": "CRM system license cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in products if 'ERP' in p.get('name', '')), products[1]['id'] if len(products) > 1 else products[0]['id']),
                "purchase_cost": 25000.00,
                "purchase_date": datetime.utcnow(),
                "currency_id": inr_currency['id'],
                "cost_type": "License",
                "remark": "ERP solution license cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in products if 'Mobile' in p.get('name', '')), products[2]['id'] if len(products) > 2 else products[0]['id']),
                "purchase_cost": 4000.00,
                "purchase_date": datetime.utcnow(),
                "currency_id": inr_currency['id'],
                "cost_type": "Development",
                "remark": "Mobile app development cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in products if 'Web' in p.get('name', '')), products[3]['id'] if len(products) > 3 else products[0]['id']),
                "purchase_cost": 8000.00,
                "purchase_date": datetime.utcnow(),
                "currency_id": inr_currency['id'],
                "cost_type": "Development",
                "remark": "Web portal development cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "id": str(uuid.uuid4()),
                "product_id": next((p['id'] for p in products if 'Cloud' in p.get('name', '')), products[4]['id'] if len(products) > 4 else products[0]['id']),
                "purchase_cost": 10000.00,
                "purchase_date": datetime.utcnow(),
                "currency_id": inr_currency['id'],
                "cost_type": "Service",
                "remark": "Cloud migration service cost",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "system"
            }
        ]
        
        # Insert sales prices
        existing_sales_prices = await db.sales_prices.find().to_list(length=None)
        if not existing_sales_prices:
            await db.sales_prices.insert_many(sales_prices_data)
            print(f"✅ Inserted {len(sales_prices_data)} sales prices")
        else:
            print(f"✅ Sales prices already exist ({len(existing_sales_prices)} records)")
        
        # Insert purchase costs
        existing_purchase_costs = await db.purchase_costs.find().to_list(length=None)
        if not existing_purchase_costs:
            await db.purchase_costs.insert_many(purchase_costs_data)
            print(f"✅ Inserted {len(purchase_costs_data)} purchase costs")
        else:
            print(f"✅ Purchase costs already exist ({len(existing_purchase_costs)} records)")
        
        # Update products with proper primary category associations
        primary_categories = await db.primary_categories.find({"is_active": True}).to_list(length=None)
        if primary_categories:
            sw_category = next((c for c in primary_categories if 'Software' in c.get('category_name', '')), primary_categories[0])
            
            for product in products:
                await db.products.update_one(
                    {"id": product['id']},
                    {"$set": {
                        "primary_category_id": sw_category['id'],
                        "unit": "License",
                        "updated_at": datetime.utcnow()
                    }}
                )
            print(f"✅ Updated {len(products)} products with category associations")
        
        print("✅ Database seeding completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        return False
    finally:
        client.close()

async def main():
    print("🌱 BACKEND DATABASE SEEDER FOR PRICING DATA")
    print("="*50)
    success = await seed_sales_prices_and_purchase_costs()
    if success:
        print("🎉 Pricing data seeding completed!")
    else:
        print("❌ Pricing data seeding failed!")

if __name__ == "__main__":
    asyncio.run(main())