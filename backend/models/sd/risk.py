from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class RiskCategory(str, Enum):
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    LEGAL = "legal"
    MARKET = "market"
    RESOURCE = "resource"
    SCHEDULE = "schedule"
    QUALITY = "quality"

class RiskProbability(str, Enum):
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"

class RiskImpact(str, Enum):
    NEGLIGIBLE = "Negligible"
    MINOR = "Minor"
    MODERATE = "Moderate"
    MAJOR = "Major"
    CATASTROPHIC = "Catastrophic"

class RiskStatus(str, Enum):
    IDENTIFIED = "Identified"
    ANALYZED = "Analyzed"
    PLANNED = "Planned"
    MITIGATED = "Mitigated" 
    CLOSED = "Closed"
    REALIZED = "Realized"

class MitigationStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"

class Risk(BaseModel):
    id: str = Field(..., description="Unique risk ID")
    risk_id: str = Field(..., description="Human-readable risk ID (RISK-XXXXXX)")
    project_id: str = Field(..., description="Associated project ID")
    
    # Risk identification
    title: str = Field(..., description="Risk title/name")
    description: str = Field(..., description="Detailed risk description")
    category: RiskCategory = Field(..., description="Risk category")
    
    # Risk assessment
    probability: RiskProbability = Field(..., description="Probability of occurrence")
    impact: RiskImpact = Field(..., description="Impact if realized")
    risk_score: float = Field(default=0.0, ge=0, le=25, description="Calculated risk score (1-25)")
    exposure_value: float = Field(default=0.0, ge=0, description="Financial exposure in currency")
    currency: str = Field(default="USD", description="Currency for financial values")
    
    # Risk management
    status: RiskStatus = Field(default=RiskStatus.IDENTIFIED, description="Current risk status")
    owner_id: Optional[str] = Field(None, description="Risk owner user ID")
    identified_by: Optional[str] = Field(None, description="User who identified the risk")
    identified_date: datetime = Field(default_factory=lambda: datetime.now(), description="Risk identification date")
    
    # Risk mitigation
    mitigation_strategy: Optional[str] = Field(None, description="Mitigation strategy description")
    mitigation_actions: List[str] = Field(default_factory=list, description="List of mitigation actions")
    mitigation_cost: float = Field(default=0.0, ge=0, description="Cost of mitigation")
    mitigation_timeline: Optional[str] = Field(None, description="Mitigation timeline")
    mitigation_status: MitigationStatus = Field(default=MitigationStatus.NOT_STARTED, description="Mitigation progress status")
    
    # Contingency planning
    contingency_plan: Optional[str] = Field(None, description="Contingency plan if risk is realized")
    contingency_cost: float = Field(default=0.0, ge=0, description="Cost of contingency plan")
    trigger_conditions: List[str] = Field(default_factory=list, description="Conditions that trigger contingency")
    
    # Monitoring and review
    review_frequency: Optional[str] = Field(None, description="How often to review (weekly, monthly, etc.)")
    last_reviewed: Optional[datetime] = Field(None, description="Last review date")
    next_review: Optional[date] = Field(None, description="Next scheduled review date")
    residual_probability: Optional[RiskProbability] = Field(None, description="Probability after mitigation")
    residual_impact: Optional[RiskImpact] = Field(None, description="Impact after mitigation")
    residual_score: float = Field(default=0.0, ge=0, le=25, description="Risk score after mitigation")
    
    # Additional attributes
    tags: List[str] = Field(default_factory=list, description="Risk tags for categorization")
    external_factors: List[str] = Field(default_factory=list, description="External factors affecting risk")
    stakeholders: List[str] = Field(default_factory=list, description="Stakeholders affected by risk")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class RiskCreate(BaseModel):
    project_id: str = Field(..., description="Associated project ID")
    title: str = Field(..., description="Risk title/name")
    description: str = Field(..., description="Detailed risk description")
    category: RiskCategory = Field(..., description="Risk category")
    probability: RiskProbability = Field(..., description="Probability of occurrence")
    impact: RiskImpact = Field(..., description="Impact if realized")
    exposure_value: float = Field(default=0.0, ge=0, description="Financial exposure")
    currency: str = Field(default="USD", description="Currency for financial values")
    owner_id: Optional[str] = Field(None, description="Risk owner user ID")
    mitigation_strategy: Optional[str] = Field(None, description="Mitigation strategy description")
    mitigation_actions: List[str] = Field(default_factory=list, description="List of mitigation actions")
    mitigation_cost: float = Field(default=0.0, ge=0, description="Cost of mitigation")
    mitigation_timeline: Optional[str] = Field(None, description="Mitigation timeline")
    contingency_plan: Optional[str] = Field(None, description="Contingency plan")
    contingency_cost: float = Field(default=0.0, ge=0, description="Cost of contingency plan")
    trigger_conditions: List[str] = Field(default_factory=list, description="Trigger conditions")
    review_frequency: Optional[str] = Field(None, description="Review frequency")
    next_review: Optional[date] = Field(None, description="Next review date")
    tags: List[str] = Field(default_factory=list, description="Risk tags")
    external_factors: List[str] = Field(default_factory=list, description="External factors")
    stakeholders: List[str] = Field(default_factory=list, description="Affected stakeholders")
    notes: Optional[str] = Field(None, description="Additional notes")

class RiskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Risk title/name")
    description: Optional[str] = Field(None, description="Detailed risk description")
    category: Optional[RiskCategory] = Field(None, description="Risk category")
    probability: Optional[RiskProbability] = Field(None, description="Probability of occurrence")
    impact: Optional[RiskImpact] = Field(None, description="Impact if realized")
    exposure_value: Optional[float] = Field(None, ge=0, description="Financial exposure")
    status: Optional[RiskStatus] = Field(None, description="Current risk status")
    owner_id: Optional[str] = Field(None, description="Risk owner user ID")
    mitigation_strategy: Optional[str] = Field(None, description="Mitigation strategy description")
    mitigation_actions: Optional[List[str]] = Field(None, description="List of mitigation actions")
    mitigation_cost: Optional[float] = Field(None, ge=0, description="Cost of mitigation")
    mitigation_timeline: Optional[str] = Field(None, description="Mitigation timeline")
    mitigation_status: Optional[MitigationStatus] = Field(None, description="Mitigation progress status")
    contingency_plan: Optional[str] = Field(None, description="Contingency plan")
    contingency_cost: Optional[float] = Field(None, ge=0, description="Cost of contingency plan")
    trigger_conditions: Optional[List[str]] = Field(None, description="Trigger conditions")
    review_frequency: Optional[str] = Field(None, description="Review frequency")
    next_review: Optional[date] = Field(None, description="Next review date")
    residual_probability: Optional[RiskProbability] = Field(None, description="Probability after mitigation")
    residual_impact: Optional[RiskImpact] = Field(None, description="Impact after mitigation")
    tags: Optional[List[str]] = Field(None, description="Risk tags")
    external_factors: Optional[List[str]] = Field(None, description="External factors")
    stakeholders: Optional[List[str]] = Field(None, description="Affected stakeholders")
    notes: Optional[str] = Field(None, description="Additional notes")

class RiskAssessment(BaseModel):
    """Model for risk assessment and scoring"""
    risk_id: str
    probability: RiskProbability
    impact: RiskImpact
    risk_score: float
    risk_level: str  # "Low", "Medium", "High", "Critical"
    assessment_date: datetime
    assessor_id: str
    comments: Optional[str] = None

