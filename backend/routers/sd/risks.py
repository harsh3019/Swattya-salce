from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, date
import uuid
import logging

# Import models
from models.sd.risk import (
    Risk, RiskCreate, RiskUpdate,
    RiskMitigationAction, RiskMitigationActionCreate, RiskMitigationActionUpdate,
    RiskReview, RiskAssessment, RiskSummary,
    RiskCategory, RiskProbability, RiskImpact, RiskStatus, MitigationStatus,
    calculate_risk_score, get_risk_level, PROBABILITY_SCORES, IMPACT_SCORES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sd/risks", tags=["Services Delivery - Risk Management"])

# Dependency to get database and utilities (imported when needed to avoid circular imports)
def get_db_and_utils():
    from server import db, prepare_for_mongo, prepare_for_json, log_audit_trail
    return db, prepare_for_mongo, prepare_for_json, log_audit_trail

def generate_risk_id() -> str:
    """Generate unique risk ID like RISK-XXXXXXXX"""
    return f"RISK-{str(uuid.uuid4())[:8].upper()}"

def generate_action_id() -> str:
    """Generate unique action ID like ACT-XXXXXXXX"""
    return f"ACT-{str(uuid.uuid4())[:8].upper()}"

def generate_review_id() -> str:
    """Generate unique review ID like REV-XXXXXXXX"""
    return f"REV-{str(uuid.uuid4())[:8].upper()}"

async def update_risk_score(risk_id: str, db):
    """Update risk score based on probability and impact"""
    try:
        risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not risk:
            return False
        
        # Calculate new score
        probability = risk.get("probability")
        impact = risk.get("impact") 
        risk_score = calculate_risk_score(probability, impact)
        
        # Calculate residual score if available
        residual_score = 0.0
        if risk.get("residual_probability") and risk.get("residual_impact"):
            residual_score = calculate_risk_score(
                risk.get("residual_probability"), 
                risk.get("residual_impact")
            )
        
        # Update risk with new scores
        await db.risks.update_one(
            {"id": risk_id},
            {"$set": {
                "risk_score": risk_score,
                "residual_score": residual_score,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating risk score: {str(e)}")
        return False

async def check_overdue_reviews(db):
    """Check for overdue risk reviews and create alerts"""
    try:
        today = date.today()
        overdue_risks = await db.risks.find({
            "next_review": {"$lt": today.isoformat()},
            "status": {"$nin": ["Closed", "Realized"]},
            "is_active": True
        }).to_list(None)
        
        # Log overdue reviews (could send notifications in production)
        for risk in overdue_risks:
            logger.warning(f"Risk {risk.get('risk_id', risk['id'])} review is overdue")
        
        return len(overdue_risks)
    
    except Exception as e:
        logger.error(f"Error checking overdue reviews: {str(e)}")
        return 0

# ==================== RISK MANAGEMENT ENDPOINTS ====================

@router.get("/")
async def get_risks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    category: Optional[str] = Query(None, description="Filter by risk category"),
    status: Optional[str] = Query(None, description="Filter by risk status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (Low/Medium/High/Critical)"),
    owner_id: Optional[str] = Query(None, description="Filter by risk owner"),
    overdue: bool = Query(False, description="Filter overdue reviews"),
    limit: int = Query(50, description="Limit number of results"),
    skip: int = Query(0, description="Skip number of results")
):
    """Get list of risks with optional filtering"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        query = {"is_active": True}
        
        # Apply filters
        if project_id:
            query["project_id"] = project_id
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        if owner_id:
            query["owner_id"] = owner_id
        
        # Risk level filter
        if risk_level:
            if risk_level == "Critical":
                query["risk_score"] = {"$gte": 15}
            elif risk_level == "High":
                query["risk_score"] = {"$gte": 10, "$lt": 15}
            elif risk_level == "Medium":
                query["risk_score"] = {"$gte": 5, "$lt": 10}
            elif risk_level == "Low":
                query["risk_score"] = {"$lt": 5}
        
        # Overdue review filter
        if overdue:
            today = date.today().isoformat()
            query["next_review"] = {"$lt": today}
            query["status"] = {"$nin": ["Closed", "Realized"]}
        
        risks = await db.risks.find(query)\
            .sort("risk_score", -1)\
            .skip(skip)\
            .limit(limit)\
            .to_list(None)
        
        return [prepare_for_json(risk) for risk in risks]
    
    except Exception as e:
        logger.error(f"Error fetching risks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching risks")

@router.get("/summary")
async def get_risks_summary():
    """Get comprehensive risk summary with statistics"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Get all active risks
        risks = await db.risks.find({"is_active": True}).to_list(None)
        
        # Calculate statistics
        total_risks = len(risks)
        active_risks = len([r for r in risks if r.get("status") not in ["Closed", "Realized"]])
        critical_risks = len([r for r in risks if r.get("risk_score", 0) >= 15])
        high_risks = len([r for r in risks if 10 <= r.get("risk_score", 0) < 15])
        medium_risks = len([r for r in risks if 5 <= r.get("risk_score", 0) < 10])
        low_risks = len([r for r in risks if r.get("risk_score", 0) < 5])
        
        # Check overdue reviews
        overdue_reviews = await check_overdue_reviews(db)
        
        # Count pending mitigations
        pending_mitigations = len([r for r in risks 
                                 if r.get("mitigation_status") in ["Not Started", "In Progress"]])
        
        # Calculate total exposure
        total_exposure = sum(r.get("exposure_value", 0) for r in risks 
                           if r.get("status") not in ["Closed", "Realized"])
        
        # Calculate average risk score
        active_risk_scores = [r.get("risk_score", 0) for r in risks 
                            if r.get("status") not in ["Closed", "Realized"]]
        average_risk_score = sum(active_risk_scores) / len(active_risk_scores) if active_risk_scores else 0.0
        
        summary = {
            "total_risks": total_risks,
            "active_risks": active_risks,
            "critical_risks": critical_risks,
            "high_risks": high_risks,
            "medium_risks": medium_risks,
            "low_risks": low_risks,
            "overdue_reviews": overdue_reviews,
            "pending_mitigations": pending_mitigations,
            "total_exposure": round(total_exposure, 2),
            "average_risk_score": round(average_risk_score, 2)
        }
        
        return summary
    
    except Exception as e:
        logger.error(f"Error fetching risk summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching risk summary")

@router.get("/{risk_id}")
async def get_risk(risk_id: str):
    """Get specific risk by ID"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        return prepare_for_json(risk)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching risk")

@router.post("/")
async def create_risk(risk_data: RiskCreate):
    """Create new risk"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Verify project exists
        project = await db.projects.find_one({"id": risk_data.project_id, "is_active": True})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate unique IDs
        risk_uuid = str(uuid.uuid4())
        risk_id = generate_risk_id()
        
        # Calculate risk score
        risk_score = calculate_risk_score(risk_data.probability, risk_data.impact)
        
        # Prepare risk data
        risk = {
            "id": risk_uuid,
            "risk_id": risk_id,
            **risk_data.dict(),
            "risk_score": risk_score,
            "status": "Identified",
            "mitigation_status": "Not Started",
            "identified_date": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",  # Will be replaced with actual user
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        risk = prepare_for_mongo(risk)
        
        # Insert into database
        await db.risks.insert_one(risk)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="Risk",
            resource_id=risk_uuid,
            details=f"Created risk {risk_id}: {risk_data.title}"
        )
        
        return prepare_for_json(risk)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating risk: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating risk")

@router.put("/{risk_id}")
async def update_risk(risk_id: str, risk_data: RiskUpdate):
    """Update existing risk"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if risk exists
        existing_risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not existing_risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in risk_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"  # Will be replaced with actual user
        }
        
        # Update in database
        await db.risks.update_one(
            {"id": risk_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Recalculate risk score if probability or impact changed
        if "probability" in update_data or "impact" in update_data:
            await update_risk_score(risk_id, db)
        
        # Get updated risk
        updated_risk = await db.risks.find_one({"id": risk_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="Risk",
            resource_id=risk_id,
            details=f"Updated risk {existing_risk.get('risk_id', risk_id)}"
        )
        
        return prepare_for_json(updated_risk)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating risk")

@router.delete("/{risk_id}")
async def delete_risk(risk_id: str):
    """Delete (soft delete) risk"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if risk exists
        risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        # Soft delete the risk
        await db.risks.update_one(
            {"id": risk_id},
            {"$set": prepare_for_mongo({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": "system"
            })}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="DELETE",
            resource_type="Risk",
            resource_id=risk_id,
            details=f"Deleted risk {risk.get('risk_id', risk_id)}"
        )
        
        return {"message": "Risk deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting risk: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting risk")

# ==================== RISK ASSESSMENT ENDPOINTS ====================

@router.post("/{risk_id}/assess")
async def assess_risk(risk_id: str, probability: RiskProbability, impact: RiskImpact, comments: Optional[str] = None):
    """Perform risk assessment and update risk score"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if risk exists
        risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        # Calculate new risk score
        risk_score = calculate_risk_score(probability, impact)
        risk_level = get_risk_level(risk_score)
        
        # Update risk with new assessment
        update_data = {
            "probability": probability,
            "impact": impact,
            "risk_score": risk_score,
            "status": "Analyzed",
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        await db.risks.update_one(
            {"id": risk_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Create assessment record
        assessment = {
            "id": str(uuid.uuid4()),
            "risk_id": risk_id,
            "probability": probability,
            "impact": impact,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "assessment_date": datetime.now(timezone.utc),
            "assessor_id": "system",
            "comments": comments
        }
        
        await db.risk_assessments.insert_one(prepare_for_mongo(assessment))
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="ASSESS",
            resource_type="Risk",
            resource_id=risk_id,
            details=f"Assessed risk {risk.get('risk_id', risk_id)}: {probability}/{impact} = {risk_score}"
        )
        
        return {
            "message": "Risk assessment completed",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "assessment": prepare_for_json(assessment)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing risk: {str(e)}")
        raise HTTPException(status_code=500, detail="Error assessing risk")

# ==================== MITIGATION ACTION ENDPOINTS ====================

@router.get("/{risk_id}/actions")
async def get_risk_actions(risk_id: str):
    """Get all mitigation actions for a risk"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        actions = await db.risk_mitigation_actions.find({
            "risk_id": risk_id,
            "is_active": True
        }).sort("created_at", -1).to_list(None)
        
        return [prepare_for_json(action) for action in actions]
    
    except Exception as e:
        logger.error(f"Error fetching risk actions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching risk actions")

@router.post("/{risk_id}/actions")
async def create_risk_action(risk_id: str, action_data: RiskMitigationActionCreate):
    """Create new mitigation action for a risk"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Verify risk exists
        risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        # Generate unique IDs
        action_uuid = str(uuid.uuid4())
        action_id = generate_action_id()
        
        # Prepare action data
        action = {
            "id": action_uuid,
            "action_id": action_id,
            "risk_id": risk_id,
            **action_data.dict(),
            "status": "Not Started",
            "progress": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "system",
            "updated_by": "system",
            "is_active": True
        }
        
        # Convert for MongoDB storage
        action = prepare_for_mongo(action)
        
        # Insert into database
        await db.risk_mitigation_actions.insert_one(action)
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="CREATE",
            resource_type="RiskMitigationAction",
            resource_id=action_uuid,
            details=f"Created mitigation action {action_id}: {action_data.title}"
        )
        
        return prepare_for_json(action)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating risk action: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating risk action")

@router.put("/actions/{action_id}")
async def update_risk_action(action_id: str, action_data: RiskMitigationActionUpdate):
    """Update existing mitigation action"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Check if action exists
        existing_action = await db.risk_mitigation_actions.find_one({
            "id": action_id,
            "is_active": True
        })
        if not existing_action:
            raise HTTPException(status_code=404, detail="Mitigation action not found")
        
        # Prepare update data
        update_data = {
            **{k: v for k, v in action_data.dict().items() if v is not None},
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        # Update in database
        await db.risk_mitigation_actions.update_one(
            {"id": action_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        
        # Get updated action
        updated_action = await db.risk_mitigation_actions.find_one({"id": action_id})
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="UPDATE",
            resource_type="RiskMitigationAction",
            resource_id=action_id,
            details=f"Updated mitigation action {existing_action.get('action_id', action_id)}"
        )
        
        return prepare_for_json(updated_action)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk action: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating risk action")

# ==================== RISK REVIEW ENDPOINTS ====================

@router.get("/{risk_id}/reviews")
async def get_risk_reviews(risk_id: str):
    """Get all reviews for a risk"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        reviews = await db.risk_reviews.find({
            "risk_id": risk_id,
            "is_active": True
        }).sort("review_date", -1).to_list(None)
        
        return [prepare_for_json(review) for review in reviews]
    
    except Exception as e:
        logger.error(f"Error fetching risk reviews: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching risk reviews")

@router.post("/{risk_id}/review")
async def create_risk_review(
    risk_id: str,
    current_probability: RiskProbability,
    current_impact: RiskImpact,
    status_change: Optional[RiskStatus] = None,
    mitigation_effectiveness: Optional[str] = None,
    recommendations: List[str] = [],
    action_items: List[str] = [],
    next_review_date: Optional[date] = None,
    review_notes: Optional[str] = None,
    attendees: List[str] = []
):
    """Create new risk review"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        # Verify risk exists
        risk = await db.risks.find_one({"id": risk_id, "is_active": True})
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        # Calculate current risk score
        current_score = calculate_risk_score(current_probability, current_impact)
        
        # Generate unique IDs
        review_uuid = str(uuid.uuid4())
        review_id = generate_review_id()
        
        # Prepare review data
        review = {
            "id": review_uuid,
            "review_id": review_id,
            "risk_id": risk_id,
            "review_date": datetime.now(timezone.utc),
            "reviewer_id": "system",
            "current_probability": current_probability,
            "current_impact": current_impact,
            "current_score": current_score,
            "status_change": status_change,
            "mitigation_effectiveness": mitigation_effectiveness,
            "recommendations": recommendations,
            "action_items": action_items,
            "next_review_date": next_review_date,
            "review_notes": review_notes,
            "attendees": attendees,
            "created_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        # Convert for MongoDB storage
        review = prepare_for_mongo(review)
        
        # Insert into database
        await db.risk_reviews.insert_one(review)
        
        # Update risk with review findings
        risk_updates = {
            "probability": current_probability,
            "impact": current_impact,
            "risk_score": current_score,
            "last_reviewed": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system"
        }
        
        if status_change:
            risk_updates["status"] = status_change
        if next_review_date:
            risk_updates["next_review"] = next_review_date
        
        await db.risks.update_one(
            {"id": risk_id},
            {"$set": prepare_for_mongo(risk_updates)}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id="system",
            action="REVIEW",
            resource_type="Risk",
            resource_id=risk_id,
            details=f"Reviewed risk {risk.get('risk_id', risk_id)}: Score {current_score}"
        )
        
        return prepare_for_json(review)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating risk review: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating risk review")

# ==================== UTILITY ENDPOINTS ====================

@router.get("/matrix/scoring")
async def get_risk_scoring_matrix():
    """Get risk scoring matrix for reference"""
    return {
        "probability_scores": PROBABILITY_SCORES,
        "impact_scores": IMPACT_SCORES,
        "risk_levels": {
            "Low": "1-4",
            "Medium": "5-9", 
            "High": "10-14",
            "Critical": "15-25"
        },
        "scoring_formula": "Risk Score = Probability Score × Impact Score"
    }

@router.get("/dashboard/overdue")
async def get_overdue_risks():
    """Get risks with overdue reviews"""
    try:
        # Import here to avoid circular dependency
        db, prepare_for_mongo, prepare_for_json, log_audit_trail = get_db_and_utils()
        
        today = date.today().isoformat()
        overdue_risks = await db.risks.find({
            "next_review": {"$lt": today},
            "status": {"$nin": ["Closed", "Realized"]},
            "is_active": True
        }).sort("next_review", 1).to_list(None)
        
        return [prepare_for_json(risk) for risk in overdue_risks]
    
    except Exception as e:
        logger.error(f"Error fetching overdue risks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching overdue risks")