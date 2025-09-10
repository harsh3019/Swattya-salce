#!/usr/bin/env python3
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def init_complete_master_data():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/sawayatta_erp')
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()
    
    print("Initializing comprehensive master data...")
    
    # Enhanced Primary Categories
    categories_data = [
        {"name": "Software", "description": "Software applications and licenses"},
        {"name": "Hardware", "description": "Physical equipment and devices"},
        {"name": "Services", "description": "Professional and consulting services"},
        {"name": "Consulting", "description": "Advisory and strategy services"},
        {"name": "Cloud Services", "description": "Cloud computing and hosting services"},
        {"name": "Security", "description": "Cybersecurity products and services"},
        {"name": "Infrastructure", "description": "IT infrastructure components"},
        {"name": "Training", "description": "Training and certification services"}
    ]
    
    category_ids = {}
    for category_data in categories_data:
        existing = await db.mst_primary_categories.find_one({"name": category_data["name"]})
        if not existing:
            category_id = str(uuid.uuid4())
            category_record = {
                "id": category_id,
                **category_data,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            await db.mst_primary_categories.insert_one(category_record)
            print(f"Added category: {category_data['name']}")
        else:
            category_id = existing["id"]
            print(f"Category exists: {category_data['name']}")
        
        category_ids[category_data["name"]] = category_id
    
    # Enhanced Products with proper categorization
    products_data = [
        # Software Products
        {"name": "CRM Software Pro", "description": "Advanced customer relationship management", "unit": "License", "category": "Software"},
        {"name": "ERP Suite Enterprise", "description": "Complete enterprise resource planning", "unit": "License", "category": "Software"},
        {"name": "Project Management Tool", "description": "Comprehensive project management platform", "unit": "License", "category": "Software"},
        {"name": "Business Intelligence Dashboard", "description": "Advanced analytics and reporting", "unit": "License", "category": "Software"},
        {"name": "Document Management System", "description": "Centralized document storage and workflow", "unit": "License", "category": "Software"},
        
        # Hardware Products
        {"name": "Server Rack Unit", "description": "High-performance rack server", "unit": "Unit", "category": "Hardware"},
        {"name": "Network Switch 48-Port", "description": "Managed Gigabit Ethernet switch", "unit": "Unit", "category": "Hardware"},
        {"name": "Firewall Appliance", "description": "Enterprise-grade security appliance", "unit": "Unit", "category": "Hardware"},
        {"name": "Storage Array 10TB", "description": "Network attached storage system", "unit": "Unit", "category": "Hardware"},
        {"name": "Workstation Desktop", "description": "High-performance workstation", "unit": "Unit", "category": "Hardware"},
        
        # Services
        {"name": "Implementation Service", "description": "Software implementation and setup", "unit": "Hours", "category": "Services"},
        {"name": "Technical Support Annual", "description": "24/7 technical support service", "unit": "Year", "category": "Services"},
        {"name": "Data Migration Service", "description": "Complete data migration and validation", "unit": "Project", "category": "Services"},
        {"name": "System Integration", "description": "Custom system integration service", "unit": "Hours", "category": "Services"},
        
        # Cloud Services
        {"name": "Cloud Hosting Standard", "description": "Standard cloud hosting package", "unit": "Month", "category": "Cloud Services"},
        {"name": "Cloud Hosting Premium", "description": "Premium cloud hosting with SLA", "unit": "Month", "category": "Cloud Services"},
        {"name": "Cloud Storage 1TB", "description": "Secure cloud storage service", "unit": "Month", "category": "Cloud Services"},
        {"name": "Backup Service Cloud", "description": "Automated cloud backup service", "unit": "Month", "category": "Cloud Services"},
        
        # Security Products
        {"name": "Antivirus Enterprise", "description": "Enterprise antivirus solution", "unit": "License", "category": "Security"},
        {"name": "Security Audit Service", "description": "Comprehensive security assessment", "unit": "Project", "category": "Security"},
        {"name": "Penetration Testing", "description": "Professional penetration testing", "unit": "Project", "category": "Security"},
        
        # Training Services
        {"name": "User Training Program", "description": "Comprehensive user training", "unit": "Hours", "category": "Training"},
        {"name": "Admin Training Course", "description": "Administrator certification training", "unit": "Course", "category": "Training"}
    ]
    
    product_ids = []
    for product_data in products_data:
        category_name = product_data.pop("category")
        primary_category_id = category_ids.get(category_name)
        
        existing = await db.mst_products.find_one({"name": product_data["name"]})
        if not existing:
            product_id = str(uuid.uuid4())
            product_record = {
                "id": product_id,
                "primary_category_id": primary_category_id,
                **product_data,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            await db.mst_products.insert_one(product_record)
            print(f"Added product: {product_data['name']}")
            product_ids.append(product_id)
        else:
            print(f"Product exists: {product_data['name']}")
            product_ids.append(existing["id"])
    
    # Get rate card
    rate_card = await db.mst_rate_cards.find_one({"is_active": True})
    if not rate_card:
        print("No active rate card found")
        return
    
    # Comprehensive Sales Prices with realistic pricing
    sales_prices_data = [
        # Software Products (mix of recurring and one-time)
        {"recurring_sale_price": 15000, "one_time_sale_price": 0, "purchase_cost": 8000},  # CRM Software Pro
        {"recurring_sale_price": 0, "one_time_sale_price": 500000, "purchase_cost": 300000},  # ERP Suite Enterprise
        {"recurring_sale_price": 8000, "one_time_sale_price": 0, "purchase_cost": 4500},  # Project Management Tool
        {"recurring_sale_price": 25000, "one_time_sale_price": 0, "purchase_cost": 15000},  # Business Intelligence
        {"recurring_sale_price": 0, "one_time_sale_price": 120000, "purchase_cost": 75000},  # Document Management
        
        # Hardware Products (all one-time)
        {"recurring_sale_price": 0, "one_time_sale_price": 180000, "purchase_cost": 120000},  # Server Rack Unit
        {"recurring_sale_price": 0, "one_time_sale_price": 45000, "purchase_cost": 28000},  # Network Switch
        {"recurring_sale_price": 0, "one_time_sale_price": 85000, "purchase_cost": 55000},  # Firewall Appliance
        {"recurring_sale_price": 0, "one_time_sale_price": 95000, "purchase_cost": 65000},  # Storage Array
        {"recurring_sale_price": 0, "one_time_sale_price": 75000, "purchase_cost": 50000},  # Workstation Desktop
        
        # Services (mix based on service type)
        {"recurring_sale_price": 0, "one_time_sale_price": 2500, "purchase_cost": 1800},  # Implementation Service (per hour)
        {"recurring_sale_price": 60000, "one_time_sale_price": 0, "purchase_cost": 35000},  # Technical Support Annual
        {"recurring_sale_price": 0, "one_time_sale_price": 150000, "purchase_cost": 90000},  # Data Migration Service
        {"recurring_sale_price": 0, "one_time_sale_price": 3000, "purchase_cost": 2000},  # System Integration (per hour)
        
        # Cloud Services (all recurring)
        {"recurring_sale_price": 12000, "one_time_sale_price": 0, "purchase_cost": 7000},  # Cloud Hosting Standard
        {"recurring_sale_price": 25000, "one_time_sale_price": 0, "purchase_cost": 15000},  # Cloud Hosting Premium
        {"recurring_sale_price": 1500, "one_time_sale_price": 0, "purchase_cost": 800},  # Cloud Storage 1TB
        {"recurring_sale_price": 5000, "one_time_sale_price": 0, "purchase_cost": 3000},  # Backup Service Cloud
        
        # Security Products
        {"recurring_sale_price": 3500, "one_time_sale_price": 0, "purchase_cost": 2000},  # Antivirus Enterprise
        {"recurring_sale_price": 0, "one_time_sale_price": 200000, "purchase_cost": 120000},  # Security Audit Service
        {"recurring_sale_price": 0, "one_time_sale_price": 350000, "purchase_cost": 220000},  # Penetration Testing
        
        # Training Services
        {"recurring_sale_price": 0, "one_time_sale_price": 1500, "purchase_cost": 1000},  # User Training Program (per hour)
        {"recurring_sale_price": 0, "one_time_sale_price": 45000, "purchase_cost": 28000}   # Admin Training Course
    ]
    
    # Add sales prices for all products
    for i, product_id in enumerate(product_ids):
        if i < len(sales_prices_data):
            price_data = sales_prices_data[i]
            
            # Check if sales price already exists
            existing = await db.mst_sales_prices.find_one({
                "rate_card_id": rate_card["id"],
                "product_id": product_id
            })
            
            if not existing:
                sales_price = {
                    "id": str(uuid.uuid4()),
                    "rate_card_id": rate_card["id"],
                    "product_id": product_id,
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
                print(f"Added sales price for product {i+1}")
            else:
                print(f"Sales price exists for product {i+1}")
    
    print(f"\n✅ Master data initialization completed!")
    print(f"📊 Summary:")
    print(f"  - Categories: {len(categories_data)}")
    print(f"  - Products: {len(products_data)}")
    print(f"  - Sales Prices: {len(sales_prices_data)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(init_complete_master_data())