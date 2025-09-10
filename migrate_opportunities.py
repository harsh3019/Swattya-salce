#!/usr/bin/env python3
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def migrate_opportunities():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/sawayatta_erp')
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()
    
    # Get default currency ID (INR)
    inr_currency = await db.mst_currencies.find_one({"currency_code": "INR"})
    currency_id = inr_currency["id"] if inr_currency else "default-inr-id"
    
    # Find all opportunities with old structure
    old_opportunities = await db.opportunities.find({
        "$or": [
            {"project_title": {"$exists": False}},
            {"current_stage": {"$exists": False}},
            {"status": {"$exists": False}}
        ]
    }).to_list(None)
    
    print(f"Found {len(old_opportunities)} opportunities to migrate")
    
    for opp in old_opportunities:
        update_data = {}
        
        # Map old fields to new fields
        if not opp.get("project_title") and opp.get("name"):
            update_data["project_title"] = opp["name"]
            
        if not opp.get("current_stage"):
            if opp.get("stage") == "Qualification":
                update_data["current_stage"] = 1
            else:
                update_data["current_stage"] = 1
                
        if not opp.get("status"):
            update_data["status"] = "Active"
            
        if not opp.get("win_probability") and opp.get("probability"):
            update_data["win_probability"] = float(opp["probability"])
            
        if not opp.get("expected_revenue") and opp.get("expected_value"):
            update_data["expected_revenue"] = float(opp["expected_value"])
            
        if not opp.get("lead_owner_id") and opp.get("owner_user_id"):
            update_data["lead_owner_id"] = opp["owner_user_id"]
            
        if not opp.get("currency_id"):
            update_data["currency_id"] = currency_id
            
        # Calculate weighted revenue if missing
        if not opp.get("weighted_revenue"):
            expected_revenue = update_data.get("expected_revenue", opp.get("expected_revenue", 0))
            win_probability = update_data.get("win_probability", opp.get("win_probability", 25))
            update_data["weighted_revenue"] = float(expected_revenue) * (float(win_probability) / 100)
        
        # Add stage history if missing
        if not opp.get("stage_history"):
            update_data["stage_history"] = [{
                "from_stage": 0,
                "to_stage": update_data.get("current_stage", 1),
                "changed_by": opp.get("created_by", "system"),
                "changed_at": opp.get("created_at", datetime.now(timezone.utc)),
                "notes": "Migration - Initial stage assignment"
            }]
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update the opportunity
        if update_data:
            await db.opportunities.update_one(
                {"id": opp["id"]},
                {"$set": update_data}
            )
            print(f"Migrated opportunity: {opp['id']} - {update_data.get('project_title', opp.get('name', 'Unknown'))}")
    
    print("Migration completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_opportunities())