#!/usr/bin/env python3
"""
Create Comprehensive Dummy Data for Sawayatta ERP
Primary Categories, Products, Rate Cards, Sales Prices, Purchase Costs
"""

import asyncio
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import os

async def create_comprehensive_dummy_data():
    """Create comprehensive dummy data for all master tables"""
    print("🌱 CREATING COMPREHENSIVE DUMMY DATA")
    print("=" * 50)
    
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.sawayatta_erp
    
    try:
        # Step 1: Create Primary Categories
        print("1. Creating Primary Categories...")
        
        primary_categories = [
            {
                "id": str(uuid.uuid4()),
                "category_name": "Software Development",
                "category_code": "SD",
                "description": "Custom software development and application services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "IT Infrastructure",
                "category_code": "IT",
                "description": "Network setup, server management, and infrastructure services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "Digital Marketing",
                "category_code": "DM",
                "description": "SEO, social media, and digital advertising services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "Business Consulting",
                "category_code": "BC",
                "description": "Strategic planning and business advisory services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "Training Services",
                "category_code": "TS",
                "description": "Professional training and skill development programs",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        category_map = {}
        for category in primary_categories:
            existing = db.mst_primary_categories.find_one({"category_code": category["category_code"]})
            if not existing:
                db.mst_primary_categories.insert_one(category)
                category_map[category["category_code"]] = category["id"]
                print(f"   ✅ Created: {category['category_name']} ({category['category_code']})")
            else:
                category_map[category["category_code"]] = existing["id"]
                print(f"   ✅ Using existing: {existing['category_name']} ({existing['category_code']})")
        
        # Step 2: Create Products with SQU codes
        print("\n2. Creating Products with SQU codes...")
        
        products_data = [
            # Software Development
            {
                "name": "Custom Web Application",
                "squ_code": "SQU-SD-WEB-001",
                "product_code": "SD-WEB-001",
                "category_code": "SD",
                "description": "Full-stack web application development with modern frameworks",
                "unit": "Project"
            },
            {
                "name": "Mobile App Development",
                "squ_code": "SQU-SD-MOB-001", 
                "product_code": "SD-MOB-001",
                "category_code": "SD",
                "description": "Native iOS and Android mobile application development",
                "unit": "Project"
            },
            {
                "name": "E-commerce Platform",
                "squ_code": "SQU-SD-ECM-001",
                "product_code": "SD-ECM-001", 
                "category_code": "SD",
                "description": "Complete e-commerce solution with payment integration",
                "unit": "Project"
            },
            {
                "name": "CRM System",
                "squ_code": "SQU-SD-CRM-001",
                "product_code": "SD-CRM-001",
                "category_code": "SD", 
                "description": "Customer relationship management system",
                "unit": "License"
            },
            {
                "name": "ERP Solution",
                "squ_code": "SQU-SD-ERP-001",
                "product_code": "SD-ERP-001",
                "category_code": "SD",
                "description": "Enterprise resource planning solution",
                "unit": "License"
            },
            
            # IT Infrastructure
            {
                "name": "Network Setup",
                "squ_code": "SQU-IT-NET-001",
                "product_code": "IT-NET-001",
                "category_code": "IT",
                "description": "Complete network infrastructure setup and configuration",
                "unit": "Project"
            },
            {
                "name": "Cloud Migration",
                "squ_code": "SQU-IT-CLD-001",
                "product_code": "IT-CLD-001",
                "category_code": "IT",
                "description": "Migration to AWS/Azure/Google Cloud platforms",
                "unit": "Project"
            },
            {
                "name": "Server Management",
                "squ_code": "SQU-IT-SRV-001",
                "product_code": "IT-SRV-001",
                "category_code": "IT",
                "description": "24/7 server monitoring and management services",
                "unit": "Month"
            },
            
            # Digital Marketing
            {
                "name": "SEO Package",
                "squ_code": "SQU-DM-SEO-001",
                "product_code": "DM-SEO-001",
                "category_code": "DM",
                "description": "Complete SEO optimization and ranking improvement",
                "unit": "Month"
            },
            {
                "name": "Social Media Management",
                "squ_code": "SQU-DM-SMM-001",
                "product_code": "DM-SMM-001",
                "category_code": "DM",
                "description": "Social media content creation and management",
                "unit": "Month"
            },
            {
                "name": "Google Ads Campaign",
                "squ_code": "SQU-DM-ADS-001",
                "product_code": "DM-ADS-001",
                "category_code": "DM",
                "description": "Google Ads setup and management",
                "unit": "Month"
            },
            
            # Business Consulting
            {
                "name": "Business Strategy Consulting",
                "squ_code": "SQU-BC-STR-001",
                "product_code": "BC-STR-001",
                "category_code": "BC",
                "description": "Strategic planning and business development consulting",
                "unit": "Days"
            },
            {
                "name": "Digital Transformation",
                "squ_code": "SQU-BC-DIG-001",
                "product_code": "BC-DIG-001",
                "category_code": "BC",
                "description": "Complete digital transformation strategy and implementation",
                "unit": "Project"
            },
            
            # Training Services
            {
                "name": "Technical Training Program",
                "squ_code": "SQU-TS-TEC-001",
                "product_code": "TS-TEC-001",
                "category_code": "TS",
                "description": "Comprehensive technical training for teams",
                "unit": "Days"
            },
            {
                "name": "Certification Program",
                "squ_code": "SQU-TS-CER-001",
                "product_code": "TS-CER-001",
                "category_code": "TS",
                "description": "Professional certification training programs",
                "unit": "Course"
            }
        ]
        
        product_map = {}
        for product_data in products_data:
            category_id = category_map.get(product_data["category_code"])
            
            product = {
                "id": str(uuid.uuid4()),
                "name": product_data["name"],
                "squ_code": product_data["squ_code"],
                "product_code": product_data["product_code"],
                "primary_category_id": category_id,
                "description": product_data["description"],
                "unit": product_data["unit"],
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            existing = db.mst_products.find_one({"product_code": product_data["product_code"]})
            if not existing:
                db.mst_products.insert_one(product)
                product_map[product_data["product_code"]] = product["id"]
                print(f"   ✅ Created: {product_data['name']} ({product_data['squ_code']})")
            else:
                product_map[product_data["product_code"]] = existing["id"]
                print(f"   ✅ Using existing: {existing['name']} ({existing.get('squ_code', 'N/A')})")
        
        # Step 3: Create Rate Cards
        print("\n3. Creating Rate Cards...")
        
        rate_cards = [
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Standard Pricing 2024",
                "rate_card_code": "STD-2024",
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "description": "Standard pricing for all services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Premium Pricing 2024", 
                "rate_card_code": "PRM-2024",
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "description": "Premium pricing for enterprise clients",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Bulk Discount 2024",
                "rate_card_code": "BLK-2024", 
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "description": "Discounted pricing for bulk orders",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        rate_card_map = {}
        for rate_card in rate_cards:
            existing = db.mst_rate_cards.find_one({"rate_card_code": rate_card["rate_card_code"]})
            if not existing:
                db.mst_rate_cards.insert_one(rate_card)
                rate_card_map[rate_card["rate_card_code"]] = rate_card["id"]
                print(f"   ✅ Created: {rate_card['rate_card_name']} ({rate_card['rate_card_code']})")
            else:
                rate_card_map[rate_card["rate_card_code"]] = existing["id"]
                print(f"   ✅ Using existing: {existing['rate_card_name']} ({existing.get('rate_card_code', 'N/A')})")
        
        # Step 4: Create Sales Prices
        print("\n4. Creating Sales Prices...")
        
        # Define base prices for products
        base_pricing = {
            "SD-WEB-001": 500000,   # Custom Web Application
            "SD-MOB-001": 800000,   # Mobile App Development  
            "SD-ECM-001": 1200000,  # E-commerce Platform
            "SD-CRM-001": 600000,   # CRM System
            "SD-ERP-001": 2000000,  # ERP Solution
            "IT-NET-001": 300000,   # Network Setup
            "IT-CLD-001": 800000,   # Cloud Migration
            "IT-SRV-001": 50000,    # Server Management (monthly)
            "DM-SEO-001": 25000,    # SEO Package (monthly)
            "DM-SMM-001": 35000,    # Social Media Management (monthly)
            "DM-ADS-001": 40000,    # Google Ads Campaign (monthly)
            "BC-STR-001": 15000,    # Business Strategy Consulting (daily)
            "BC-DIG-001": 1500000,  # Digital Transformation
            "TS-TEC-001": 12000,    # Technical Training (daily)
            "TS-CER-001": 75000     # Certification Program
        }
        
        # Price multipliers for different rate cards
        multipliers = {
            "STD-2024": 1.0,    # Standard
            "PRM-2024": 1.5,    # Premium
            "BLK-2024": 0.8     # Bulk Discount
        }
        
        sales_prices_created = 0
        for rate_card_code, rate_card_id in rate_card_map.items():
            multiplier = multipliers[rate_card_code]
            print(f"   Creating prices for {rate_card_code} (x{multiplier})...")
            
            for product_code, base_price in base_pricing.items():
                if product_code in product_map:
                    product_id = product_map[product_code]
                    sales_price = int(base_price * multiplier)
                    
                    existing_price = db.mst_sales_prices.find_one({
                        "rate_card_id": rate_card_id,
                        "product_id": product_id
                    })
                    
                    if not existing_price:
                        price_record = {
                            "id": str(uuid.uuid4()),
                            "rate_card_id": rate_card_id,
                            "product_id": product_id,
                            "sales_price": sales_price,
                            "pricing_type": "recurring" if product_code in ["IT-SRV-001", "DM-SEO-001", "DM-SMM-001", "DM-ADS-001"] else "one_time",
                            "effective_date": datetime.now(timezone.utc),
                            "is_active": True,
                            "created_by": "system",
                            "created_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }
                        
                        db.mst_sales_prices.insert_one(price_record)
                        sales_prices_created += 1
                        
                        # Find product name for display
                        product_name = next((p["name"] for p in products_data if p["product_code"] == product_code), product_code)
                        print(f"     ✅ {product_name}: ₹{sales_price:,}")
        
        # Step 5: Create Purchase Costs
        print("\n5. Creating Purchase Costs...")
        
        purchase_costs_created = 0
        for product_code, base_price in base_pricing.items():
            if product_code in product_map:
                product_id = product_map[product_code]
                
                existing_cost = db.mst_purchase_costs.find_one({"product_id": product_id})
                if not existing_cost:
                    # Purchase cost is typically 60-70% of sales price
                    purchase_cost = int(base_price * 0.65)
                    
                    cost_record = {
                        "id": str(uuid.uuid4()),
                        "product_id": product_id,
                        "purchase_cost": purchase_cost,
                        "cost_type": "standard",
                        "vendor": "Default Vendor",
                        "effective_date": datetime.now(timezone.utc),
                        "notes": f"Standard cost for {product_code}",
                        "is_active": True,
                        "created_by": "system",
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    
                    db.mst_purchase_costs.insert_one(cost_record)
                    purchase_costs_created += 1
                    
                    margin = base_price - purchase_cost
                    margin_percent = (margin / base_price) * 100
                    
                    product_name = next((p["name"] for p in products_data if p["product_code"] == product_code), product_code)
                    print(f"   ✅ {product_name}: Cost ₹{purchase_cost:,} | Sales ₹{base_price:,} | Margin {margin_percent:.1f}%")
        
        # Step 6: Verification
        print("\n6. Final Verification...")
        
        counts = {
            "Primary Categories": db.mst_primary_categories.count_documents({"is_active": True}),
            "Products": db.mst_products.count_documents({"is_active": True}),
            "Products with SQU": db.mst_products.count_documents({"squ_code": {"$exists": True, "$ne": None}}),
            "Rate Cards": db.mst_rate_cards.count_documents({"is_active": True}),
            "Sales Prices": db.mst_sales_prices.count_documents({"is_active": True}),
            "Purchase Costs": db.mst_purchase_costs.count_documents({"is_active": True})
        }
        
        print("   📊 Final Data Counts:")
        for category, count in counts.items():
            print(f"     • {category}: {count} records")
        
        # Sample data verification
        print("\n   💰 Sample Product Pricing:")
        sample_products = list(db.mst_products.find({"squ_code": {"$exists": True}}).limit(3))
        for product in sample_products:
            name = product.get("name", "N/A")
            squ = product.get("squ_code", "N/A")
            
            # Get standard pricing
            standard_rate_card_id = rate_card_map.get("STD-2024")
            price_record = db.mst_sales_prices.find_one({
                "product_id": product["id"],
                "rate_card_id": standard_rate_card_id
            })
            price = price_record.get("sales_price", 0) if price_record else 0
            
            cost_record = db.mst_purchase_costs.find_one({"product_id": product["id"]})
            cost = cost_record.get("purchase_cost", 0) if cost_record else 0
            
            margin = ((price - cost) / price * 100) if price > 0 else 0
            print(f"     • {name} ({squ}): Sales ₹{price:,} | Cost ₹{cost:,} | Margin {margin:.1f}%")
        
        print(f"\n✅ COMPREHENSIVE DUMMY DATA CREATION COMPLETED!")
        print("   🎯 SUMMARY:")
        print(f"   • Primary Categories: {len(primary_categories)} created")
        print(f"   • Products with SQU codes: {len(products_data)} created")
        print(f"   • Rate Cards: {len(rate_cards)} created")
        print(f"   • Sales Prices: {sales_prices_created} created")
        print(f"   • Purchase Costs: {purchase_costs_created} created")
        print("   🎉 READY FOR QUOTATION WORKFLOW AND TESTING!")
        
    except Exception as e:
        print(f"❌ Error creating dummy data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_comprehensive_dummy_data())