class RiskMitigationAction(BaseModel):
    """Model for individual mitigation actions"""
    id: str = Field(..., description="Unique action ID")
    action_id: str = Field(..., description="Human-readable action ID (ACT-XXXXXX)")
    risk_id: str = Field(..., description="Associated risk ID")
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    due_date: Optional[date] = Field(None, description="Due date for action")
    status: MitigationStatus = Field(default=MitigationStatus.NOT_STARTED, description="Action status")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    cost: float = Field(default=0.0, ge=0, description="Action cost")
    effectiveness: Optional[str] = Field(None, description="Effectiveness rating")
    notes: Optional[str] = Field(None, description="Action notes")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    is_active: bool = Field(default=True, description="Active status")

class RiskMitigationActionCreate(BaseModel):
    risk_id: str = Field(..., description="Associated risk ID")
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    due_date: Optional[date] = Field(None, description="Due date for action")
    cost: float = Field(default=0.0, ge=0, description="Action cost")
    notes: Optional[str] = Field(None, description="Action notes")

class RiskMitigationActionUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Action title")
    description: Optional[str] = Field(None, description="Action description")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    due_date: Optional[date] = Field(None, description="Due date for action")
    status: Optional[MitigationStatus] = Field(None, description="Action status")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    cost: Optional[float] = Field(None, ge=0, description="Action cost")
    effectiveness: Optional[str] = Field(None, description="Effectiveness rating")
    notes: Optional[str] = Field(None, description="Action notes")

class RiskReview(BaseModel):
    """Model for risk review sessions"""
    id: str = Field(..., description="Unique review ID")
    review_id: str = Field(..., description="Human-readable review ID (REV-XXXXXX)")
    risk_id: str = Field(..., description="Associated risk ID")
    review_date: datetime = Field(default_factory=lambda: datetime.now(), description="Review date")
    reviewer_id: str = Field(..., description="Reviewer user ID")
    
    # Review assessment
    current_probability: RiskProbability = Field(..., description="Current probability assessment")
    current_impact: RiskImpact = Field(..., description="Current impact assessment")
    current_score: float = Field(..., ge=0, le=25, description="Current risk score")
    
    # Review outcomes
    status_change: Optional[RiskStatus] = Field(None, description="New status if changed")
    mitigation_effectiveness: Optional[str] = Field(None, description="Mitigation effectiveness rating")
    recommendations: List[str] = Field(default_factory=list, description="Review recommendations")
    action_items: List[str] = Field(default_factory=list, description="New action items")
    next_review_date: Optional[date] = Field(None, description="Next review date")
    
    # Review details
    review_notes: Optional[str] = Field(None, description="Review notes")
    attendees: List[str] = Field(default_factory=list, description="Review attendees")
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    is_active: bool = Field(default=True, description="Active status")

class RiskSummary(BaseModel):
    """Summary model for risk dashboard"""
    total_risks: int
    active_risks: int
    critical_risks: int  # Score >= 15
    high_risks: int      # Score >= 10
    medium_risks: int    # Score >= 5
    low_risks: int       # Score < 5
    overdue_reviews: int
    pending_mitigations: int
    total_exposure: float
    average_risk_score: float

# Risk scoring matrix
PROBABILITY_SCORES = {
    RiskProbability.VERY_LOW: 1,
    RiskProbability.LOW: 2,
    RiskProbability.MEDIUM: 3,
    RiskProbability.HIGH: 4,
    RiskProbability.VERY_HIGH: 5
}

IMPACT_SCORES = {
    RiskImpact.NEGLIGIBLE: 1,
    RiskImpact.MINOR: 2,
    RiskImpact.MODERATE: 3,
    RiskImpact.MAJOR: 4,
    RiskImpact.CATASTROPHIC: 5
}

def calculate_risk_score(probability: RiskProbability, impact: RiskImpact) -> float:
    """Calculate risk score based on probability and impact"""
    prob_score = PROBABILITY_SCORES.get(probability, 3)
    impact_score = IMPACT_SCORES.get(impact, 3)
    return float(prob_score * impact_score)

def get_risk_level(score: float) -> str:
    """Get risk level based on score"""
    if score >= 15:
        return "Critical"
    elif score >= 10:
        return "High"
    elif score >= 5:
        return "Medium"
    else:
        return "Low"