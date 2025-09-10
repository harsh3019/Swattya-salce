#!/usr/bin/env python3
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def init_regions():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/sawayatta_erp')
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()
    
    # Initialize Regions
    regions_data = [
        {"region_name": "North India", "region_code": "NORTH", "description": "Delhi, Punjab, Haryana, Uttar Pradesh, Himachal Pradesh"},
        {"region_name": "South India", "region_code": "SOUTH", "description": "Karnataka, Tamil Nadu, Andhra Pradesh, Telangana, Kerala"},
        {"region_name": "West India", "region_code": "WEST", "description": "Maharashtra, Gujarat, Rajasthan, Goa"},
        {"region_name": "East India", "region_code": "EAST", "description": "West Bengal, Odisha, Jharkhand, Bihar"},
        {"region_name": "Central India", "region_code": "CENTRAL", "description": "Madhya Pradesh, Chhattisgarh"},
        {"region_name": "Northeast India", "region_code": "NORTHEAST", "description": "Assam, Meghalaya, Manipur, Mizoram, Nagaland, Tripura, Arunachal Pradesh, Sikkim"}
    ]
    
    for region_data in regions_data:
        existing = await db.mst_regions.find_one({"region_code": region_data["region_code"]})
        if not existing:
            region_record = {
                "id": str(uuid.uuid4()),
                **region_data,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            await db.mst_regions.insert_one(region_record)
            print(f"Inserted region: {region_data['region_name']}")
        else:
            print(f"Region already exists: {region_data['region_name']}")
    
    # Initialize Competitors
    competitors_data = [
        {"competitor_name": "TCS", "competitor_type": "Direct", "description": "Tata Consultancy Services - Leading IT services company", "strengths": "Brand recognition, large scale operations", "weaknesses": "Higher pricing, slower decision making"},
        {"competitor_name": "Infosys", "competitor_type": "Direct", "description": "Global leader in consulting and technology services", "strengths": "Strong delivery capabilities, innovation focus", "weaknesses": "Premium pricing, complex processes"},
        {"competitor_name": "Wipro", "competitor_type": "Direct", "description": "Leading technology services and consulting company", "strengths": "Domain expertise, global presence", "weaknesses": "Limited market share in certain segments"},
        {"competitor_name": "HCL Technologies", "competitor_type": "Direct", "description": "Technology and services company", "strengths": "Competitive pricing, agile delivery", "weaknesses": "Brand perception in premium segment"},
        {"competitor_name": "Local System Integrators", "competitor_type": "Indirect", "description": "Regional players and system integrators", "strengths": "Local market knowledge, flexible pricing", "weaknesses": "Limited scale, technology capabilities"}
    ]
    
    for competitor_data in competitors_data:
        existing = await db.mst_competitors.find_one({"competitor_name": competitor_data["competitor_name"]})
        if not existing:
            competitor_record = {
                "id": str(uuid.uuid4()),
                **competitor_data,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }
            await db.mst_competitors.insert_one(competitor_record)
            print(f"Inserted competitor: {competitor_data['competitor_name']}")
        else:
            print(f"Competitor already exists: {competitor_data['competitor_name']}")

    print("Region and Competitor initialization completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(init_regions())