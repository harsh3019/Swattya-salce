#!/usr/bin/env python3
"""
Create Minimal Master Data for Testing
"""

import asyncio
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import os

async def create_minimal_master_data():
    """Create minimal master data needed for quotation testing"""
    print("🌱 CREATING MINIMAL MASTER DATA FOR TESTING")
    print("=" * 50)
    
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.sawayatta_erp
    
    try:
        # Create primary category
        print("1. Creating primary category...")
        category_id = str(uuid.uuid4())
        category_data = {
            "id": category_id,
            "category_name": "Software Solutions",
            "category_code": "SW",
            "description": "Software development and implementation services",
            "created_by": "system",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        existing_category = db.mst_primary_categories.find_one({"category_code": "SW"})
        if not existing_category:
            db.mst_primary_categories.insert_one(category_data)
            print(f"   ✅ Created category: {category_data['category_name']}")
        else:
            category_id = existing_category["id"]
            print(f"   ✅ Using existing category: {existing_category['category_name']}")
        
        # Create products
        print("2. Creating products...")
        products_data = [
            {
                "id": str(uuid.uuid4()),
                "product_name": "CRM System",
                "product_code": "CRM-001",
                "squ_code": "SQ-CRM-001",
                "primary_category_id": category_id,
                "unit": "License",
                "description": "Customer Relationship Management System",
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "Training Services",
                "product_code": "TRN-001",
                "squ_code": "SQ-TRN-001",
                "primary_category_id": category_id,
                "unit": "Days",
                "description": "Professional training and support services",
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
        ]
        
        for product_data in products_data:
            existing = db.mst_products.find_one({"product_code": product_data["product_code"]})
            if not existing:
                db.mst_products.insert_one(product_data)
                print(f"   ✅ Created product: {product_data['product_name']}")
            else:
                print(f"   ✅ Using existing product: {existing['product_name']}")
        
        # Create rate card
        print("3. Creating rate card...")
        rate_card_id = str(uuid.uuid4())
        rate_card_data = {
            "id": rate_card_id,
            "rate_card_name": "Standard Rate Card 2024",
            "effective_from": datetime.now(timezone.utc),
            "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
            "created_by": "system",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        existing_rate_card = db.mst_rate_cards.find_one({"rate_card_name": rate_card_data["rate_card_name"]})
        if not existing_rate_card:
            db.mst_rate_cards.insert_one(rate_card_data)
            print(f"   ✅ Created rate card: {rate_card_data['rate_card_name']}")
        else:
            rate_card_id = existing_rate_card["id"]
            print(f"   ✅ Using existing rate card: {existing_rate_card['rate_card_name']}")
        
        # Create sales prices
        print("4. Creating sales prices...")
        products = list(db.mst_products.find({"is_active": True}))
        
        for product in products:
            sales_price_data = {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card_id,
                "product_id": product["id"],
                "sales_price": 500000 if "CRM" in product["product_name"] else 25000,
                "pricing_type": "one_time",
                "effective_date": datetime.now(timezone.utc),
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            
            existing = db.mst_sales_prices.find_one({
                "rate_card_id": rate_card_id,
                "product_id": product["id"]
            })
            
            if not existing:
                db.mst_sales_prices.insert_one(sales_price_data)
                print(f"   ✅ Created sales price for: {product['product_name']} - ₹{sales_price_data['sales_price']:,}")
            else:
                print(f"   ✅ Using existing sales price for: {product['product_name']}")
        
        # Verify data
        print("\n5. Verifying created data...")
        categories_count = db.mst_primary_categories.count_documents({"is_active": True})
        products_count = db.mst_products.count_documents({"is_active": True})
        rate_cards_count = db.mst_rate_cards.count_documents({"is_active": True})
        sales_prices_count = db.mst_sales_prices.count_documents({"is_active": True})
        
        print(f"   📊 Categories: {categories_count}")
        print(f"   📊 Products: {products_count}")
        print(f"   📊 Rate Cards: {rate_cards_count}")
        print(f"   📊 Sales Prices: {sales_prices_count}")
        
        if all([categories_count > 0, products_count > 0, rate_cards_count > 0, sales_prices_count > 0]):
            print(f"\n✅ MINIMAL MASTER DATA CREATION COMPLETED")
            print("   🎯 Ready for quotation and L5 testing!")
        else:
            print(f"\n❌ SOME DATA CREATION FAILED")
            
    except Exception as e:
        print(f"❌ Error creating master data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_minimal_master_data())