from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import os
import jwt
import bcrypt
import uuid
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'sawayatta-erp-super-secret-key-2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Sawayatta ERP API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================ MODELS ================

class BaseAuditModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

# User Management Models
class User(BaseAuditModel):
    username: str
    email: EmailStr
    password_hash: str
    role_id: Optional[str] = None
    department_id: Optional[str] = None
    designation_id: Optional[str] = None
    status: str = "active"
    last_login_at: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role_id: Optional[str] = None
    department_id: Optional[str] = None
    designation_id: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role_id: Optional[str] = None
    department_id: Optional[str] = None
    designation_id: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class Role(BaseAuditModel):
    name: str
    description: Optional[str] = None

class Permission(BaseAuditModel):
    key: str
    label: str
    module_id: str

class Module(BaseAuditModel):
    name: str
    description: Optional[str] = None

class Menu(BaseAuditModel):
    name: str
    module_id: str
    route_path: str
    icon: Optional[str] = None
    order_index: int = 0

class RolePermission(BaseAuditModel):
    role_id: str
    permission_id: str

class Department(BaseAuditModel):
    name: str

class Designation(BaseAuditModel):
    name: str

class ActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_name: str
    table_name: str
    action: str  # create/read/update/delete/login/logout
    status: str  # success/fail
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Sales Models
class Company(BaseAuditModel):
    company_name: str
    company_type: Optional[str] = None
    account_type: Optional[str] = None
    region: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    billing_record_id: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None
    
    # Domestic/International fields
    is_domestic: bool = True
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    vat_number: Optional[str] = None
    
    # Hierarchy
    is_child: bool = False
    parent_company_id: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Financials
    turnover_data: Optional[List[Dict]] = None  # [{year, revenue, currency}]
    profit_data: Optional[List[Dict]] = None
    
    # Additional
    company_profile: Optional[str] = None
    documents: Optional[List[Dict]] = None  # [{type, file_path, description}]

class Contact(BaseAuditModel):
    title_id: Optional[str] = None
    first_name: str
    last_name: str
    dob: Optional[datetime] = None
    company_id: Optional[str] = None
    designation_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phones: Optional[List[str]] = None
    fax: Optional[str] = None
    
    # Communication preferences
    dont_mail: bool = False
    dont_call: bool = False
    dont_email: bool = False
    
    # Addresses
    addresses: Optional[List[Dict]] = None  # [{type, address, country, state, city, zip}]

class ChannelPartner(BaseAuditModel):
    name: str
    type: Optional[str] = None
    region: Optional[str] = None
    website: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class Lead(BaseAuditModel):
    title: str
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    source: Optional[str] = None
    status: str = "New"  # New/Qualified/Disqualified
    owner_user_id: Optional[str] = None
    expected_value: Optional[float] = None
    currency: str = "USD"

class Opportunity(BaseAuditModel):
    name: str
    company_id: Optional[str] = None
    stage: str = "Qualification"  # Qualification/Proposal/Negotiation/Won/Lost
    amount: Optional[float] = None
    currency: str = "USD"
    close_date: Optional[datetime] = None
    owner_user_id: Optional[str] = None

# Auth Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# ================ UTILITIES ================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(data: dict) -> str:
    """Create JWT token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id, "is_active": True})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")

async def log_activity(module_name: str, table_name: str, action: str, status: str, 
                      user_id: Optional[str] = None, details: Optional[Dict] = None):
    """Log activity"""
    log = ActivityLog(
        module_name=module_name,
        table_name=table_name,
        action=action,
        status=status,
        user_id=user_id,
        details=details
    )
    await db.activity_logs.insert_one(log.dict())

def prepare_for_mongo(data: dict) -> dict:
    """Prepare data for MongoDB storage"""
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    if isinstance(data.get('updated_at'), datetime):
        data['updated_at'] = data['updated_at'].isoformat()
    if isinstance(data.get('last_login_at'), datetime):
        data['last_login_at'] = data['last_login_at'].isoformat()
    if isinstance(data.get('dob'), datetime):
        data['dob'] = data['dob'].isoformat()
    if isinstance(data.get('close_date'), datetime):
        data['close_date'] = data['close_date'].isoformat()
    return data

def parse_from_mongo(item: dict) -> dict:
    """Parse data from MongoDB"""
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    if isinstance(item.get('updated_at'), str):
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
    if isinstance(item.get('last_login_at'), str):
        item['last_login_at'] = datetime.fromisoformat(item['last_login_at'])
    if isinstance(item.get('dob'), str):
        item['dob'] = datetime.fromisoformat(item['dob'])
    if isinstance(item.get('close_date'), str):
        item['close_date'] = datetime.fromisoformat(item['close_date'])
    return item

# ================ AUTHENTICATION ENDPOINTS ================

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    try:
        # Find user
        user_data = await db.users.find_one({
            "$or": [
                {"username": request.username},
                {"email": request.username}
            ],
            "is_active": True
        })
        
        if not user_data or not verify_password(request.password, user_data["password_hash"]):
            await log_activity("auth", "users", "login", "fail", details={"username": request.username})
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        await db.users.update_one(
            {"id": user_data["id"]},
            {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create token
        token = create_jwt_token({"user_id": user_data["id"]})
        
        # Log successful login
        await log_activity("auth", "users", "login", "success", user_data["id"])
        
        # Remove password from response
        user_data.pop("password_hash", None)
        user_data = parse_from_mongo(user_data)
        
        return LoginResponse(access_token=token, user=user_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    user_dict = current_user.dict()
    user_dict.pop("password_hash", None)
    return user_dict

@api_router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint"""
    await log_activity("auth", "users", "logout", "success", current_user.id)
    return {"message": "Logged out successfully"}

