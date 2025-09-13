#!/usr/bin/env python3
"""
Fix Stage Master Data - Ensure proper L1-L8 stages are initialized
"""

import asyncio
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import os

async def fix_stage_master_data():
    """Fix and properly initialize stage master data"""
    print("🔧 FIXING STAGE MASTER DATA")
    print("=" * 50)
    
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.sawayatta_erp
    
    try:
        # Delete all existing stages to ensure clean slate
        print("1. Clearing existing stage data...")
        result = db.mst_stages.delete_many({})
        print(f"   Deleted {result.deleted_count} existing stages")
        
        # Initialize proper stages data
        print("2. Initializing proper L1-L8 stages...")
        stages_data = [
            {"stage_name": "Prospect", "stage_code": "L1", "stage_order": 1, "description": "Initial prospect identification and qualification"},
            {"stage_name": "Qualification", "stage_code": "L2", "stage_order": 2, "description": "Detailed qualification using BANT/CHAMP methodology"},
            {"stage_name": "Proposal", "stage_code": "L3", "stage_order": 3, "description": "Proposal creation and submission"},
            {"stage_name": "Technical Qualification", "stage_code": "L4", "stage_order": 4, "description": "Technical evaluation and quotation selection"},
            {"stage_name": "Commercial Negotiation", "stage_code": "L5", "stage_order": 5, "description": "Price negotiation and commercial terms"},
            {"stage_name": "Won", "stage_code": "L6", "stage_order": 6, "description": "Deal won and handover to delivery"},
            {"stage_name": "Lost", "stage_code": "L7", "stage_order": 7, "description": "Deal lost - capture learning and feedback"},
            {"stage_name": "Dropped", "stage_code": "L8", "stage_order": 8, "description": "Opportunity dropped - no longer active"}
        ]
        
        for stage_data in stages_data:
            stage_record = {
                "id": str(uuid.uuid4()),
                **stage_data,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            db.mst_stages.insert_one(stage_record)
            print(f"   ✅ Inserted stage: {stage_data['stage_code']} - {stage_data['stage_name']}")
        
        # Verify the stages
        print("\n3. Verifying stage data...")
        stages = list(db.mst_stages.find({"is_active": True}).sort("stage_order", 1))
        print(f"   Total stages found: {len(stages)}")
        
        for stage in stages:
            print(f"   {stage['stage_code']} - {stage['stage_name']} (Order: {stage['stage_order']})")
            
        # Check if there are opportunities to update
        print("\n4. Checking existing opportunities...")
        opportunities = list(db.opportunities.find({}))
        print(f"   Total opportunities found: {len(opportunities)}")
        
        if opportunities:
            print("   Sample opportunity current_stage values:")
            for i, opp in enumerate(opportunities[:5]):  # Show first 5
                current_stage = opp.get('current_stage', 'N/A')
                opp_id = opp.get('id', opp.get('_id', 'N/A'))
                project_title = opp.get('project_title', 'N/A')[:50] + '...' if len(opp.get('project_title', '')) > 50 else opp.get('project_title', 'N/A')
                print(f"   {i+1}. {opp_id}: Stage L{current_stage} - {project_title}")
        
        print("\n✅ STAGE MASTER DATA FIX COMPLETED")
        print("   - All L1-L8 stages properly initialized")
        print("   - Stage codes and names are correct")
        print("   - Ready for opportunity stage management testing")
        
    except Exception as e:
        print(f"❌ Error fixing stage master data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_stage_master_data())