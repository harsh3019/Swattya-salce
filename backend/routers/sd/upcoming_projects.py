from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import os
import shutil
import logging

# Import from main server components without circular dependency
from motor.motor_asyncio import AsyncIOMotorClient

# Import these at module level to avoid circular dependency issues
try:
    from auth import get_current_user, User
    from database import db
    from utils import prepare_for_mongo, prepare_for_json, log_audit_trail
except ImportError:
    # Fallback imports if circular dependency occurs
    get_current_user = None
    User = None
    db = None
    prepare_for_mongo = None
    prepare_for_json = None
    log_audit_trail = None
from auth import get_current_user, User
from database import db
from utils import prepare_for_mongo, prepare_for_json, log_audit_trail
from models.sd.upcoming_project import (
    UpcomingProject, UpcomingProjectCreate, UpcomingProjectUpdate,
    ValidationResult, OrderStatus, ValidationStatus, GCSignoffStatus
)
from services.sd.validation_service import ValidationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sd/upcoming-projects", tags=["Services Delivery - Upcoming Projects"])

# Upload directories
UPLOAD_DIRS = {
    'boq': 'uploads/sd/boq/',
    'bom': 'uploads/sd/bom/'
}

# Ensure upload directories exist
for dir_path in UPLOAD_DIRS.values():
    os.makedirs(dir_path, exist_ok=True)