# ================ USER MANAGEMENT ENDPOINTS ================

# Users CRUD
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    """Get all users"""
    users = await db.users.find({"is_active": True}).to_list(length=None)
    result = []
    for user in users:
        user.pop('_id', None)  # Remove MongoDB ObjectId
        parsed_user = parse_from_mongo(user)
        result.append(User(**parsed_user))
    return result

@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    """Create new user"""
    # Check if user exists
    existing = await db.users.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ],
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user = User(
        **user_data.dict(exclude={"password"}),
        password_hash=hash_password(user_data.password),
        created_by=current_user.id
    )
    
    user_dict = prepare_for_mongo(user.dict())
    await db.users.insert_one(user_dict)
    
    await log_activity("user_management", "users", "create", "success", current_user.id, {"user_id": user.id})
    
    return user

# Roles CRUD
@api_router.get("/roles", response_model=List[Role])
async def get_roles(current_user: User = Depends(get_current_user)):
    """Get all roles"""
    roles = await db.roles.find({"is_active": True}).to_list(length=None)
    return [Role(**parse_from_mongo(role)) for role in roles]

@api_router.post("/roles", response_model=Role)
async def create_role(role_data: Role, current_user: User = Depends(get_current_user)):
    """Create new role"""
    # Check if role exists
    existing = await db.roles.find_one({"name": role_data.name, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
    
    role = Role(**role_data.dict(), created_by=current_user.id)
    role_dict = prepare_for_mongo(role.dict())
    await db.roles.insert_one(role_dict)
    
    await log_activity("user_management", "roles", "create", "success", current_user.id, {"role_id": role.id})
    
    return role

# ================ SALES MODULE ENDPOINTS ================

# Companies CRUD
@api_router.get("/companies", response_model=List[Company])
async def get_companies(current_user: User = Depends(get_current_user)):
    """Get all companies"""
    companies = await db.companies.find({"is_active": True}).to_list(length=None)
    return [Company(**parse_from_mongo(company)) for company in companies]

@api_router.post("/companies", response_model=Company)
async def create_company(company_data: Company, current_user: User = Depends(get_current_user)):
    """Create new company"""
    company = Company(**company_data.dict(), created_by=current_user.id)
    company_dict = prepare_for_mongo(company.dict())
    await db.companies.insert_one(company_dict)
    
    await log_activity("sales", "companies", "create", "success", current_user.id, {"company_id": company.id})
    
    return company

@api_router.get("/companies/{company_id}", response_model=Company)
async def get_company(company_id: str, current_user: User = Depends(get_current_user)):
    """Get company by ID"""
    company = await db.companies.find_one({"id": company_id, "is_active": True})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return Company(**parse_from_mongo(company))

# Contacts CRUD
@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user)):
    """Get all contacts"""
    contacts = await db.contacts.find({"is_active": True}).to_list(length=None)
    return [Contact(**parse_from_mongo(contact)) for contact in contacts]

@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact_data: Contact, current_user: User = Depends(get_current_user)):
    """Create new contact"""
    contact = Contact(**contact_data.dict(), created_by=current_user.id)
    contact_dict = prepare_for_mongo(contact.dict())
    await db.contacts.insert_one(contact_dict)
    
    await log_activity("sales", "contacts", "create", "success", current_user.id, {"contact_id": contact.id})
    
    return contact

# Basic endpoints for other masters
@api_router.get("/departments", response_model=List[Department])
async def get_departments(current_user: User = Depends(get_current_user)):
    departments = await db.departments.find({"is_active": True}).to_list(length=None)
    return [Department(**parse_from_mongo(dept)) for dept in departments]

@api_router.get("/designations", response_model=List[Designation])
async def get_designations(current_user: User = Depends(get_current_user)):
    designations = await db.designations.find({"is_active": True}).to_list(length=None)
    return [Designation(**parse_from_mongo(desig)) for desig in designations]

@api_router.get("/activity-logs", response_model=List[ActivityLog])
async def get_activity_logs(current_user: User = Depends(get_current_user)):
    """Get activity logs"""
    logs = await db.activity_logs.find().sort("created_at", -1).limit(100).to_list(length=None)
    return [ActivityLog(**parse_from_mongo(log)) for log in logs]

# Include router
app.include_router(api_router)

# ================ STARTUP EVENT ================

@app.on_event("startup")
async def startup_event():
    """Initialize default data"""
    try:
        # Create default admin user if not exists
        admin_user = await db.users.find_one({"username": "admin", "is_active": True})
        if not admin_user:
            # Create default role
            admin_role = Role(
                name="Super Admin",
                description="Full system access",
                created_by="system"
            )
            role_dict = prepare_for_mongo(admin_role.dict())
            # Remove MongoDB ObjectId to avoid serialization issues
            role_dict.pop('_id', None)
            await db.roles.insert_one(role_dict)
            
            # Create default department
            default_dept = Department(name="IT", created_by="system")
            dept_dict = prepare_for_mongo(default_dept.dict())
            dept_dict.pop('_id', None)
            await db.departments.insert_one(dept_dict)
            
            # Create default designation
            default_desig = Designation(name="Administrator", created_by="system")
            desig_dict = prepare_for_mongo(default_desig.dict())
            desig_dict.pop('_id', None)
            await db.designations.insert_one(desig_dict)
            
            # Create default admin user
            admin = User(
                username="admin",
                email="admin@sawayatta.com",
                password_hash=hash_password("admin123"),
                role_id=admin_role.id,
                department_id=default_dept.id,
                designation_id=default_desig.id,
                created_by="system"
            )
            user_dict = prepare_for_mongo(admin.dict())
            user_dict.pop('_id', None)
            await db.users.insert_one(user_dict)
            
            logger.info("Default admin user created: admin/admin123")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()