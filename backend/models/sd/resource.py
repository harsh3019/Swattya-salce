from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class ResourceType(str, Enum):
    CLOUD = "cloud"
    SERVER = "server"
    LICENSE = "license"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"

class ResourceStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    MAINTENANCE = "Maintenance"
    RETIRED = "Retired"

class AllocationStatus(str, Enum):
    ACTIVE = "Active"
    RELEASED = "Released"
    EXPIRED = "Expired"

class PurchaseRequestStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ORDERED = "Ordered"
    RECEIVED = "Received"
    CANCELLED = "Cancelled"

class Resource(BaseModel):
    id: str = Field(..., description="Unique resource ID")
    resource_id: str = Field(..., description="Human-readable resource ID (RES-XXXXXX)")
    type: ResourceType = Field(..., description="Resource type")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    
    # Capacity and utilization
    available_qty: float = Field(..., ge=0, description="Total available quantity")
    assigned_qty: float = Field(default=0.0, ge=0, description="Currently assigned quantity")
    utilization: float = Field(default=0.0, ge=0, le=100, description="Utilization percentage")
    
    # Costing
    unit_cost: float = Field(default=0.0, ge=0, description="Cost per unit")
    currency: str = Field(default="USD", description="Currency code")
    
    # Resource details
    specifications: Optional[dict] = Field(None, description="Technical specifications")
    vendor: Optional[str] = Field(None, description="Vendor/supplier name")
    model: Optional[str] = Field(None, description="Model/version")
    location: Optional[str] = Field(None, description="Physical/logical location")
    
    # Lifecycle
    procurement_date: Optional[date] = Field(None, description="Procurement date")
    warranty_expiry: Optional[date] = Field(None, description="Warranty expiry date")
    maintenance_schedule: Optional[str] = Field(None, description="Maintenance schedule")
    
    # Status and management
    status: ResourceStatus = Field(default=ResourceStatus.ACTIVE, description="Resource status")
    owner_id: Optional[str] = Field(None, description="Resource owner user ID")
    tags: List[str] = Field(default_factory=list, description="Resource tags")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class ResourceCreate(BaseModel):
    type: ResourceType = Field(..., description="Resource type")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    available_qty: float = Field(..., ge=0, description="Total available quantity")
    unit_cost: float = Field(default=0.0, ge=0, description="Cost per unit")
    currency: str = Field(default="USD", description="Currency code")
    specifications: Optional[dict] = Field(None, description="Technical specifications")
    vendor: Optional[str] = Field(None, description="Vendor/supplier name")
    model: Optional[str] = Field(None, description="Model/version")
    location: Optional[str] = Field(None, description="Physical/logical location")
    procurement_date: Optional[date] = Field(None, description="Procurement date")
    warranty_expiry: Optional[date] = Field(None, description="Warranty expiry date")
    maintenance_schedule: Optional[str] = Field(None, description="Maintenance schedule")
    owner_id: Optional[str] = Field(None, description="Resource owner user ID")
    tags: List[str] = Field(default_factory=list, description="Resource tags")
    notes: Optional[str] = Field(None, description="Additional notes")

class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    available_qty: Optional[float] = Field(None, ge=0, description="Total available quantity")
    unit_cost: Optional[float] = Field(None, ge=0, description="Cost per unit")
    currency: Optional[str] = Field(None, description="Currency code")
    specifications: Optional[dict] = Field(None, description="Technical specifications")
    vendor: Optional[str] = Field(None, description="Vendor/supplier name")
    model: Optional[str] = Field(None, description="Model/version")
    location: Optional[str] = Field(None, description="Physical/logical location")
    procurement_date: Optional[date] = Field(None, description="Procurement date")
    warranty_expiry: Optional[date] = Field(None, description="Warranty expiry date")
    maintenance_schedule: Optional[str] = Field(None, description="Maintenance schedule")
    status: Optional[ResourceStatus] = Field(None, description="Resource status")
    owner_id: Optional[str] = Field(None, description="Resource owner user ID")
    tags: Optional[List[str]] = Field(None, description="Resource tags")
    notes: Optional[str] = Field(None, description="Additional notes")

class ResourceAllocation(BaseModel):
    id: str = Field(..., description="Unique allocation ID")
    allocation_id: str = Field(..., description="Human-readable allocation ID (ALL-XXXXXX)")
    resource_id: str = Field(..., description="Resource ID")
    project_id: str = Field(..., description="Project ID")
    allocated_qty: float = Field(..., gt=0, description="Allocated quantity")
    allocated_by: Optional[str] = Field(None, description="Allocator user ID")
    allocation_date: datetime = Field(default_factory=lambda: datetime.now(), description="Allocation date")
    start_date: Optional[date] = Field(None, description="Allocation start date")
    end_date: Optional[date] = Field(None, description="Allocation end date")
    status: AllocationStatus = Field(default=AllocationStatus.ACTIVE, description="Allocation status")
    purpose: Optional[str] = Field(None, description="Allocation purpose/reason")
    notes: Optional[str] = Field(None, description="Allocation notes")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class ResourceAllocationCreate(BaseModel):
    resource_id: str = Field(..., description="Resource ID")
    project_id: str = Field(..., description="Project ID")
    allocated_qty: float = Field(..., gt=0, description="Allocated quantity")
    start_date: Optional[date] = Field(None, description="Allocation start date")
    end_date: Optional[date] = Field(None, description="Allocation end date")
    purpose: Optional[str] = Field(None, description="Allocation purpose/reason")
    notes: Optional[str] = Field(None, description="Allocation notes")

