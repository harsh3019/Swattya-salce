#!/usr/bin/env python3
"""
Script to check for standalone Master Data module and remove it if exists
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/sawayatta_erp')

async def check_master_data_module():
    """Check for standalone Master Data module"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.sawayatta_erp
    
    try:
        # Check if there's a standalone Master Data module
        master_data_module = await db.modules.find_one({"name": "Master Data"})
        
        if master_data_module:
            print(f"✅ Found Master Data module: {master_data_module['id']}")
            
            # Check if it has any menus
            menus = await db.menus.find({
                "module_id": master_data_module["id"],
                "status": "active"
            }).to_list(length=None)
            
            print(f"📋 Master Data module has {len(menus)} menus:")
            for menu in menus:
                print(f"  - {menu['name']} ({menu['path']})")
            
            if len(menus) == 0:
                print("⚠️  Master Data module has no menus, considering removal...")
                # Optionally remove empty module
                # await db.modules.update_one(
                #     {"id": master_data_module["id"]},
                #     {"$set": {"status": "inactive"}}
                # )
                # print("✅ Deactivated empty Master Data module")
        else:
            print("ℹ️  No standalone Master Data module found")
        
        # List all current modules
        print("\n📊 All current modules:")
        modules = await db.modules.find({"status": "active"}).to_list(length=None)
        for module in modules:
            menu_count = await db.menus.count_documents({
                "module_id": module["id"],
                "status": "active"
            })
            print(f"  - {module['name']}: {menu_count} menus")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_master_data_module())