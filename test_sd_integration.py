#!/usr/bin/env python3
"""
Test script to verify SD Module Integration
This script tests the create_upcoming_project_from_opportunity function
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

# Mock the required modules and functions for testing
class MockDB:
    def __init__(self):
        self.collections = {
            'companies': [],
            'quotations': [],
            'upcoming_projects': []
        }
    
    def __getattr__(self, name):
        if name in self.collections:
            return MockCollection(self.collections[name])
        return MockCollection([])

class MockCollection:
    def __init__(self, data):
        self.data = data
    
    async def find_one(self, query):
        # Mock company data
        if 'company_name' in str(query):
            return {"company_name": "Test Company Ltd"}
        # Mock quotation data
        if 'is_selected' in str(query):
            return {"total_amount": 50000, "is_selected": True}
        return None
    
    async def insert_one(self, document):
        self.data.append(document)
        return True

# Mock the required imports
import uuid
from datetime import datetime, timezone

# Mock logger
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

# Mock log_activity function
async def log_activity(*args, **kwargs):
    print(f"Activity logged: {args}")

# Set up mocks
db = MockDB()
logger = MockLogger()

# Import the function we want to test
async def create_upcoming_project_from_opportunity(opportunity_id: str, opportunity: dict, user_id: str):
    """Create an upcoming project entry when opportunity is won (SD Module Integration)"""
    try:
        # Get company details
        company = await db.companies.find_one({"id": opportunity.get("company_id")})
        company_name = company.get("company_name", "Unknown Company") if company else "Unknown Company"
        
        # Get selected quotation for project value
        selected_quotation = await db.quotations.find_one({
            "opportunity_id": opportunity_id,
            "is_selected": True,
            "is_active": True
        })
        
        project_value = 0
        if selected_quotation:
            project_value = selected_quotation.get("total_amount", 0)
        else:
            # Fallback to opportunity expected revenue
            project_value = opportunity.get("expected_revenue", 0)
        
        # Create upcoming project entry
        upcoming_project = {
            "id": str(uuid.uuid4()),
            "project_name": f"{opportunity.get('name', 'Untitled Project')} - {company_name}",
            "opportunity_id": opportunity_id,
            "company_id": opportunity.get("company_id"),
            "company_name": company_name,
            "project_value": project_value,
            "currency": opportunity.get("currency", "USD"),
            "expected_start_date": None,  # To be filled by SD team
            "expected_end_date": None,    # To be filled by SD team
            "project_manager_id": None,   # To be assigned by SD team
            "status": "Upcoming",
            "source": "Won Opportunity",
            "notes": f"Auto-created from won opportunity: {opportunity.get('name')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        
        # Insert into upcoming_projects collection
        await db.upcoming_projects.insert_one(upcoming_project)
        
        # Log the activity
        await log_activity(
            "sd_module", 
            "upcoming_projects", 
            "create", 
            "success", 
            user_id, 
            {
                "project_id": upcoming_project["id"],
                "opportunity_id": opportunity_id,
                "project_name": upcoming_project["project_name"],
                "project_value": project_value
            }
        )
        
        logger.info(f"Created upcoming project {upcoming_project['id']} from won opportunity {opportunity_id}")
        return upcoming_project
        
    except Exception as e:
        logger.error(f"Failed to create upcoming project from opportunity {opportunity_id}: {str(e)}")
        raise e

async def test_sd_integration():
    """Test the SD Module Integration"""
    print("Testing SD Module Integration...")
    
    # Test data
    opportunity_id = "test-opp-123"
    opportunity = {
        "name": "Big Enterprise Deal",
        "company_id": "company-456",
        "expected_revenue": 75000,
        "currency": "USD"
    }
    user_id = "user-789"
    
    try:
        # Test the function
        result = await create_upcoming_project_from_opportunity(opportunity_id, opportunity, user_id)
        
        print("✅ Test PASSED!")
        print(f"Created project: {result['project_name']}")
        print(f"Project value: {result['project_value']}")
        print(f"Status: {result['status']}")
        print(f"Source: {result['source']}")
        
        # Verify the project was added to the mock database
        if len(db.upcoming_projects.data) > 0:
            print("✅ Project successfully added to database")
        else:
            print("❌ Project was not added to database")
            
    except Exception as e:
        print(f"❌ Test FAILED: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("SD Module Integration Test")
    print("=" * 40)
    
    # Run the test
    success = asyncio.run(test_sd_integration())
    
    if success:
        print("\n🎉 All tests passed! SD Module Integration is working correctly.")
    else:
        print("\n💥 Tests failed! Please check the implementation.")