class ResourceAllocationUpdate(BaseModel):
    allocated_qty: Optional[float] = Field(None, gt=0, description="Allocated quantity")
    start_date: Optional[date] = Field(None, description="Allocation start date")
    end_date: Optional[date] = Field(None, description="Allocation end date")
    status: Optional[AllocationStatus] = Field(None, description="Allocation status")
    purpose: Optional[str] = Field(None, description="Allocation purpose/reason")
    notes: Optional[str] = Field(None, description="Allocation notes")

class PurchaseRequest(BaseModel):
    id: str = Field(..., description="Unique purchase request ID")
    pr_id: str = Field(..., description="Human-readable PR ID (PR-XXXXXX)")
    project_id: Optional[str] = Field(None, description="Project ID (if project-specific)")
    resource_id: Optional[str] = Field(None, description="Existing resource ID (for replenishment)")
    
    # Request details
    sku: str = Field(..., description="Stock Keeping Unit")
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., gt=0, description="Requested quantity")
    estimated_cost: float = Field(default=0.0, ge=0, description="Estimated total cost")
    unit_cost: float = Field(default=0.0, ge=0, description="Estimated unit cost")
    currency: str = Field(default="USD", description="Currency code")
    
    # Business justification
    justification: str = Field(..., description="Business justification")
    priority: str = Field(default="Medium", description="Request priority")
    required_by: Optional[date] = Field(None, description="Required by date")
    
    # Workflow management
    spoc_id: Optional[str] = Field(None, description="Single Point of Contact User ID")
    status: PurchaseRequestStatus = Field(default=PurchaseRequestStatus.PENDING, description="Request status")
    approval_date: Optional[datetime] = Field(None, description="Approval date")
    approver_id: Optional[str] = Field(None, description="Approver user ID")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    
    # Procurement details
    vendor: Optional[str] = Field(None, description="Selected vendor")
    po_number: Optional[str] = Field(None, description="Purchase order number")
    order_date: Optional[date] = Field(None, description="Order placement date")
    expected_delivery: Optional[date] = Field(None, description="Expected delivery date")
    actual_delivery: Optional[date] = Field(None, description="Actual delivery date")
    actual_cost: Optional[float] = Field(None, description="Actual cost")
    
    # Additional fields
    specifications: Optional[dict] = Field(None, description="Technical specifications")
    tags: List[str] = Field(default_factory=list, description="Request tags")
    comments: Optional[str] = Field(None, description="Additional comments")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class PurchaseRequestCreate(BaseModel):
    project_id: Optional[str] = Field(None, description="Project ID (if project-specific)")
    resource_id: Optional[str] = Field(None, description="Existing resource ID (for replenishment)")
    sku: str = Field(..., description="Stock Keeping Unit")
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., gt=0, description="Requested quantity")
    estimated_cost: float = Field(default=0.0, ge=0, description="Estimated total cost")
    unit_cost: float = Field(default=0.0, ge=0, description="Estimated unit cost")
    currency: str = Field(default="USD", description="Currency code")
    justification: str = Field(..., description="Business justification")
    priority: str = Field(default="Medium", description="Request priority")
    required_by: Optional[date] = Field(None, description="Required by date")
    spoc_id: Optional[str] = Field(None, description="Single Point of Contact User ID")
    specifications: Optional[dict] = Field(None, description="Technical specifications")
    tags: List[str] = Field(default_factory=list, description="Request tags")
    comments: Optional[str] = Field(None, description="Additional comments")

class PurchaseRequestUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0, description="Requested quantity")
    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated total cost")
    unit_cost: Optional[float] = Field(None, ge=0, description="Estimated unit cost")
    justification: Optional[str] = Field(None, description="Business justification")
    priority: Optional[str] = Field(None, description="Request priority")
    required_by: Optional[date] = Field(None, description="Required by date")
    spoc_id: Optional[str] = Field(None, description="Single Point of Contact User ID")
    status: Optional[PurchaseRequestStatus] = Field(None, description="Request status")
    approval_date: Optional[datetime] = Field(None, description="Approval date")
    approver_id: Optional[str] = Field(None, description="Approver user ID")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    vendor: Optional[str] = Field(None, description="Selected vendor")
    po_number: Optional[str] = Field(None, description="Purchase order number")
    order_date: Optional[date] = Field(None, description="Order placement date")
    expected_delivery: Optional[date] = Field(None, description="Expected delivery date")
    actual_delivery: Optional[date] = Field(None, description="Actual delivery date")
    actual_cost: Optional[float] = Field(None, description="Actual cost")
    specifications: Optional[dict] = Field(None, description="Technical specifications")
    tags: Optional[List[str]] = Field(None, description="Request tags")
    comments: Optional[str] = Field(None, description="Additional comments")

class ResourceUtilizationAlert(BaseModel):
    """Model for resource utilization alerts"""
    resource_id: str
    resource_name: str
    utilization: float
    threshold: float
    severity: str  # "Warning", "Critical"
    message: str
    created_at: datetime

class ResourceSummary(BaseModel):
    """Summary model for resource dashboard"""
    total_resources: int
    active_resources: int
    high_utilization_resources: int  # ≥80%
    low_stock_resources: int
    pending_purchase_requests: int
    total_allocated_value: float
    average_utilization: float