from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class LOIStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"

class OrderStatus(str, Enum):
    PENDING = "Pending"
    CONVERTED = "Converted"
    REJECTED = "Rejected"

class ValidationStatus(str, Enum):
    VALID = "Valid"
    INVALID = "Invalid"
    PENDING_GC_SIGNOFF = "Pending GC Sign-off"

class GCSignoffStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class UpcomingProject(BaseModel):
    id: str = Field(..., description="Unique upcoming project ID")
    order_id: str = Field(..., description="Reference to Order Analysis ID")
    opp_id: str = Field(..., description="Reference to Opportunity ID")
    pot_id: str = Field(..., description="POT ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    po_boq_file: Optional[str] = Field(None, description="BOQ file path")
    bom_file: Optional[str] = Field(None, description="BOM file path")
    setup_cost: float = Field(default=0.0, description="Setup cost")
    loi_status: LOIStatus = Field(default=LOIStatus.PENDING, description="LOI status")
    opp_status: str = Field(default="Won", description="Opportunity status")
    order_status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING_GC_SIGNOFF, description="Validation status")
    discrepancy_notes: Optional[str] = Field(None, description="Validation discrepancy notes")
    loi_approved_on: Optional[datetime] = Field(None, description="LOI approval date")
    validation_date: Optional[datetime] = Field(None, description="Validation completion date")
    gc_signoff_required: bool = Field(default=False, description="Whether GC signoff is required")
    gc_signoff_status: GCSignoffStatus = Field(default=GCSignoffStatus.PENDING, description="GC signoff status")
    gc_signoff_timestamp: Optional[datetime] = Field(None, description="GC signoff timestamp")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")

class UpcomingProjectCreate(BaseModel):
    order_id: str = Field(..., description="Reference to Order Analysis ID")
    opp_id: str = Field(..., description="Reference to Opportunity ID")
    pot_id: str = Field(..., description="POT ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    setup_cost: float = Field(default=0.0, description="Setup cost")
    loi_status: LOIStatus = Field(default=LOIStatus.PENDING, description="LOI status")

class UpcomingProjectUpdate(BaseModel):
    po_boq_file: Optional[str] = Field(None, description="BOQ file path")
    bom_file: Optional[str] = Field(None, description="BOM file path")
    setup_cost: Optional[float] = Field(None, description="Setup cost")
    loi_status: Optional[LOIStatus] = Field(None, description="LOI status")
    order_status: Optional[OrderStatus] = Field(None, description="Order status")
    validation_status: Optional[ValidationStatus] = Field(None, description="Validation status")
    discrepancy_notes: Optional[str] = Field(None, description="Validation discrepancy notes")
    loi_approved_on: Optional[datetime] = Field(None, description="LOI approval date")
    gc_signoff_required: Optional[bool] = Field(None, description="Whether GC signoff is required")
    gc_signoff_status: Optional[GCSignoffStatus] = Field(None, description="GC signoff status")

class BOQItem(BaseModel):
    sku: str = Field(..., description="Stock Keeping Unit")
    item_name: str = Field(..., description="Item name")
    quantity: int = Field(..., ge=0, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")
    total_price: float = Field(..., ge=0, description="Total price")

class BOMItem(BaseModel):
    sku: str = Field(..., description="Stock Keeping Unit")
    item_name: str = Field(..., description="Item name")
    quantity: int = Field(..., ge=0, description="Quantity")
    unit_cost: float = Field(..., ge=0, description="Unit cost")
    total_cost: float = Field(..., ge=0, description="Total cost")

class ValidationDiscrepancy(BaseModel):
    type: str = Field(..., description="Discrepancy type")
    sku: str = Field(..., description="SKU with discrepancy")
    message: str = Field(..., description="Discrepancy message")
    boq_quantity: Optional[int] = Field(None, description="BOQ quantity")
    bom_quantity: Optional[int] = Field(None, description="BOM quantity")
    severity: str = Field(default="Medium", description="Severity level")

class ValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Overall validation result")
    discrepancies: List[ValidationDiscrepancy] = Field(default_factory=list, description="List of discrepancies")
    total_discrepancies: int = Field(..., description="Total number of discrepancies")
    validation_summary: str = Field(..., description="Validation summary")