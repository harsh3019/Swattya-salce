#!/usr/bin/env python3
"""
Script to add Master Data menu items to the Sales module in the sidebar
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/sawayatta_erp')

async def add_master_data_to_sales():
    """Add master data menu items to Sales module"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.sawayatta_erp
    
    try:
        # Sales module ID (from the API response)
        sales_module_id = "fe76408c-d68e-48ea-9c25-2392e945528a"
        
        # Master data menu items to add
        master_data_menus = [
            {
                "name": "Primary Categories",
                "path": "/master-data/primary-categories",
                "order_index": 8
            },
            {
                "name": "Products",
                "path": "/master-data/products",
                "order_index": 9
            },
            {
                "name": "Rate Cards",
                "path": "/master-data/rate-cards",
                "order_index": 10
            },
            {
                "name": "Sales Prices",
                "path": "/master-data/sales-prices",
                "order_index": 11
            },
            {
                "name": "Purchase Costs",
                "path": "/master-data/purchase-costs",
                "order_index": 12
            }
        ]
        
        # Get the View permission ID
        view_permission = await db.permissions.find_one({"name": "View"})
        if not view_permission:
            print("❌ View permission not found")
            return
        
        view_permission_id = view_permission["id"]
        print(f"✅ Found View permission ID: {view_permission_id}")
        
        # Get admin role ID (should have access to all master data)
        admin_role = await db.roles.find_one({"name": "Super Admin"})
        if not admin_role:
            print("❌ Super Admin role not found")
            return
        
        admin_role_id = admin_role["id"]
        print(f"✅ Found Super Admin role ID: {admin_role_id}")
        
        # Add each master data menu to Sales module
        for menu_data in master_data_menus:
            menu_id = str(uuid.uuid4())
            
            # Check if menu already exists
            existing_menu = await db.menus.find_one({
                "path": menu_data["path"],
                "module_id": sales_module_id
            })
            
            if existing_menu:
                print(f"⚠️  Menu '{menu_data['name']}' already exists in Sales module")
                continue
            
            # Create menu entry
            menu_doc = {
                "id": menu_id,
                "name": menu_data["name"],
                "path": menu_data["path"],
                "module_id": sales_module_id,
                "parent": None,
                "order_index": menu_data["order_index"],
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": "system",
                "updated_by": None
            }
            
            await db.menus.insert_one(menu_doc)
            print(f"✅ Created menu: {menu_data['name']}")
            
            # Create role permission for admin role
            role_permission_id = str(uuid.uuid4())
            role_permission_doc = {
                "id": role_permission_id,
                "role_id": admin_role_id,
                "permission_id": view_permission_id,
                "menu_id": menu_id,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": "system",
                "updated_by": None
            }
            
            await db.role_permissions.insert_one(role_permission_doc)
            print(f"✅ Created role permission for: {menu_data['name']}")
        
        print("\n🎉 Successfully added all master data menus to Sales module!")
        
        # Verify the additions
        print("\n📋 Verifying additions...")
        sales_menus = await db.menus.find({
            "module_id": sales_module_id,
            "status": "active"
        }).sort("order_index", 1).to_list(length=None)
        
        print(f"\n📊 Sales module now has {len(sales_menus)} menus:")
        for menu in sales_menus:
            print(f"  - {menu['order_index']}: {menu['name']} ({menu['path']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_master_data_to_sales())