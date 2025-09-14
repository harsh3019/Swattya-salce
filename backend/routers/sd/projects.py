from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, date
import uuid
import logging

# Import models
from models.sd.project import (
    Project, ProjectCreate, ProjectUpdate, ProjectSummary,
    Milestone, MilestoneCreate, MilestoneUpdate,
    WBSTask, WBSTaskCreate, WBSTaskUpdate,
    ProjectPhase, ProjectStatus, MilestoneStatus, TaskStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sd/projects", tags=["Services Delivery - Projects"])

# Dependency to get database and utilities (imported when needed to avoid circular imports)
def get_db_and_utils():
    from server import db, prepare_for_mongo, prepare_for_json, log_audit_trail
    return db, prepare_for_mongo, prepare_for_json, log_audit_trail

def generate_project_id() -> str:
    """Generate unique project ID like PRJ-XXXXXXXX"""
    return f"PRJ-{str(uuid.uuid4())[:8].upper()}"

def generate_task_id() -> str:
    """Generate unique task ID like TSK-XXXXXXXX"""
    return f"TSK-{str(uuid.uuid4())[:8].upper()}"

async def calculate_project_progress(project_id: str, db) -> float:
    """Calculate overall project progress based on tasks and milestones"""
    try:
        # Get all active tasks for the project
        tasks = await db.wbs_tasks.find({"project_id": project_id, "is_active": True}).to_list(None)
        
        if not tasks:
            return 0.0
        
        # Calculate weighted average progress
        total_progress = sum(task.get("progress_percentage", 0) for task in tasks)
        return round(total_progress / len(tasks), 2)
    
    except Exception as e:
        logger.error(f"Error calculating project progress: {str(e)}")
        return 0.0

# ==================== PROJECT ENDPOINTS ====================

@router.get("/")
async def get_projects(
    status: Optional[str] = Query(None, description="Filter by project status"),
    phase: Optional[str] = Query(None, description="Filter by project phase"),
    manager_id: Optional[str] = Query(None, description="Filter by project manager"),
    limit: int = Query(50, description="Limit number of results"),
    skip: int = Query(0, description="Skip number of results")
):
    """Get list of projects with optional filtering"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        query = {"is_active": True}
        
        if status:
            query["status"] = status
        if phase:
            query["phase"] = phase
        if manager_id:
            query["manager_id"] = manager_id
        
        projects = await db.projects.find(query)\
            .sort("created_at", -1)\
            .skip(skip)\
            .limit(limit)\
            .to_list(None)
        
        return [prepare_for_json(project) for project in projects]
    
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching projects")

@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get specific project by ID"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        project = await db.projects.find_one({"id": project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return prepare_for_json(project)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching project")

@router.get("/{project_id}/summary")
async def get_project_summary(project_id: str):
    """Get comprehensive project summary with statistics"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Get project
        project = await db.projects.find_one({"id": project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get statistics
        milestones = await db.milestones.find({"project_id": project_id, "is_active": True}).to_list(None)
        tasks = await db.wbs_tasks.find({"project_id": project_id, "is_active": True}).to_list(None)
        
        # Calculate metrics
        milestones_count = len(milestones)
        completed_milestones = len([m for m in milestones if m.get("status") == "Completed"])
        overdue_milestones = len([m for m in milestones 
                                if m.get("due_date") and datetime.fromisoformat(m["due_date"]).date() < date.today() 
                                and m.get("status") != "Completed"])
        
        tasks_count = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "Completed"])
        overdue_tasks = len([t for t in tasks 
                           if t.get("end_date") and datetime.fromisoformat(t["end_date"]).date() < date.today() 
                           and t.get("status") != "Completed"])
        
        # Get unique team members
        team_members = set()
        if project.get("manager_id"):
            team_members.add(project["manager_id"])
        if project.get("sponsor_id"):
            team_members.add(project["sponsor_id"])
        for task in tasks:
            if task.get("assigned_to"):
                team_members.add(task["assigned_to"])
        
        team_size = len(team_members)
        
        # Calculate budget utilization
        budget = project.get("budget", 0)
        actual_cost = project.get("actual_cost", 0)
        budget_utilization = (actual_cost / budget * 100) if budget > 0 else 0
        
        # Calculate schedule variance (simplified)
        if project.get("end_date") and project.get("start_date"):
            planned_duration = (datetime.fromisoformat(project["end_date"]).date() - 
                              datetime.fromisoformat(project["start_date"]).date()).days
            current_duration = (date.today() - 
                              datetime.fromisoformat(project["start_date"]).date()).days
            schedule_variance = ((current_duration - planned_duration) / planned_duration * 100) if planned_duration > 0 else 0
        else:
            schedule_variance = 0
        
        summary = {
            "project": prepare_for_json(project),
            "milestones_count": milestones_count,
            "completed_milestones": completed_milestones,
            "overdue_milestones": overdue_milestones,
            "tasks_count": tasks_count,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "team_size": team_size,
            "budget_utilization": round(budget_utilization, 2),
            "schedule_variance": round(schedule_variance, 2)
        }
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching project summary")

@router.post("/")
async def create_project(project_data: ProjectCreate):
    """Create new project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Generate unique IDs
        project_uuid = str(uuid.uuid4())
        project_id = generate_project_id()
        
        # Prepare project data
        project = {
            "id": project_uuid,
            "project_id": project_id,
            **project_data.dict(),
            "phase": "Planning",
            "status": "Active",
            "overall_progress": 0.0,
            "completion_percentage": 0.0,
            "actual_cost": 0.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",  # Will be replaced with actual user
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        project = prepare_for_mongo(project)
        
        # Insert into database
        await db.projects.insert_one(project)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="Project",
            resource_id=project_uuid,
            details=f"Created project {project_id}: {project_data.name}"
        )
        
        return prepare_for_json(project)
    
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating project")

@router.put("/{project_id}")
async def update_project(project_id: str, project_data: ProjectUpdate):
    """Update existing project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if project exists
        existing_project = await db.projects.find_one({"id": project_id, "is_active": True})
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in project_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"  # Will be replaced with actual user
        }
        
        # Recalculate progress if needed
        if "status" in update_data or "phase" in update_data:
            progress = await calculate_project_progress(project_id, db)
            update_data["overall_progress"] = progress
        
        # Update in database
        await db.projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Get updated project
        updated_project = await db.projects.find_one({"id": project_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="Project",
            resource_id=project_id,
            details=f"Updated project {existing_project.get('project_id', project_id)}"
        )
        
        return prepare_for_json(updated_project)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating project")

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Soft delete project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if project exists
        project = await db.projects.find_one({"id": project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Soft delete
        await db.projects.update_one(
            {"id": project_id},
            {"$set": prepare_for_mongo({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": "system"
            })}
        )
        
        # Also soft delete associated milestones and tasks
        await db.milestones.update_many(
            {"project_id": project_id},
            {"$set": prepare_for_mongo({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc)
            })}
        )
        
        await db.wbs_tasks.update_many(
            {"project_id": project_id},
            {"$set": prepare_for_mongo({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc)
            })}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="DELETE",
            resource_type="Project",
            resource_id=project_id,
            details=f"Deleted project {project.get('project_id', project_id)}"
        )
        
        return {"message": "Project deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting project")

# ==================== MILESTONE ENDPOINTS ====================

@router.get("/{project_id}/milestones")
async def get_project_milestones(project_id: str):
    """Get all milestones for a project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        milestones = await db.milestones.find({
            "project_id": project_id,
            "is_active": True
        }).sort("due_date", 1).to_list(None)
        
        return [prepare_for_json(milestone) for milestone in milestones]
    
    except Exception as e:
        logger.error(f"Error fetching milestones: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching milestones")

@router.post("/{project_id}/milestones")
async def create_milestone(project_id: str, milestone_data: MilestoneCreate):
    """Create new milestone for a project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Verify project exists
        project = await db.projects.find_one({"id": project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate unique milestone ID
        milestone_id = str(uuid.uuid4())
        
        # Prepare milestone data
        milestone = {
            "id": milestone_id,
            "project_id": project_id,
            **milestone_data.dict(),
            "status": "Not Started",
            "progress_percentage": 0.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        milestone = prepare_for_mongo(milestone)
        
        # Insert into database
        await db.milestones.insert_one(milestone)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="Milestone",
            resource_id=milestone_id,
            details=f"Created milestone '{milestone_data.milestone_name}' for project {project.get('project_id', project_id)}"
        )
        
        return prepare_for_json(milestone)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating milestone: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating milestone")

@router.put("/{project_id}/milestones/{milestone_id}")
async def update_milestone(project_id: str, milestone_id: str, milestone_data: MilestoneUpdate):
    """Update existing milestone"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if milestone exists
        existing_milestone = await db.milestones.find_one({
            "id": milestone_id,
            "project_id": project_id,
            "is_active": True
        })
        if not existing_milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in milestone_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        # Update in database
        await db.milestones.update_one(
            {"id": milestone_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Get updated milestone
        updated_milestone = await db.milestones.find_one({"id": milestone_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="Milestone",
            resource_id=milestone_id,
            details=f"Updated milestone '{existing_milestone.get('milestone_name', milestone_id)}'"
        )
        
        return prepare_for_json(updated_milestone)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating milestone: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating milestone")

# ==================== WBS TASK ENDPOINTS ====================

@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: str):
    """Get all WBS tasks for a project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        tasks = await db.wbs_tasks.find({
            "project_id": project_id,
            "is_active": True
        }).sort("created_at", 1).to_list(None)
        
        return [prepare_for_json(task) for task in tasks]
    
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching tasks")

@router.post("/{project_id}/tasks")
async def create_task(project_id: str, task_data: WBSTaskCreate):
    """Create new WBS task for a project"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Verify project exists
        project = await db.projects.find_one({"id": project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate unique task IDs
        task_uuid = str(uuid.uuid4())
        task_id = generate_task_id()
        
        # Prepare task data
        task = {
            "id": task_uuid,
            "project_id": project_id,
            "task_id": task_id,
            **task_data.dict(),
            "status": "Not Started",
            "progress_percentage": 0.0,
            "actual_hours": 0.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        task = prepare_for_mongo(task)
        
        # Insert into database
        await db.wbs_tasks.insert_one(task)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="WBSTask",
            resource_id=task_uuid,
            details=f"Created task {task_id}: '{task_data.task_name}' for project {project.get('project_id', project_id)}"
        )
        
        return prepare_for_json(task)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating task")

@router.put("/{project_id}/tasks/{task_id}")
async def update_task(project_id: str, task_id: str, task_data: WBSTaskUpdate):
    """Update existing WBS task"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if task exists
        existing_task = await db.wbs_tasks.find_one({
            "id": task_id,
            "project_id": project_id,
            "is_active": True
        })
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in task_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        # Update in database
        await db.wbs_tasks.update_one(
            {"id": task_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Get updated task
        updated_task = await db.wbs_tasks.find_one({"id": task_id})
        
        # Recalculate project progress
        progress = await calculate_project_progress(project_id, db)
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"overall_progress": progress, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="WBSTask",
            resource_id=task_id,
            details=f"Updated task '{existing_task.get('task_name', task_id)}'"
        )
        
        return prepare_for_json(updated_task)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating task")