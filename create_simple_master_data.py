#!/usr/bin/env python3
"""
Create Simple Master Data - Compatible with existing structure
"""

import asyncio
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import os

async def create_simple_master_data():
    """Create master data compatible with existing structure"""
    print("🌱 CREATING SIMPLE MASTER DATA (COMPATIBLE)")
    print("=" * 50)
    
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.sawayatta_erp
    
    try:
        # Step 1: Update existing products with SQU codes
        print("1. Adding SQU codes to existing products...")
        existing_products = list(db.mst_products.find({"is_active": True}))
        
        squ_mapping = {
            "CRM System": "SQU-CRM-001",
            "Training Services": "SQU-TRN-001"
        }
        
        for product in existing_products:
            product_name = product.get("name", "")
            if product_name in squ_mapping and not product.get("squ_code"):
                db.mst_products.update_one(
                    {"id": product["id"]},
                    {"$set": {
                        "squ_code": squ_mapping[product_name],
                        "product_code": f"PRD-{product_name.replace(' ', '-').upper()[:10]}",
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
                print(f"   ✅ Updated {product_name} with SQU code: {squ_mapping[product_name]}")
        
        # Step 2: Create additional products with SQU codes
        print("\n2. Creating additional products with SQU codes...")
        additional_products = [
            {
                "id": str(uuid.uuid4()),
                "name": "Web Development Service",
                "squ_code": "SQU-WEB-001",
                "product_code": "PRD-WEB-001",
                "description": "Custom web application development",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mobile App Development",
                "squ_code": "SQU-MOB-001", 
                "product_code": "PRD-MOB-001",
                "description": "Mobile application development for iOS and Android",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Cloud Migration Service",
                "squ_code": "SQU-CLD-001",
                "product_code": "PRD-CLD-001", 
                "description": "Complete cloud infrastructure migration",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Digital Marketing Package",
                "squ_code": "SQU-MKT-001",
                "product_code": "PRD-MKT-001",
                "description": "Complete digital marketing solution",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        for product_data in additional_products:
            existing = db.mst_products.find_one({"name": product_data["name"]})
            if not existing:
                db.mst_products.insert_one(product_data)
                print(f"   ✅ Created: {product_data['name']} ({product_data['squ_code']})")
            else:
                print(f"   ✅ Using existing: {existing['name']}")
        
        # Step 3: Create Rate Cards
        print("\n3. Creating Rate Cards...")
        rate_cards = [
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Standard Pricing 2024",
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Premium Pricing 2024", 
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        rate_card_ids = []
        for rate_card in rate_cards:
            existing = db.mst_rate_cards.find_one({"rate_card_name": rate_card["rate_card_name"]})
            if not existing:
                db.mst_rate_cards.insert_one(rate_card)
                rate_card_ids.append(rate_card["id"])
                print(f"   ✅ Created: {rate_card['rate_card_name']}")
            else:
                rate_card_ids.append(existing["id"])
                print(f"   ✅ Using existing: {existing['rate_card_name']}")
        
        # Step 4: Create Sales Prices
        print("\n4. Creating Sales Prices...")
        products = list(db.mst_products.find({"is_active": True}))
        
        # Simple pricing for demo
        base_prices = {
            "CRM System": 500000,
            "Training Services": 25000,
            "Web Development Service": 400000,
            "Mobile App Development": 800000,
            "Cloud Migration Service": 600000,
            "Digital Marketing Package": 150000
        }
        
        for i, rate_card_id in enumerate(rate_card_ids):
            multiplier = 1.0 if i == 0 else 1.5  # Standard vs Premium
            
            for product in products:
                product_name = product.get("name", "")
                base_price = base_prices.get(product_name, 100000)
                sales_price = int(base_price * multiplier)
                
                existing_price = db.mst_sales_prices.find_one({
                    "rate_card_id": rate_card_id,
                    "product_id": product["id"]
                })
                
                if not existing_price:
                    price_data = {
                        "id": str(uuid.uuid4()),
                        "rate_card_id": rate_card_id,
                        "product_id": product["id"],
                        "sales_price": sales_price,
                        "pricing_type": "one_time",
                        "effective_date": datetime.now(timezone.utc),
                        "is_active": True,
                        "created_by": "system",
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    db.mst_sales_prices.insert_one(price_data)
                    print(f"   ✅ {product_name}: ₹{sales_price:,}")
        
        # Step 5: Create Purchase Costs
        print("\n5. Creating Purchase Costs...")
        for product in products:
            existing_cost = db.mst_purchase_costs.find_one({"product_id": product["id"]})
            if not existing_cost:
                product_name = product.get("name", "")
                base_price = base_prices.get(product_name, 100000)
                purchase_cost = int(base_price * 0.65)  # 65% of base price
                
                cost_data = {
                    "id": str(uuid.uuid4()),
                    "product_id": product["id"],
                    "purchase_cost": purchase_cost,
                    "cost_type": "standard",
                    "vendor": "Default Vendor",
                    "effective_date": datetime.now(timezone.utc),
                    "is_active": True,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                db.mst_purchase_costs.insert_one(cost_data)
                
                margin = base_price - purchase_cost
                margin_percent = (margin / base_price) * 100
                print(f"   ✅ {product_name}: Cost ₹{purchase_cost:,} | Margin {margin_percent:.1f}%")
        
        # Step 6: Verification
        print("\n6. Verification...")
        counts = {
            "Products": db.mst_products.count_documents({"is_active": True}),
            "Products with SQU": db.mst_products.count_documents({"squ_code": {"$exists": True}}),
            "Rate Cards": db.mst_rate_cards.count_documents({"is_active": True}),
            "Sales Prices": db.mst_sales_prices.count_documents({"is_active": True}),
            "Purchase Costs": db.mst_purchase_costs.count_documents({"is_active": True})
        }
        
        for category, count in counts.items():
            print(f"   📊 {category}: {count}")
        
        print(f"\n✅ SIMPLE MASTER DATA CREATION COMPLETED!")
        print("   🎯 READY FOR QUOTATION TESTING AND PRICING!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_simple_master_data())