@router.get("/", response_model=List[UpcomingProject])
async def get_upcoming_projects(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get list of upcoming projects with optional filtering"""
    try:
        query = {"is_active": {"$ne": False}}  # Exclude soft-deleted records
        
        if status:
            query["order_status"] = status
        
        upcoming_projects = await db.upcoming_projects.find(query)\
            .sort("created_at", -1)\
            .skip(skip)\
            .limit(limit)\
            .to_list(None)
        
        return [prepare_for_json(project) for project in upcoming_projects]
    
    except Exception as e:
        logger.error(f"Error fetching upcoming projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching upcoming projects")

@router.get("/{project_id}", response_model=UpcomingProject)
async def get_upcoming_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific upcoming project by ID"""
    project = await db.upcoming_projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Upcoming project not found")
    
    return prepare_for_json(project)

@router.post("/", response_model=UpcomingProject)
async def create_upcoming_project(
    project_data: UpcomingProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new upcoming project from won opportunity"""
    try:
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        
        # Prepare project data
        project = {
            "id": project_id,
            **project_data.dict(),
            "opp_status": "Won",  # Always Won for SD entry
            "order_status": OrderStatus.PENDING,
            "validation_status": ValidationStatus.PENDING_GC_SIGNOFF,
            "gc_signoff_required": False,  # Will be determined during validation
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": current_user.id,
            "updated_by": current_user.id
        }
        
        # Convert for MongoDB storage
        project = prepare_for_mongo(project)
        
        # Insert into database
        await db.upcoming_projects.insert_one(project)
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CREATE",
            resource_type="UpcomingProject",
            resource_id=project_id,
            details=f"Created upcoming project for order {project_data.order_id}"
        )
        
        return prepare_for_json(project)
    
    except Exception as e:
        logger.error(f"Error creating upcoming project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating upcoming project")

@router.post("/{project_id}/upload-files")
async def upload_boq_bom_files(
    project_id: str,
    boq_file: UploadFile = File(...),
    bom_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload BOQ and BOM files for validation"""
    try:
        # Verify project exists
        project = await db.upcoming_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Upcoming project not found")
        
        # Validate file types
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        
        boq_ext = os.path.splitext(boq_file.filename)[1].lower()
        bom_ext = os.path.splitext(bom_file.filename)[1].lower()
        
        if boq_ext not in allowed_extensions or bom_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are allowed")
        
        # Generate unique filenames
        boq_filename = f"{project_id}_boq_{int(datetime.now().timestamp())}{boq_ext}"
        bom_filename = f"{project_id}_bom_{int(datetime.now().timestamp())}{bom_ext}"
        
        # Save files
        boq_path = os.path.join(UPLOAD_DIRS['boq'], boq_filename)
        bom_path = os.path.join(UPLOAD_DIRS['bom'], bom_filename)
        
        with open(boq_path, "wb") as buffer:
            shutil.copyfileobj(boq_file.file, buffer)
        
        with open(bom_path, "wb") as buffer:
            shutil.copyfileobj(bom_file.file, buffer)
        
        # Update project with file paths
        update_data = {
            "po_boq_file": boq_path,
            "bom_file": bom_path,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user.id
        }
        
        await db.upcoming_projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="UPDATE",
            resource_type="UpcomingProject",
            resource_id=project_id,
            details=f"Uploaded BOQ and BOM files: {boq_filename}, {bom_filename}"
        )
        
        return {
            "message": "Files uploaded successfully",
            "boq_file": boq_filename,
            "bom_file": bom_filename
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading files")

@router.post("/{project_id}/validate", response_model=ValidationResult)
async def validate_boq_bom(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Validate BOQ vs BOM files for discrepancies"""
    try:
        # Get project
        project = await db.upcoming_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Upcoming project not found")
        
        if not project.get('po_boq_file') or not project.get('bom_file'):
            raise HTTPException(status_code=400, detail="BOQ and BOM files must be uploaded first")
        
        # Parse files
        boq_items = ValidationService.parse_csv_file(project['po_boq_file'], "boq")
        bom_items = ValidationService.parse_csv_file(project['bom_file'], "bom")
        
        # Perform validation
        validation_result = ValidationService.validate_boq_bom_match(boq_items, bom_items)
        
        # Calculate setup cost
        setup_cost = ValidationService.calculate_setup_cost(boq_items)
        
        # Determine if GC signoff is required
        gc_signoff_required = ValidationService.requires_gc_signoff(setup_cost)
        
        # Update project with validation results
        update_data = {
            "validation_status": ValidationStatus.VALID if validation_result.is_valid else ValidationStatus.INVALID,
            "discrepancy_notes": validation_result.validation_summary,
            "setup_cost": setup_cost,
            "gc_signoff_required": gc_signoff_required,
            "validation_date": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user.id
        }
        
        await db.upcoming_projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="VALIDATE",
            resource_type="UpcomingProject",
            resource_id=project_id,
            details=f"BOQ/BOM validation completed. Result: {validation_result.validation_summary}"
        )
        
        return validation_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating BOQ/BOM: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during validation: {str(e)}")

@router.post("/{project_id}/convert-to-project")
async def convert_to_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Convert upcoming project to active project"""
    try:
        # Get upcoming project
        upcoming_project = await db.upcoming_projects.find_one({"id": project_id})
        if not upcoming_project:
            raise HTTPException(status_code=404, detail="Upcoming project not found")
        
        # Check if project can be converted
        if upcoming_project.get('order_status') == OrderStatus.CONVERTED:
            raise HTTPException(status_code=400, detail="Project already converted")
        
        if upcoming_project.get('validation_status') == ValidationStatus.INVALID:
            raise HTTPException(status_code=400, detail="Cannot convert project with validation errors")
        
        # Check GC signoff if required
        if upcoming_project.get('gc_signoff_required') and upcoming_project.get('gc_signoff_status') != GCSignoffStatus.APPROVED:
            raise HTTPException(status_code=400, detail="GC signoff required before conversion")
        
        # Generate project ID
        project_id_new = f"PRJ-{str(uuid.uuid4())[:8].upper()}"
        
        # Create project record (we'll implement this in Phase 2)
        project_data = {
            "project_id": project_id_new,
            "name": f"Project for {upcoming_project['customer_name']}",
            "order_id": upcoming_project['order_id'],
            "customer_name": upcoming_project['customer_name'],
            "setup_cost": upcoming_project.get('setup_cost', 0),
            "phase": "Planning",
            "status": "Active",
            "created_at": datetime.now(timezone.utc),
            "created_by": current_user.id
        }
        
        # For now, we'll just mark the upcoming project as converted
        await db.upcoming_projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo({
                "order_status": OrderStatus.CONVERTED,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": current_user.id
            })}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CONVERT",
            resource_type="UpcomingProject",
            resource_id=project_id,
            details=f"Converted upcoming project to active project {project_id_new}"
        )
        
        return {
            "message": "Project converted successfully",
            "project_id": project_id_new,
            "status": "Active"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error converting project")

@router.put("/{project_id}/reject")
async def reject_opportunity(
    project_id: str,
    rejection_reason: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Reject upcoming project/opportunity"""
    try:
        # Get project
        project = await db.upcoming_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Upcoming project not found")
        
        # Update status
        update_data = {
            "order_status": OrderStatus.REJECTED,
            "discrepancy_notes": f"REJECTED: {rejection_reason}",
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user.id
        }
        
        await db.upcoming_projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="REJECT",
            resource_type="UpcomingProject",
            resource_id=project_id,
            details=f"Rejected project. Reason: {rejection_reason}"
        )
        
        return {"message": "Project rejected successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error rejecting project")

@router.put("/{project_id}/gc-signoff")
async def gc_digital_signoff(
    project_id: str,
    approval_decision: str = Form(...),  # "approve" or "reject"
    approver_notes: str = Form(default=""),
    current_user: User = Depends(get_current_user)
):
    """Handle GC digital signoff"""
    try:
        # Validate decision
        if approval_decision not in ["approve", "reject"]:
            raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")
        
        # Get project
        project = await db.upcoming_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Upcoming project not found")
        
        if not project.get('gc_signoff_required'):
            raise HTTPException(status_code=400, detail="GC signoff not required for this project")
        
        # Update signoff status
        gc_status = GCSignoffStatus.APPROVED if approval_decision == "approve" else GCSignoffStatus.REJECTED
        
        update_data = {
            "gc_signoff_status": gc_status,
            "gc_signoff_timestamp": datetime.now(timezone.utc),
            "discrepancy_notes": f"{project.get('discrepancy_notes', '')} | GC Signoff: {approver_notes}".strip(" |"),
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user.id
        }
        
        await db.upcoming_projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="GC_SIGNOFF",
            resource_type="UpcomingProject",
            resource_id=project_id,
            details=f"GC signoff: {approval_decision.upper()}. Notes: {approver_notes}"
        )
        
        return {
            "message": f"GC signoff {approval_decision}d successfully",
            "status": gc_status,
            "timestamp": datetime.now(timezone.utc)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GC signoff: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing GC signoff")