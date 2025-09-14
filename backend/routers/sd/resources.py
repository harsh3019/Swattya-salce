from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, date
import uuid
import logging

# Import models
from models.sd.resource import (
    Resource, ResourceCreate, ResourceUpdate,
    ResourceAllocation, ResourceAllocationCreate, ResourceAllocationUpdate,
    PurchaseRequest, PurchaseRequestCreate, PurchaseRequestUpdate,
    ResourceType, ResourceStatus, AllocationStatus, PurchaseRequestStatus,
    ResourceUtilizationAlert, ResourceSummary
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sd/resources", tags=["Services Delivery - Resources"])

# Dependency to get database and utilities (imported when needed to avoid circular imports)
def get_db_and_utils():
    from server import db, prepare_for_mongo, prepare_for_json, log_audit_trail
    return db, prepare_for_mongo, prepare_for_json, log_audit_trail

def generate_resource_id() -> str:
    """Generate unique resource ID like RES-XXXXXXXX"""
    return f"RES-{str(uuid.uuid4())[:8].upper()}"

def generate_allocation_id() -> str:
    """Generate unique allocation ID like ALL-XXXXXXXX"""
    return f"ALL-{str(uuid.uuid4())[:8].upper()}"

def generate_pr_id() -> str:
    """Generate unique purchase request ID like PR-XXXXXXXX"""
    return f"PR-{str(uuid.uuid4())[:8].upper()}"

async def calculate_resource_utilization(resource_id: str, db) -> float:
    """Calculate resource utilization percentage"""
    try:
        resource = await db.resources.find_one({"id": resource_id, "is_active": True})
        if not resource:
            return 0.0
        
        # Get active allocations
        allocations = await db.resource_allocations.find({
            "resource_id": resource_id,
            "status": "Active",
            "is_active": True
        }).to_list(None)
        
        total_allocated = sum(allocation.get("allocated_qty", 0) for allocation in allocations)
        available_qty = resource.get("available_qty", 0)
        
        if available_qty <= 0:
            return 0.0
        
        utilization = (total_allocated / available_qty) * 100
        return min(utilization, 100.0)  # Cap at 100%
    
    except Exception as e:
        logger.error(f"Error calculating resource utilization: {str(e)}")
        return 0.0

async def update_resource_utilization(resource_id: str, db):
    """Update resource utilization and assigned quantity"""
    try:
        utilization = await calculate_resource_utilization(resource_id, db)
        
        # Get total assigned quantity
        allocations = await db.resource_allocations.find({
            "resource_id": resource_id,
            "status": "Active",
            "is_active": True
        }).to_list(None)
        
        assigned_qty = sum(allocation.get("allocated_qty", 0) for allocation in allocations)
        
        # Update resource
        await db.resources.update_one(
            {"id": resource_id},
            {"$set": {
                "assigned_qty": assigned_qty,
                "utilization": utilization,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        # Check for high utilization alert
        if utilization >= 80.0:
            await create_utilization_alert(resource_id, utilization, db)
        
        return utilization
    
    except Exception as e:
        logger.error(f"Error updating resource utilization: {str(e)}")
        return 0.0

async def create_utilization_alert(resource_id: str, utilization: float, db):
    """Create utilization alert for high usage resources"""
    try:
        resource = await db.resources.find_one({"id": resource_id})
        if not resource:
            return
        
        severity = "Critical" if utilization >= 95.0 else "Warning"
        message = f"Resource '{resource['name']}' is at {utilization:.1f}% utilization"
        
        # Check if recent alert exists (within last hour)
        one_hour_ago = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        existing_alert = await db.utilization_alerts.find_one({
            "resource_id": resource_id,
            "created_at": {"$gte": one_hour_ago}
        })
        
        if not existing_alert:
            alert = {
                "id": str(uuid.uuid4()),
                "resource_id": resource_id,
                "resource_name": resource["name"],
                "utilization": utilization,
                "threshold": 80.0,
                "severity": severity,
                "message": message,
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.utilization_alerts.insert_one(alert)
            logger.warning(f"Utilization alert created: {message}")
    
    except Exception as e:
        logger.error(f"Error creating utilization alert: {str(e)}")

# ==================== RESOURCE ENDPOINTS ====================

@router.get("/")
async def get_resources(
    type: Optional[str] = Query(None, description="Filter by resource type"),
    status: Optional[str] = Query(None, description="Filter by resource status"),
    high_utilization: bool = Query(False, description="Filter resources with ≥80% utilization"),
    limit: int = Query(50, description="Limit number of results"),
    skip: int = Query(0, description="Skip number of results")
):
    """Get list of resources with optional filtering"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        query = {"is_active": True}
        
        if type:
            query["type"] = type
        if status:
            query["status"] = status
        if high_utilization:
            query["utilization"] = {"$gte": 80.0}
        
        resources = await db.resources.find(query)\
            .sort("created_at", -1)\
            .skip(skip)\
            .limit(limit)\
            .to_list(None)
        
        return [prepare_for_json(resource) for resource in resources]
    
    except Exception as e:
        logger.error(f"Error fetching resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching resources")

@router.get("/summary")
async def get_resources_summary():
    """Get comprehensive resource summary with statistics"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Get all active resources
        resources = await db.resources.find({"is_active": True}).to_list(None)
        
        # Calculate statistics
        total_resources = len(resources)
        active_resources = len([r for r in resources if r.get("status") == "Active"])
        high_utilization_resources = len([r for r in resources if r.get("utilization", 0) >= 80])
        low_stock_resources = len([r for r in resources 
                                 if r.get("available_qty", 0) - r.get("assigned_qty", 0) <= 5])
        
        # Get purchase requests
        pending_prs = await db.purchase_requests.count_documents({
            "status": "Pending",
            "is_active": True
        })
        
        # Calculate total allocated value
        total_allocated_value = 0.0
        total_utilization = 0.0
        
        for resource in resources:
            assigned_qty = resource.get("assigned_qty", 0)
            unit_cost = resource.get("unit_cost", 0)
            total_allocated_value += assigned_qty * unit_cost
            total_utilization += resource.get("utilization", 0)
        
        average_utilization = total_utilization / total_resources if total_resources > 0 else 0.0
        
        summary = {
            "total_resources": total_resources,
            "active_resources": active_resources,
            "high_utilization_resources": high_utilization_resources,
            "low_stock_resources": low_stock_resources,
            "pending_purchase_requests": pending_prs,
            "total_allocated_value": round(total_allocated_value, 2),
            "average_utilization": round(average_utilization, 2)
        }
        
        return summary
    
    except Exception as e:
        logger.error(f"Error fetching resource summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching resource summary")

@router.get("/{resource_id}")
async def get_resource(resource_id: str):
    """Get specific resource by ID"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        resource = await db.resources.find_one({"id": resource_id, "is_active": True})
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return prepare_for_json(resource)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching resource")

@router.post("/")
async def create_resource(resource_data: ResourceCreate):
    """Create new resource"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Generate unique IDs
        resource_uuid = str(uuid.uuid4())
        resource_id = generate_resource_id()
        
        # Prepare resource data
        resource = {
            "id": resource_uuid,
            "resource_id": resource_id,
            **resource_data.dict(),
            "assigned_qty": 0.0,
            "utilization": 0.0,
            "status": "Active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",  # Will be replaced with actual user
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        resource = prepare_for_mongo(resource)
        
        # Insert into database
        await db.resources.insert_one(resource)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="Resource",
            resource_id=resource_uuid,
            details=f"Created resource {resource_id}: {resource_data.name}"
        )
        
        return prepare_for_json(resource)
    
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating resource")

@router.put("/{resource_id}")
async def update_resource(resource_id: str, resource_data: ResourceUpdate):
    """Update existing resource"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if resource exists
        existing_resource = await db.resources.find_one({"id": resource_id, "is_active": True})
        if not existing_resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in resource_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"  # Will be replaced with actual user
        }
        
        # Update in database
        await db.resources.update_one(
            {"id": resource_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Recalculate utilization if quantity changed
        if "available_qty" in update_data:
            await update_resource_utilization(resource_id, db)
        
        # Get updated resource
        updated_resource = await db.resources.find_one({"id": resource_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="Resource",
            resource_id=resource_id,
            details=f"Updated resource {existing_resource.get('resource_id', resource_id)}"
        )
        
        return prepare_for_json(updated_resource)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating resource")

# ==================== ALLOCATION ENDPOINTS ====================

@router.get("/{resource_id}/allocations")
async def get_resource_allocations(resource_id: str):
    """Get all allocations for a resource"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        allocations = await db.resource_allocations.find({
            "resource_id": resource_id,
            "is_active": True
        }).sort("allocation_date", -1).to_list(None)
        
        return [prepare_for_json(allocation) for allocation in allocations]
    
    except Exception as e:
        logger.error(f"Error fetching resource allocations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching resource allocations")

@router.post("/{resource_id}/allocate")
async def allocate_resource(resource_id: str, allocation_data: ResourceAllocationCreate):
    """Allocate resource to a project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Verify resource exists and has sufficient capacity
        resource = await db.resources.find_one({"id": resource_id, "is_active": True})
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        available_qty = resource.get("available_qty", 0)
        assigned_qty = resource.get("assigned_qty", 0)
        free_qty = available_qty - assigned_qty
        
        if allocation_data.allocated_qty > free_qty:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient resources. Available: {free_qty}, Requested: {allocation_data.allocated_qty}"
            )
        
        # Verify project exists
        project = await db.projects.find_one({"id": allocation_data.project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate unique allocation ID
        allocation_uuid = str(uuid.uuid4())
        allocation_id = generate_allocation_id()
        
        # Prepare allocation data
        allocation = {
            "id": allocation_uuid,
            "allocation_id": allocation_id,
            "resource_id": resource_id,
            **allocation_data.dict(),
            "allocated_by": "system",
            "allocation_date": datetime.now(timezone.utc),
            "status": "Active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        allocation = prepare_for_mongo(allocation)
        
        # Insert into database
        await db.resource_allocations.insert_one(allocation)
        
        # Update resource utilization
        await update_resource_utilization(resource_id, db)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="ALLOCATE",
            resource_type="ResourceAllocation",
            resource_id=allocation_uuid,
            details=f"Allocated {allocation_data.allocated_qty} units of {resource['name']} to project {project.get('project_id', allocation_data.project_id)}"
        )
        
        return prepare_for_json(allocation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error allocating resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Error allocating resource")

@router.put("/allocations/{allocation_id}")
async def update_allocation(allocation_id: str, allocation_data: ResourceAllocationUpdate):
    """Update existing resource allocation"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if allocation exists
        existing_allocation = await db.resource_allocations.find_one({
            "id": allocation_id,
            "is_active": True
        })
        if not existing_allocation:
            raise HTTPException(status_code=404, detail="Allocation not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in allocation_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        # Update in database
        await db.resource_allocations.update_one(
            {"id": allocation_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Update resource utilization
        resource_id = existing_allocation["resource_id"]
        await update_resource_utilization(resource_id, db)
        
        # Get updated allocation
        updated_allocation = await db.resource_allocations.find_one({"id": allocation_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="ResourceAllocation",
            resource_id=allocation_id,
            details=f"Updated allocation {existing_allocation.get('allocation_id', allocation_id)}"
        )
        
        return prepare_for_json(updated_allocation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating allocation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating allocation")

@router.delete("/allocations/{allocation_id}")
async def release_allocation(allocation_id: str):
    """Release (soft delete) resource allocation"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if allocation exists
        allocation = await db.resource_allocations.find_one({
            "id": allocation_id,
            "is_active": True
        })
        if not allocation:
            raise HTTPException(status_code=404, detail="Allocation not found")
        
        # Update status to Released and soft delete
        await db.resource_allocations.update_one(
            {"id": allocation_id},
            {"$set": prepare_for_mongo({
                "status": "Released",
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": "system"
            })}
        )
        
        # Update resource utilization
        resource_id = allocation["resource_id"]
        await update_resource_utilization(resource_id, db)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="RELEASE",
            resource_type="ResourceAllocation",
            resource_id=allocation_id,
            details=f"Released allocation {allocation.get('allocation_id', allocation_id)}"
        )
        
        return {"message": "Resource allocation released successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing allocation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error releasing allocation")

# ==================== PURCHASE REQUEST ENDPOINTS ====================

@router.get("/purchase-requests/")
async def get_purchase_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    limit: int = Query(50, description="Limit number of results"),
    skip: int = Query(0, description="Skip number of results")
):
    """Get list of purchase requests with optional filtering"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        query = {"is_active": True}
        
        if status:
            query["status"] = status
        if project_id:
            query["project_id"] = project_id
        
        purchase_requests = await db.purchase_requests.find(query)\
            .sort("created_at", -1)\
            .skip(skip)\
            .limit(limit)\
            .to_list(None)
        
        return [prepare_for_json(pr) for pr in purchase_requests]
    
    except Exception as e:
        logger.error(f"Error fetching purchase requests: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching purchase requests")

@router.post("/purchase-requests/")
async def create_purchase_request(pr_data: PurchaseRequestCreate):
    """Create new purchase request"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Generate unique PR ID
        pr_uuid = str(uuid.uuid4())
        pr_id = generate_pr_id()
        
        # Verify project exists if project_id provided
        if pr_data.project_id:
            project = await db.projects.find_one({"id": pr_data.project_id, "is_active": True})
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        
        # Prepare purchase request data
        purchase_request = {
            "id": pr_uuid,
            "pr_id": pr_id,
            **pr_data.dict(),
            "status": "Pending",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        purchase_request = prepare_for_mongo(purchase_request)
        
        # Insert into database
        await db.purchase_requests.insert_one(purchase_request)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="PurchaseRequest",
            resource_id=pr_uuid,
            details=f"Created purchase request {pr_id}: {pr_data.description}"
        )
        
        return prepare_for_json(purchase_request)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating purchase request: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating purchase request")

@router.put("/purchase-requests/{pr_id}")
async def update_purchase_request(pr_id: str, pr_data: PurchaseRequestUpdate):
    """Update existing purchase request"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if purchase request exists
        existing_pr = await db.purchase_requests.find_one({"id": pr_id, "is_active": True})
        if not existing_pr:
            raise HTTPException(status_code=404, detail="Purchase request not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in pr_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        # Update in database
        await db.purchase_requests.update_one(
            {"id": pr_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Get updated purchase request
        updated_pr = await db.purchase_requests.find_one({"id": pr_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="PurchaseRequest",
            resource_id=pr_id,
            details=f"Updated purchase request {existing_pr.get('pr_id', pr_id)}"
        )
        
        return prepare_for_json(updated_pr)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating purchase request: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating purchase request")