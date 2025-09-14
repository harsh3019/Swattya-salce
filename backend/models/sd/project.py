from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class ProjectPhase(str, Enum):
    PLANNING = "Planning"
    EXECUTION = "Execution"
    CLOSURE = "Closure"

class ProjectStatus(str, Enum):
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class MilestoneStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DELAYED = "Delayed"

class TaskStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"

class Project(BaseModel):
    id: str = Field(..., description="Unique project ID")
    project_id: str = Field(..., description="Human-readable project ID (PRJ-XXXXXX)")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    order_id: Optional[str] = Field(None, description="Reference to Order Analysis ID")
    upcoming_project_id: Optional[str] = Field(None, description="Reference to source upcoming project")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    
    # Project management fields
    manager_id: Optional[str] = Field(None, description="Project Manager User ID")
    sponsor_id: Optional[str] = Field(None, description="Project Sponsor User ID")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    actual_end_date: Optional[date] = Field(None, description="Actual end date")
    
    # Status and phase
    phase: ProjectPhase = Field(default=ProjectPhase.PLANNING, description="Current project phase")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    
    # Financial
    budget: float = Field(default=0.0, description="Project budget")
    actual_cost: float = Field(default=0.0, description="Actual cost incurred")
    currency: str = Field(default="USD", description="Currency code")
    
    # Progress tracking
    overall_progress: float = Field(default=0.0, ge=0, le=100, description="Overall progress percentage")
    completion_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")
    
    # Additional fields
    priority: str = Field(default="Medium", description="Project priority (Low, Medium, High, Critical)")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    notes: Optional[str] = Field(None, description="Project notes")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    order_id: Optional[str] = Field(None, description="Reference to Order Analysis ID")
    upcoming_project_id: Optional[str] = Field(None, description="Reference to source upcoming project")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    manager_id: Optional[str] = Field(None, description="Project Manager User ID")
    sponsor_id: Optional[str] = Field(None, description="Project Sponsor User ID")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    budget: float = Field(default=0.0, description="Project budget")
    priority: str = Field(default="Medium", description="Project priority")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    notes: Optional[str] = Field(None, description="Project notes")

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    manager_id: Optional[str] = Field(None, description="Project Manager User ID")
    sponsor_id: Optional[str] = Field(None, description="Project Sponsor User ID")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    actual_end_date: Optional[date] = Field(None, description="Actual end date")
    phase: Optional[ProjectPhase] = Field(None, description="Current project phase")
    status: Optional[ProjectStatus] = Field(None, description="Project status")
    budget: Optional[float] = Field(None, description="Project budget")
    actual_cost: Optional[float] = Field(None, description="Actual cost incurred")
    priority: Optional[str] = Field(None, description="Project priority")
    tags: Optional[List[str]] = Field(None, description="Project tags")
    notes: Optional[str] = Field(None, description="Project notes")

class Milestone(BaseModel):
    id: str = Field(..., description="Unique milestone ID")
    project_id: str = Field(..., description="Project ID")
    milestone_name: str = Field(..., description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: date = Field(..., description="Milestone due date")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    owner_id: Optional[str] = Field(None, description="Milestone Owner User ID")
    status: MilestoneStatus = Field(default=MilestoneStatus.NOT_STARTED, description="Milestone status")
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    priority: str = Field(default="Medium", description="Milestone priority")
    dependencies: List[str] = Field(default_factory=list, description="Dependent milestone IDs")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")
    notes: Optional[str] = Field(None, description="Milestone notes")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class MilestoneCreate(BaseModel):
    milestone_name: str = Field(..., description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: date = Field(..., description="Milestone due date")
    owner_id: Optional[str] = Field(None, description="Milestone Owner User ID")
    priority: str = Field(default="Medium", description="Milestone priority")
    dependencies: List[str] = Field(default_factory=list, description="Dependent milestone IDs")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")
    notes: Optional[str] = Field(None, description="Milestone notes")

class MilestoneUpdate(BaseModel):
    milestone_name: Optional[str] = Field(None, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: Optional[date] = Field(None, description="Milestone due date")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    owner_id: Optional[str] = Field(None, description="Milestone Owner User ID")
    status: Optional[MilestoneStatus] = Field(None, description="Milestone status")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    priority: Optional[str] = Field(None, description="Milestone priority")
    dependencies: Optional[List[str]] = Field(None, description="Dependent milestone IDs")
    deliverables: Optional[List[str]] = Field(None, description="Expected deliverables")
    notes: Optional[str] = Field(None, description="Milestone notes")

class WBSTask(BaseModel):
    id: str = Field(..., description="Unique task ID")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Human-readable task ID (TSK-XXXXXX)")
    task_name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    assigned_to: Optional[str] = Field(None, description="Assigned User ID")
    start_date: Optional[date] = Field(None, description="Task start date")
    end_date: Optional[date] = Field(None, description="Task end date")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    actual_end_date: Optional[date] = Field(None, description="Actual end date")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Task status")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for hierarchical WBS")
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    estimated_hours: float = Field(default=0.0, description="Estimated hours")
    actual_hours: float = Field(default=0.0, description="Actual hours spent")
    priority: str = Field(default="Medium", description="Task priority")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    dependencies: List[str] = Field(default_factory=list, description="Dependent task IDs")
    milestone_id: Optional[str] = Field(None, description="Associated milestone ID")
    notes: Optional[str] = Field(None, description="Task notes")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class WBSTaskCreate(BaseModel):
    task_name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    assigned_to: Optional[str] = Field(None, description="Assigned User ID")
    start_date: Optional[date] = Field(None, description="Task start date")
    end_date: Optional[date] = Field(None, description="Task end date")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for hierarchical WBS")
    estimated_hours: float = Field(default=0.0, description="Estimated hours")
    priority: str = Field(default="Medium", description="Task priority")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    dependencies: List[str] = Field(default_factory=list, description="Dependent task IDs")
    milestone_id: Optional[str] = Field(None, description="Associated milestone ID")
    notes: Optional[str] = Field(None, description="Task notes")

class WBSTaskUpdate(BaseModel):
    task_name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    assigned_to: Optional[str] = Field(None, description="Assigned User ID")
    start_date: Optional[date] = Field(None, description="Task start date")
    end_date: Optional[date] = Field(None, description="Task end date")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    actual_end_date: Optional[date] = Field(None, description="Actual end date")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for hierarchical WBS")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours")
    actual_hours: Optional[float] = Field(None, description="Actual hours spent")
    priority: Optional[str] = Field(None, description="Task priority")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    dependencies: Optional[List[str]] = Field(None, description="Dependent task IDs")
    milestone_id: Optional[str] = Field(None, description="Associated milestone ID")
    notes: Optional[str] = Field(None, description="Task notes")

class ProjectSummary(BaseModel):
    """Summary model for project dashboard"""
    project: Project
    milestones_count: int
    completed_milestones: int
    overdue_milestones: int
    tasks_count: int
    completed_tasks: int
    overdue_tasks: int
    team_size: int
    budget_utilization: float
    schedule_variance: float