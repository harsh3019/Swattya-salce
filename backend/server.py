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
    code: Optional[str] = None
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
        
        # Remove password and MongoDB ObjectId from response
        user_data.pop("password_hash", None)
        user_data.pop("_id", None)
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
    user_dict = user_data.dict(exclude={"password"})
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_by'] = current_user.id
    user = User(**user_dict)
    
    user_dict = prepare_for_mongo(user.dict())
    user_dict.pop('_id', None)
    await db.users.insert_one(user_dict)
    
    await log_activity("user_management", "users", "create", "success", current_user.id, {"user_id": user.id})
    
    return user

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserUpdate, current_user: User = Depends(get_current_user)):
    """Update user"""
    existing = await db.users.find_one({"id": user_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_dict = user_data.dict(exclude_unset=True)
    user_dict['updated_by'] = current_user.id
    user_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"id": user_id}, {"$set": user_dict})
    
    updated_user = await db.users.find_one({"id": user_id})
    updated_user.pop('_id', None)
    updated_user.pop('password_hash', None)  # Don't return password
    
    await log_activity("user_management", "users", "update", "success", current_user.id, {"user_id": user_id})
    return User(**parse_from_mongo(updated_user))

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete user"""
    existing = await db.users.find_one({"id": user_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    await db.users.update_one(
        {"id": user_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "users", "delete", "success", current_user.id, {"user_id": user_id})
    return {"message": "User deleted successfully"}

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
    
    # Fix the duplicate created_by issue
    role_dict = role_data.dict()
    role_dict['created_by'] = current_user.id
    role = Role(**role_dict)
    role_dict = prepare_for_mongo(role.dict())
    role_dict.pop('_id', None)
    await db.roles.insert_one(role_dict)
    
    await log_activity("user_management", "roles", "create", "success", current_user.id, {"role_id": role.id})
    
    return role

@api_router.put("/roles/{role_id}", response_model=Role)
async def update_role(role_id: str, role_data: Role, current_user: User = Depends(get_current_user)):
    """Update role"""
    existing = await db.roles.find_one({"id": role_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    role_dict = role_data.dict()
    role_dict['updated_by'] = current_user.id
    role_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    role_dict.pop('_id', None)
    
    await db.roles.update_one({"id": role_id}, {"$set": role_dict})
    
    updated_role = await db.roles.find_one({"id": role_id})
    updated_role.pop('_id', None)
    
    await log_activity("user_management", "roles", "update", "success", current_user.id, {"role_id": role_id})
    return Role(**parse_from_mongo(updated_role))

@api_router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete role"""
    existing = await db.roles.find_one({"id": role_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    await db.roles.update_one(
        {"id": role_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "roles", "delete", "success", current_user.id, {"role_id": role_id})
    return {"message": "Role deleted successfully"}

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
    company_dict = company_data.dict()
    company_dict['created_by'] = current_user.id
    company = Company(**company_dict)
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
    contact_dict = contact_data.dict()
    contact_dict['created_by'] = current_user.id
    contact = Contact(**contact_dict)
    contact_dict = prepare_for_mongo(contact.dict())
    await db.contacts.insert_one(contact_dict)
    
    await log_activity("sales", "contacts", "create", "success", current_user.id, {"contact_id": contact.id})
    
    return contact

# ================ COMPLETE USER MANAGEMENT ENDPOINTS ================

# Departments CRUD
@api_router.get("/departments", response_model=List[Department])
async def get_departments(current_user: User = Depends(get_current_user)):
    departments = await db.departments.find({"is_active": True}).to_list(length=None)
    result = []
    for dept in departments:
        dept.pop('_id', None)
        result.append(Department(**parse_from_mongo(dept)))
    return result

@api_router.post("/departments", response_model=Department)
async def create_department(dept_data: Department, current_user: User = Depends(get_current_user)):
    """Create new department"""
    existing = await db.departments.find_one({"name": dept_data.name, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")
    
    dept_dict = dept_data.dict()
    dept_dict['created_by'] = current_user.id
    department = Department(**dept_dict)
    dept_dict = prepare_for_mongo(department.dict())
    dept_dict.pop('_id', None)
    await db.departments.insert_one(dept_dict)
    
    await log_activity("user_management", "departments", "create", "success", current_user.id, {"department_id": department.id})
    return department

@api_router.put("/departments/{dept_id}", response_model=Department)
async def update_department(dept_id: str, dept_data: Department, current_user: User = Depends(get_current_user)):
    """Update department"""
    existing = await db.departments.find_one({"id": dept_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")
    
    dept_dict = dept_data.dict()
    dept_dict['updated_by'] = current_user.id
    dept_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    dept_dict.pop('_id', None)
    
    await db.departments.update_one({"id": dept_id}, {"$set": dept_dict})
    
    updated_dept = await db.departments.find_one({"id": dept_id})
    if not updated_dept:
        raise HTTPException(status_code=404, detail="Department not found after update")
    updated_dept.pop('_id', None)
    
    await log_activity("user_management", "departments", "update", "success", current_user.id, {"department_id": dept_id})
    return Department(**parse_from_mongo(updated_dept))

@api_router.delete("/departments/{dept_id}")
async def delete_department(dept_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete department"""
    existing = await db.departments.find_one({"id": dept_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")
    
    await db.departments.update_one(
        {"id": dept_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "departments", "delete", "success", current_user.id, {"department_id": dept_id})
    return {"message": "Department deleted successfully"}

# Designations CRUD
@api_router.get("/designations", response_model=List[Designation])
async def get_designations(current_user: User = Depends(get_current_user)):
    designations = await db.designations.find({"is_active": True}).to_list(length=None)
    result = []
    for desig in designations:
        desig.pop('_id', None)
        result.append(Designation(**parse_from_mongo(desig)))
    return result

@api_router.post("/designations", response_model=Designation)
async def create_designation(desig_data: Designation, current_user: User = Depends(get_current_user)):
    """Create new designation"""
    existing = await db.designations.find_one({"name": desig_data.name, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Designation already exists")
    
    desig_dict = desig_data.dict()
    desig_dict['created_by'] = current_user.id
    designation = Designation(**desig_dict)
    desig_dict = prepare_for_mongo(designation.dict())
    desig_dict.pop('_id', None)
    await db.designations.insert_one(desig_dict)
    
    await log_activity("user_management", "designations", "create", "success", current_user.id, {"designation_id": designation.id})
    return designation

@api_router.put("/designations/{desig_id}", response_model=Designation)
async def update_designation(desig_id: str, desig_data: Designation, current_user: User = Depends(get_current_user)):
    """Update designation"""
    existing = await db.designations.find_one({"id": desig_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Designation not found")
    
    desig_dict = desig_data.dict()
    desig_dict['updated_by'] = current_user.id
    desig_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    desig_dict.pop('_id', None)
    
    await db.designations.update_one({"id": desig_id}, {"$set": desig_dict})
    
    updated_desig = await db.designations.find_one({"id": desig_id})
    updated_desig.pop('_id', None)
    
    await log_activity("user_management", "designations", "update", "success", current_user.id, {"designation_id": desig_id})
    return Designation(**parse_from_mongo(updated_desig))

@api_router.delete("/designations/{desig_id}")
async def delete_designation(desig_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete designation"""
    existing = await db.designations.find_one({"id": desig_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Designation not found")
    
    await db.designations.update_one(
        {"id": desig_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "designations", "delete", "success", current_user.id, {"designation_id": desig_id})
    return {"message": "Designation deleted successfully"}

# Permissions CRUD
@api_router.get("/permissions", response_model=List[Permission])
async def get_permissions(current_user: User = Depends(get_current_user)):
    permissions = await db.permissions.find({"is_active": True}).to_list(length=None)
    result = []
    for perm in permissions:
        perm.pop('_id', None)
        result.append(Permission(**parse_from_mongo(perm)))
    return result

@api_router.post("/permissions", response_model=Permission)
async def create_permission(perm_data: Permission, current_user: User = Depends(get_current_user)):
    """Create new permission"""
    existing = await db.permissions.find_one({"key": perm_data.key, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")
    
    perm_dict = perm_data.dict()
    perm_dict['created_by'] = current_user.id
    permission = Permission(**perm_dict)
    perm_dict = prepare_for_mongo(permission.dict())
    perm_dict.pop('_id', None)
    await db.permissions.insert_one(perm_dict)
    
    await log_activity("user_management", "permissions", "create", "success", current_user.id, {"permission_id": permission.id})
    return permission

@api_router.put("/permissions/{perm_id}", response_model=Permission)
async def update_permission(perm_id: str, perm_data: Permission, current_user: User = Depends(get_current_user)):
    """Update permission"""
    existing = await db.permissions.find_one({"id": perm_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    perm_dict = perm_data.dict()
    perm_dict['updated_by'] = current_user.id
    perm_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    perm_dict.pop('_id', None)
    
    await db.permissions.update_one({"id": perm_id}, {"$set": perm_dict})
    
    updated_perm = await db.permissions.find_one({"id": perm_id})
    updated_perm.pop('_id', None)
    
    await log_activity("user_management", "permissions", "update", "success", current_user.id, {"permission_id": perm_id})
    return Permission(**parse_from_mongo(updated_perm))

@api_router.delete("/permissions/{perm_id}")
async def delete_permission(perm_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete permission"""
    existing = await db.permissions.find_one({"id": perm_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    await db.permissions.update_one(
        {"id": perm_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "permissions", "delete", "success", current_user.id, {"permission_id": perm_id})
    return {"message": "Permission deleted successfully"}

# Modules CRUD
@api_router.get("/modules", response_model=List[Module])
async def get_modules(current_user: User = Depends(get_current_user)):
    modules = await db.modules.find({"is_active": True}).to_list(length=None)
    result = []
    for module in modules:
        module.pop('_id', None)
        result.append(Module(**parse_from_mongo(module)))
    return result

@api_router.post("/modules", response_model=Module)
async def create_module(module_data: Module, current_user: User = Depends(get_current_user)):
    """Create new module"""
    existing = await db.modules.find_one({"name": module_data.name, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Module already exists")
    
    module_dict = module_data.dict()
    module_dict['created_by'] = current_user.id
    module = Module(**module_dict)
    module_dict = prepare_for_mongo(module.dict())
    module_dict.pop('_id', None)
    await db.modules.insert_one(module_dict)
    
    await log_activity("user_management", "modules", "create", "success", current_user.id, {"module_id": module.id})
    return module

@api_router.put("/modules/{module_id}", response_model=Module)
async def update_module(module_id: str, module_data: Module, current_user: User = Depends(get_current_user)):
    """Update module"""
    existing = await db.modules.find_one({"id": module_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Module not found")
    
    module_dict = module_data.dict()
    module_dict['updated_by'] = current_user.id
    module_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    module_dict.pop('_id', None)
    
    await db.modules.update_one({"id": module_id}, {"$set": module_dict})
    
    updated_module = await db.modules.find_one({"id": module_id})
    updated_module.pop('_id', None)
    
    await log_activity("user_management", "modules", "update", "success", current_user.id, {"module_id": module_id})
    return Module(**parse_from_mongo(updated_module))

@api_router.delete("/modules/{module_id}")
async def delete_module(module_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete module"""
    existing = await db.modules.find_one({"id": module_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Module not found")
    
    await db.modules.update_one(
        {"id": module_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "modules", "delete", "success", current_user.id, {"module_id": module_id})
    return {"message": "Module deleted successfully"}

# Menus CRUD
@api_router.get("/menus", response_model=List[Menu])
async def get_menus(current_user: User = Depends(get_current_user)):
    menus = await db.menus.find({"is_active": True}).to_list(length=None)
    result = []
    for menu in menus:
        menu.pop('_id', None)
        result.append(Menu(**parse_from_mongo(menu)))
    return result

@api_router.post("/menus", response_model=Menu)
async def create_menu(menu_data: Menu, current_user: User = Depends(get_current_user)):
    """Create new menu"""
    existing = await db.menus.find_one({"name": menu_data.name, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Menu already exists")
    
    menu_dict = menu_data.dict()
    menu_dict['created_by'] = current_user.id
    menu = Menu(**menu_dict)
    menu_dict = prepare_for_mongo(menu.dict())
    menu_dict.pop('_id', None)
    await db.menus.insert_one(menu_dict)
    
    await log_activity("user_management", "menus", "create", "success", current_user.id, {"menu_id": menu.id})
    return menu

@api_router.put("/menus/{menu_id}", response_model=Menu)
async def update_menu(menu_id: str, menu_data: Menu, current_user: User = Depends(get_current_user)):
    """Update menu"""
    existing = await db.menus.find_one({"id": menu_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    menu_dict = menu_data.dict()
    menu_dict['updated_by'] = current_user.id
    menu_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    menu_dict.pop('_id', None)
    
    await db.menus.update_one({"id": menu_id}, {"$set": menu_dict})
    
    updated_menu = await db.menus.find_one({"id": menu_id})
    updated_menu.pop('_id', None)
    
    await log_activity("user_management", "menus", "update", "success", current_user.id, {"menu_id": menu_id})
    return Menu(**parse_from_mongo(updated_menu))

@api_router.delete("/menus/{menu_id}")
async def delete_menu(menu_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete menu"""
    existing = await db.menus.find_one({"id": menu_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    await db.menus.update_one(
        {"id": menu_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "menus", "delete", "success", current_user.id, {"menu_id": menu_id})
    return {"message": "Menu deleted successfully"}

# Role-Permissions CRUD
@api_router.get("/role-permissions", response_model=List[RolePermission])
async def get_role_permissions(current_user: User = Depends(get_current_user)):
    role_perms = await db.role_permissions.find({"is_active": True}).to_list(length=None)
    result = []
    for rp in role_perms:
        rp.pop('_id', None)
        result.append(RolePermission(**parse_from_mongo(rp)))
    return result

@api_router.post("/role-permissions", response_model=RolePermission)
async def create_role_permission(rp_data: RolePermission, current_user: User = Depends(get_current_user)):
    """Create new role-permission mapping"""
    existing = await db.role_permissions.find_one({
        "role_id": rp_data.role_id, 
        "permission_id": rp_data.permission_id, 
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="Role-Permission mapping already exists")
    
    rp_dict = rp_data.dict()
    rp_dict['created_by'] = current_user.id
    role_perm = RolePermission(**rp_dict)
    rp_dict = prepare_for_mongo(role_perm.dict())
    rp_dict.pop('_id', None)
    await db.role_permissions.insert_one(rp_dict)
    
    await log_activity("user_management", "role_permissions", "create", "success", current_user.id, {"mapping_id": role_perm.id})
    return role_perm

@api_router.put("/role-permissions/{rp_id}", response_model=RolePermission)
async def update_role_permission(rp_id: str, rp_data: RolePermission, current_user: User = Depends(get_current_user)):
    """Update role-permission mapping"""
    existing = await db.role_permissions.find_one({"id": rp_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Role-Permission mapping not found")
    
    rp_dict = rp_data.dict()
    rp_dict['updated_by'] = current_user.id
    rp_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    rp_dict.pop('_id', None)
    
    await db.role_permissions.update_one({"id": rp_id}, {"$set": rp_dict})
    
    updated_rp = await db.role_permissions.find_one({"id": rp_id})
    updated_rp.pop('_id', None)
    
    await log_activity("user_management", "role_permissions", "update", "success", current_user.id, {"mapping_id": rp_id})
    return RolePermission(**parse_from_mongo(updated_rp))

@api_router.delete("/role-permissions/{rp_id}")
async def delete_role_permission(rp_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete role-permission mapping"""
    existing = await db.role_permissions.find_one({"id": rp_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="Role-Permission mapping not found")
    
    await db.role_permissions.update_one(
        {"id": rp_id}, 
        {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity("user_management", "role_permissions", "delete", "success", current_user.id, {"mapping_id": rp_id})
    return {"message": "Role-Permission mapping deleted successfully"}

# Activity Logs (Read-only)
@api_router.get("/activity-logs", response_model=List[ActivityLog])
async def get_activity_logs(current_user: User = Depends(get_current_user)):
    """Get activity logs"""
    logs = await db.activity_logs.find().sort("created_at", -1).limit(100).to_list(length=None)
    result = []
    for log in logs:
        log.pop('_id', None)
        result.append(ActivityLog(**parse_from_mongo(log)))
    return result

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