#!/usr/bin/env python3
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def init_sales_prices():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/sawayatta_erp')
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()
    
    # Get rate card
    rate_card = await db.mst_rate_cards.find_one({"is_active": True})
    if not rate_card:
        print("No active rate card found")
        return
    
    # Get products
    products = await db.mst_products.find({"is_active": True}).to_list(None)
    print(f"Found {len(products)} products")
    
    # Sample sales prices data
    sales_prices_data = [
        {"recurring_sale_price": 5000, "one_time_sale_price": 10000, "purchase_cost": 3500},
        {"recurring_sale_price": 8000, "one_time_sale_price": 15000, "purchase_cost": 5600},
        {"recurring_sale_price": 12000, "one_time_sale_price": 25000, "purchase_cost": 8400},
        {"recurring_sale_price": 3000, "one_time_sale_price": 8000, "purchase_cost": 2100},
        {"recurring_sale_price": 7500, "one_time_sale_price": 18000, "purchase_cost": 5250}
    ]
    
    for i, product in enumerate(products):
        price_data = sales_prices_data[i % len(sales_prices_data)]
        
        # Check if sales price already exists
        existing = await db.mst_sales_prices.find_one({
            "rate_card_id": rate_card["id"],
            "product_id": product["id"]
        })
        
        if not existing:
            sales_price = {
                "id": str(uuid.uuid4()),
                "rate_card_id": rate_card["id"],
                "product_id": product["id"],
                "recurring_sale_price": price_data["recurring_sale_price"],
                "one_time_sale_price": price_data["one_time_sale_price"],
                "purchase_cost": price_data["purchase_cost"],
                "effective_from": datetime.now(timezone.utc),
                "effective_to": None,
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await db.mst_sales_prices.insert_one(sales_price)
            print(f"Added sales price for product: {product['name']}")
        else:
            print(f"Sales price already exists for product: {product['name']}")
    
    print("Sales prices initialization completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(init_sales_prices())