#!/usr/bin/env python3
"""
Create Comprehensive Master Data for Sawayatta ERP
Primary Categories, Products with SQU codes, Rate Cards, Purchase Costs
"""

import asyncio
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import os

async def create_comprehensive_master_data():
    """Create comprehensive master data for all modules"""
    print("🌱 CREATING COMPREHENSIVE MASTER DATA FOR SAWAYATTA ERP")
    print("=" * 70)
    
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.sawayatta_erp
    
    try:
        # Step 1: Create Primary Categories
        print("1. Creating Primary Categories...")
        categories_data = [
            {
                "id": str(uuid.uuid4()),
                "category_name": "Software Development",
                "category_code": "SD",
                "description": "Custom software development and programming services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "IT Infrastructure",
                "category_code": "IT",
                "description": "Network setup, server management, and IT infrastructure services",
                "is_active": True,
                "created_by": "system", 
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "Digital Marketing",
                "category_code": "DM",
                "description": "Digital marketing, SEO, social media, and online advertising services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "Consulting Services",
                "category_code": "CS",
                "description": "Business consulting, strategy, and advisory services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "category_name": "Training & Support", 
                "category_code": "TS",
                "description": "Professional training, workshops, and technical support services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        category_ids = {}
        for category_data in categories_data:
            existing = db.mst_primary_categories.find_one({"category_code": category_data["category_code"]})
            if not existing:
                db.mst_primary_categories.insert_one(category_data)
                category_ids[category_data["category_code"]] = category_data["id"]
                print(f"   ✅ Created category: {category_data['category_name']} ({category_data['category_code']})")
            else:
                category_ids[category_data["category_code"]] = existing["id"]
                print(f"   ✅ Using existing category: {existing['category_name']} ({existing['category_code']})")
        
        # Step 2: Create Products with SQU codes
        print("\n2. Creating Products with SQU codes...")
        products_data = [
            # Software Development Category
            {
                "id": str(uuid.uuid4()),
                "product_name": "Custom Web Application",
                "product_code": "SD-WEB-001",
                "squ_code": "SQU-SD-WEB-001",
                "primary_category_id": category_ids["SD"],
                "unit": "Project",
                "description": "Custom web application development with responsive design",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "Mobile App Development",
                "product_code": "SD-MOB-001", 
                "squ_code": "SQU-SD-MOB-001",
                "primary_category_id": category_ids["SD"],
                "unit": "Project",
                "description": "Native and cross-platform mobile application development",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "ERP System Implementation",
                "product_code": "SD-ERP-001",
                "squ_code": "SQU-SD-ERP-001", 
                "primary_category_id": category_ids["SD"],
                "unit": "License",
                "description": "Complete ERP system implementation and customization",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            # IT Infrastructure Category
            {
                "id": str(uuid.uuid4()),
                "product_name": "Network Setup & Configuration",
                "product_code": "IT-NET-001",
                "squ_code": "SQU-IT-NET-001",
                "primary_category_id": category_ids["IT"],
                "unit": "Project",
                "description": "Complete network infrastructure setup and configuration",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "Cloud Migration Services",
                "product_code": "IT-CLD-001",
                "squ_code": "SQU-IT-CLD-001",
                "primary_category_id": category_ids["IT"],
                "unit": "Project",
                "description": "Migration of infrastructure and applications to cloud platforms",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            # Digital Marketing Category
            {
                "id": str(uuid.uuid4()),
                "product_name": "SEO Optimization Package",
                "product_code": "DM-SEO-001",
                "squ_code": "SQU-DM-SEO-001",
                "primary_category_id": category_ids["DM"],
                "unit": "Month",
                "description": "Complete SEO optimization and ranking improvement services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "Social Media Management",
                "product_code": "DM-SMM-001",
                "squ_code": "SQU-DM-SMM-001",
                "primary_category_id": category_ids["DM"],
                "unit": "Month",
                "description": "Complete social media management and content creation",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            # Consulting Services Category
            {
                "id": str(uuid.uuid4()),
                "product_name": "Business Strategy Consulting",
                "product_code": "CS-STR-001",
                "squ_code": "SQU-CS-STR-001",
                "primary_category_id": category_ids["CS"],
                "unit": "Days",
                "description": "Strategic planning and business development consulting",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "IT Process Consulting",
                "product_code": "CS-ITP-001", 
                "squ_code": "SQU-CS-ITP-001",
                "primary_category_id": category_ids["CS"],
                "unit": "Days",
                "description": "IT process optimization and digital transformation consulting",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            # Training & Support Category
            {
                "id": str(uuid.uuid4()),
                "product_name": "Technical Training Program",
                "product_code": "TS-TTP-001",
                "squ_code": "SQU-TS-TTP-001",
                "primary_category_id": category_ids["TS"],
                "unit": "Days",
                "description": "Comprehensive technical training and skill development program",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "product_name": "24/7 Technical Support",
                "product_code": "TS-SUP-001",
                "squ_code": "SQU-TS-SUP-001",
                "primary_category_id": category_ids["TS"],
                "unit": "Month",
                "description": "Round-the-clock technical support and maintenance services",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        product_ids = []
        for product_data in products_data:
            existing = db.mst_products.find_one({"product_code": product_data["product_code"]})
            if not existing:
                db.mst_products.insert_one(product_data)
                product_ids.append(product_data)
                print(f"   ✅ Created product: {product_data['product_name']} ({product_data['squ_code']})")
            else:
                product_ids.append(existing)
                print(f"   ✅ Using existing product: {existing['product_name']} ({existing.get('squ_code', 'N/A')})")
        
        # Step 3: Create Rate Cards
        print("\n3. Creating Rate Cards...")
        rate_cards_data = [
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Standard Rate Card 2024",
                "rate_card_code": "SRC-2024",
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "description": "Standard pricing for all services - effective 2024",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Premium Rate Card 2024",
                "rate_card_code": "PRC-2024",
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "description": "Premium pricing for enterprise clients - 2024",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "rate_card_name": "Discount Rate Card 2024",
                "rate_card_code": "DRC-2024",
                "effective_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_to": datetime(2024, 12, 31, tzinfo=timezone.utc),
                "description": "Discounted pricing for bulk orders and long-term contracts",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        rate_card_ids = []
        for rate_card_data in rate_cards_data:
            existing = db.mst_rate_cards.find_one({"rate_card_code": rate_card_data["rate_card_code"]})
            if not existing:
                db.mst_rate_cards.insert_one(rate_card_data)
                rate_card_ids.append(rate_card_data)
                print(f"   ✅ Created rate card: {rate_card_data['rate_card_name']} ({rate_card_data['rate_card_code']})")
            else:
                rate_card_ids.append(existing)
                print(f"   ✅ Using existing rate card: {existing['rate_card_name']} ({existing.get('rate_card_code', 'N/A')})")
        
        # Step 4: Create Sales Prices for each Rate Card
        print("\n4. Creating Sales Prices...")
        
        # Define pricing matrix (product_code: [standard_price, premium_price, discount_price])
        pricing_matrix = {
            "SD-WEB-001": [500000, 750000, 400000],  # Custom Web Application
            "SD-MOB-001": [800000, 1200000, 640000],  # Mobile App Development
            "SD-ERP-001": [2000000, 3000000, 1600000],  # ERP System Implementation
            "IT-NET-001": [300000, 450000, 240000],  # Network Setup & Configuration
            "IT-CLD-001": [600000, 900000, 480000],  # Cloud Migration Services
            "DM-SEO-001": [25000, 40000, 20000],  # SEO Optimization Package (per month)
            "DM-SMM-001": [35000, 50000, 28000],  # Social Media Management (per month)
            "CS-STR-001": [15000, 25000, 12000],  # Business Strategy Consulting (per day)
            "CS-ITP-001": [18000, 30000, 14400],  # IT Process Consulting (per day)
            "TS-TTP-001": [12000, 20000, 9600],  # Technical Training Program (per day)
            "TS-SUP-001": [45000, 70000, 36000]  # 24/7 Technical Support (per month)
        }
        
        sales_prices_created = 0
        for i, rate_card in enumerate(rate_card_ids):
            rate_card_id = rate_card["id"]
            rate_card_name = rate_card["rate_card_name"]
            
            print(f"   Creating prices for {rate_card_name}...")
            
            for product in product_ids:
                product_code = product["product_code"]
                if product_code in pricing_matrix:
                    sales_price = pricing_matrix[product_code][i]  # Use index to get price tier
                    
                    sales_price_data = {
                        "id": str(uuid.uuid4()),
                        "rate_card_id": rate_card_id,
                        "product_id": product["id"],
                        "sales_price": sales_price,
                        "pricing_type": "one_time" if product["unit"] in ["Project", "License"] else "recurring",
                        "effective_date": datetime.now(timezone.utc),
                        "is_active": True,
                        "created_by": "system",
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    
                    existing_price = db.mst_sales_prices.find_one({
                        "rate_card_id": rate_card_id,
                        "product_id": product["id"]
                    })
                    
                    if not existing_price:
                        db.mst_sales_prices.insert_one(sales_price_data)
                        sales_prices_created += 1
                        print(f"     ✅ {product['product_name']}: ₹{sales_price:,}")
                    else:
                        print(f"     ✅ Using existing price for {product['product_name']}: ₹{existing_price.get('sales_price', 0):,}")
        
        # Step 5: Create Purchase Costs (Cost Prices)
        print("\n5. Creating Purchase Costs...")
        
        # Purchase costs are typically 60-70% of sales price
        purchase_cost_multiplier = 0.65  # 65% of sales price
        
        purchase_costs_created = 0
        for product in product_ids:
            # Use standard rate card for purchase cost calculation
            standard_rate_card = rate_card_ids[0]  # First one is standard
            
            # Find sales price for this product in standard rate card
            sales_price_record = db.mst_sales_prices.find_one({
                "rate_card_id": standard_rate_card["id"],
                "product_id": product["id"]
            })
            
            if sales_price_record:
                sales_price = sales_price_record["sales_price"]
                purchase_cost = int(sales_price * purchase_cost_multiplier)
                
                purchase_cost_data = {
                    "id": str(uuid.uuid4()),
                    "product_id": product["id"],
                    "purchase_cost": purchase_cost,
                    "cost_type": "standard",
                    "effective_date": datetime.now(timezone.utc),
                    "vendor": "Default Vendor",
                    "notes": f"Calculated as {int(purchase_cost_multiplier*100)}% of standard sales price",
                    "is_active": True,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                
                existing_cost = db.mst_purchase_costs.find_one({
                    "product_id": product["id"],
                    "cost_type": "standard"
                })
                
                if not existing_cost:
                    db.mst_purchase_costs.insert_one(purchase_cost_data)
                    purchase_costs_created += 1
                    margin = sales_price - purchase_cost
                    margin_percent = (margin / sales_price) * 100
                    print(f"   ✅ {product['product_name']}: Cost ₹{purchase_cost:,} | Sales ₹{sales_price:,} | Margin {margin_percent:.1f}%")
                else:
                    existing_cost_value = existing_cost.get("purchase_cost", 0)
                    print(f"   ✅ Using existing cost for {product['product_name']}: ₹{existing_cost_value:,}")
        
        # Step 6: Create Additional Master Data for Completeness
        print("\n6. Creating Additional Master Data...")
        
        # Create Units if not exists
        units_data = [
            {"id": str(uuid.uuid4()), "unit_name": "Project", "unit_code": "PRJ", "description": "Project-based pricing", "is_active": True},
            {"id": str(uuid.uuid4()), "unit_name": "License", "unit_code": "LIC", "description": "Software license", "is_active": True},
            {"id": str(uuid.uuid4()), "unit_name": "Month", "unit_code": "MON", "description": "Monthly subscription", "is_active": True},
            {"id": str(uuid.uuid4()), "unit_name": "Days", "unit_code": "DAY", "description": "Daily rate", "is_active": True},
            {"id": str(uuid.uuid4()), "unit_name": "Hours", "unit_code": "HRS", "description": "Hourly rate", "is_active": True}
        ]
        
        for unit_data in units_data:
            existing_unit = db.mst_units.find_one({"unit_code": unit_data["unit_code"]})
            if not existing_unit:
                unit_data.update({
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                db.mst_units.insert_one(unit_data)
                print(f"   ✅ Created unit: {unit_data['unit_name']} ({unit_data['unit_code']})")
            else:
                print(f"   ✅ Using existing unit: {existing_unit['unit_name']} ({existing_unit['unit_code']})")
        
        # Step 7: Verification
        print("\n7. Verifying Created Master Data...")
        
        verification_results = {
            "Primary Categories": db.mst_primary_categories.count_documents({"is_active": True}),
            "Products": db.mst_products.count_documents({"is_active": True}),
            "Rate Cards": db.mst_rate_cards.count_documents({"is_active": True}),
            "Sales Prices": db.mst_sales_prices.count_documents({"is_active": True}),
            "Purchase Costs": db.mst_purchase_costs.count_documents({"is_active": True}),
            "Units": db.mst_units.count_documents({"is_active": True})
        }
        
        print(f"   📊 Verification Results:")
        for category, count in verification_results.items():
            print(f"     • {category}: {count} records")
        
        # Check for products with SQU codes
        products_with_squ = db.mst_products.count_documents({"squ_code": {"$exists": True, "$ne": None}})
        print(f"     • Products with SQU codes: {products_with_squ} records")
        
        # Sample pricing verification
        print(f"\n   💰 Sample Pricing Verification:")
        sample_products = list(db.mst_products.find({"is_active": True}).limit(3))
        for product in sample_products:
            product_name = product['product_name']
            squ_code = product.get('squ_code', 'N/A')
            
            # Get sales price from standard rate card
            sales_price_record = db.mst_sales_prices.find_one({
                "product_id": product["id"],
                "rate_card_id": rate_card_ids[0]["id"]
            })
            sales_price = sales_price_record["sales_price"] if sales_price_record else 0
            
            # Get purchase cost
            purchase_cost_record = db.mst_purchase_costs.find_one({
                "product_id": product["id"]
            })
            purchase_cost = purchase_cost_record["purchase_cost"] if purchase_cost_record else 0
            
            margin = sales_price - purchase_cost
            margin_percent = (margin / sales_price * 100) if sales_price > 0 else 0
            
            print(f"     • {product_name} ({squ_code})")
            print(f"       Sales: ₹{sales_price:,} | Cost: ₹{purchase_cost:,} | Margin: {margin_percent:.1f}%")
        
        print(f"\n✅ COMPREHENSIVE MASTER DATA CREATION COMPLETED!")
        print("   🎯 READY FOR:")
        print("   • Quotation creation with proper products and pricing")
        print("   • Rate card management and pricing strategies")
        print("   • Purchase cost analysis and margin calculations")
        print("   • Complete opportunity-to-order workflow")
        
        all_data_created = all(count > 0 for count in verification_results.values())
        if all_data_created and products_with_squ > 0:
            print("   🎉 ALL MASTER DATA SUCCESSFULLY CREATED WITH SQU CODES!")
        else:
            print("   ⚠️ Some master data creation may have incomplete")
            
    except Exception as e:
        print(f"❌ Error creating comprehensive master data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_comprehensive_master_data())