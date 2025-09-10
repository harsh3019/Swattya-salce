from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Dict, Any
import os
import jwt
import bcrypt
import uuid
import json
import logging
import random
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
    name: str
    description: Optional[str] = None
    status: str = "active"  # active/inactive

class Module(BaseAuditModel):
    name: str
    description: Optional[str] = None
    status: str = "active"  # active/inactive

class Menu(BaseAuditModel):
    name: str
    path: str
    parent: Optional[str] = None  # nullable for root menus
    module_id: str
    order_index: int = 0

class RolePermission(BaseAuditModel):
    role_id: str
    module_id: str
    menu_id: str
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

def generate_id() -> str:
    """Generate a random 6-digit ID"""
    return str(random.randint(100000, 999999))

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
        
        user.pop('_id', None)
        return User(**parse_from_mongo(user))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")

async def check_permission(user: User, module_name: str, menu_name: str, permission_name: str):
    """Check if user has specific permission for module/menu"""
    if not user.role_id:
        return False
    
    # Find the module
    module = await db.modules.find_one({"name": module_name, "status": "active"})
    if not module:
        return False
    
    # Find the menu
    menu = await db.menus.find_one({"name": menu_name, "module_id": module["id"]})
    if not menu:
        return False
    
    # Find the permission
    permission = await db.permissions.find_one({"name": permission_name, "status": "active"})
    if not permission:
        return False
    
    # Check role permission
    role_perm = await db.role_permissions.find_one({
        "role_id": user.role_id,
        "module_id": module["id"],
        "menu_id": menu["id"],
        "permission_id": permission["id"],
        "is_active": True
    })
    
    return role_perm is not None

# Permission helper functions
async def has_permission_by_menu_id(user: User, menu_id: str, permission_name: str):
    """Check permission by menu ID - optimized helper"""
    if not user.role_id:
        return False
    
    # Find the permission
    permission = await db.permissions.find_one({"name": permission_name, "status": "active"})
    if not permission:
        return False
    
    # Check role permission
    role_perm = await db.role_permissions.find_one({
        "role_id": user.role_id,
        "menu_id": menu_id,
        "permission_id": permission["id"],
        "is_active": True
    })
    
    return role_perm is not None

async def has_view(user: User, menu_id: str):
    return await has_permission_by_menu_id(user, menu_id, "View")

async def has_add(user: User, menu_id: str):
    return await has_permission_by_menu_id(user, menu_id, "Add")

async def has_edit(user: User, menu_id: str):
    return await has_permission_by_menu_id(user, menu_id, "Edit")

async def has_delete(user: User, menu_id: str):
    return await has_permission_by_menu_id(user, menu_id, "Delete")

async def has_export(user: User, menu_id: str):
    return await has_permission_by_menu_id(user, menu_id, "Export")

async def require_permission(module_name: str, menu_name: str, permission_name: str):
    """Dependency to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        async def check():
            has_permission = await check_permission(current_user, module_name, menu_name, permission_name)
            if not has_permission:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return current_user
        return check()
    return Depends(permission_checker)

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

def prepare_for_json(data: dict) -> dict:
    """Prepare data for JSON response by removing MongoDB ObjectId and converting dates"""
    if data is None:
        return None
    
    # Remove MongoDB ObjectId
    data.pop('_id', None)
    
    # Parse from MongoDB format
    return parse_from_mongo(data)

async def log_audit_trail(user_id: str, action: str, resource_type: str, resource_id: str, details: str):
    """Log audit trail for important actions"""
    await log_activity("audit", resource_type.lower(), action.lower(), "success", user_id, {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details
    })

async def get_user_permissions(user_id: str) -> List[Dict]:
    """Get user permissions by user ID"""
    user = await db.users.find_one({"id": user_id, "is_active": True})
    if not user or not user.get("role_id"):
        return []
    
    # Get all role permissions for this user
    role_permissions = await db.role_permissions.find({
        "role_id": user["role_id"],
        "is_active": True
    }).to_list(length=None)
    
    permissions = []
    for rp in role_permissions:
        # Get menu and permission details first
        menu = await db.menus.find_one({"id": rp["menu_id"]})
        permission = await db.permissions.find_one({"id": rp["permission_id"], "status": "active"})
        
        if menu and permission:
            # Get module details from menu
            module = await db.modules.find_one({"id": menu["module_id"], "status": "active"})
            
            if module:
                permissions.append({
                    "module": module["name"],
                    "menu": menu["name"],
                    "permission": permission["name"],
                    "path": menu["path"]
                })
    
    return permissions

# ================ NAVIGATION ENDPOINTS ================

@api_router.get("/nav/sidebar")
async def get_sidebar_navigation(current_user: User = Depends(get_current_user)):
    """Get sidebar navigation based on user permissions"""
    if not current_user.role_id:
        return {"modules": []}
    
    try:
        # Get all role permissions for this user
        role_permissions = await db.role_permissions.find({
            "role_id": current_user.role_id,
            "is_active": True
        }).to_list(length=None)
        
        if not role_permissions:
            return {"modules": []}
        
        # Get all modules, menus, and permissions that user has access to
        accessible_modules = {}
        
        for rp in role_permissions:
            # Get permission details
            permission = await db.permissions.find_one({
                "id": rp["permission_id"],
                "status": "active"
            })
            
            # Only include if user has 'View' permission
            if permission and permission["name"] == "View":
                # Get module details
                module = await db.modules.find_one({
                    "id": rp["module_id"],
                    "status": "active"
                })
                
                # Get menu details
                menu = await db.menus.find_one({
                    "id": rp["menu_id"]
                })
                
                if module and menu:
                    module_id = module["id"]
                    
                    if module_id not in accessible_modules:
                        accessible_modules[module_id] = {
                            "id": module["id"],
                            "name": module["name"],
                            "description": module.get("description"),
                            "order_index": getattr(module, 'order_index', 0),
                            "menus": {}
                        }
                    
                    # Add menu to module
                    accessible_modules[module_id]["menus"][menu["id"]] = {
                        "id": menu["id"],
                        "name": menu["name"],
                        "path": menu["path"],
                        "parent": menu.get("parent"),
                        "order_index": menu["order_index"]
                    }
        
        # Convert to final structure and sort
        result_modules = []
        for module_data in accessible_modules.values():
            # Convert menus dict to sorted list
            menus_list = list(module_data["menus"].values())
            menus_list.sort(key=lambda x: x["order_index"])
            
            # Build nested menu structure
            menu_tree = build_menu_tree(menus_list)
            
            if menu_tree:  # Only include modules with visible menus
                result_modules.append({
                    "id": module_data["id"],
                    "name": module_data["name"],
                    "description": module_data.get("description"),
                    "menus": menu_tree
                })
        
        # Sort modules by order_index (if we add that field later)
        result_modules.sort(key=lambda x: x.get("order_index", 0))
        
        return {"modules": result_modules}
        
    except Exception as e:
        logger.error(f"Error getting sidebar navigation: {e}")
        return {"modules": []}

def build_menu_tree(menus):
    """Build nested menu structure from flat menu list"""
    menu_dict = {menu["id"]: menu for menu in menus}
    root_menus = []
    
    for menu in menus:
        if menu.get("parent"):
            # This is a child menu
            parent_menu = menu_dict.get(menu["parent"])
            if parent_menu:
                if "children" not in parent_menu:
                    parent_menu["children"] = []
                parent_menu["children"].append(menu)
        else:
            # This is a root menu
            root_menus.append(menu)
    
    # Sort children within each parent
    for menu in menu_dict.values():
        if "children" in menu:
            menu["children"].sort(key=lambda x: x["order_index"])
    
    return root_menus

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

@api_router.get("/auth/permissions")
async def get_current_user_permissions(current_user: User = Depends(get_current_user)):
    """Get current user's permissions"""
    if not current_user.role_id:
        return {"permissions": []}
    
    # Get all role permissions for this user
    role_permissions = await db.role_permissions.find({
        "role_id": current_user.role_id,
        "is_active": True
    }).to_list(length=None)
    
    permissions = []
    for rp in role_permissions:
        # Get menu and permission details first
        menu = await db.menus.find_one({"id": rp["menu_id"]})
        permission = await db.permissions.find_one({"id": rp["permission_id"], "status": "active"})
        
        if menu and permission:
            # Get module details from menu
            module = await db.modules.find_one({"id": menu["module_id"], "status": "active"})
            
            if module:
                permissions.append({
                    "module": module["name"],
                    "menu": menu["name"],
                    "permission": permission["name"],
                    "path": menu["path"]
                })
    
    return {"permissions": permissions}

# ================ ROLE PERMISSION MANAGEMENT ENDPOINTS ================

@api_router.get("/role-permissions/matrix/{role_id}")
async def get_role_permission_matrix(role_id: str, current_user: User = Depends(get_current_user)):
    """Get permission matrix for a specific role"""
    # Check View permission for Role Permissions
    has_permission = await check_permission(current_user, "User Management", "Role Permissions", "View")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view role permissions")
    
    # Get all permissions
    permissions = await db.permissions.find({"status": "active"}).to_list(length=None)
    permissions_dict = {p["id"]: p for p in permissions}
    
    # Get all modules and their menus
    modules = await db.modules.find({"status": "active"}).to_list(length=None)
    matrix = []
    
    for module in modules:
        menus = await db.menus.find({"module_id": module["id"]}).sort("order_index", 1).to_list(length=None)
        
        module_data = {
            "module": {
                "id": module["id"],
                "name": module["name"],
                "description": module.get("description", "")
            },
            "menus": []
        }
        
        for menu in menus:
            menu_permissions = {}
            
            # Get existing role permissions for this menu
            role_perms = await db.role_permissions.find({
                "role_id": role_id,
                "module_id": module["id"],
                "menu_id": menu["id"],
                "is_active": True
            }).to_list(length=None)
            
            # Create permission map for this menu
            for perm in permissions:
                has_perm = any(rp["permission_id"] == perm["id"] for rp in role_perms)
                menu_permissions[perm["name"]] = {
                    "granted": has_perm,
                    "permission_id": perm["id"],
                    "description": perm.get("description", "")
                }
            
            module_data["menus"].append({
                "id": menu["id"],
                "name": menu["name"],
                "path": menu["path"],
                "permissions": menu_permissions
            })
        
        if module_data["menus"]:  # Only include modules with menus
            matrix.append(module_data)
    
    return {"matrix": matrix}

@api_router.post("/role-permissions/matrix/{role_id}")
async def update_role_permission_matrix(
    role_id: str, 
    matrix_update: dict, 
    current_user: User = Depends(get_current_user)
):
    """Update role permission matrix"""
    # Check Edit permission for Role Permissions
    has_permission = await check_permission(current_user, "User Management", "Role Permissions", "Edit")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit role permissions")
    
    updates = matrix_update.get("updates", [])
    
    for update in updates:
        menu_id = update.get("menu_id")
        module_id = update.get("module_id")
        permission_id = update.get("permission_id")
        granted = update.get("granted", False)
        
        if not all([menu_id, module_id, permission_id]):
            continue
        
        # Check if role permission exists
        existing = await db.role_permissions.find_one({
            "role_id": role_id,
            "module_id": module_id,
            "menu_id": menu_id,
            "permission_id": permission_id
        })
        
        if granted:
            if not existing:
                # Create new role permission
                role_perm = RolePermission(
                    role_id=role_id,
                    module_id=module_id,
                    menu_id=menu_id,
                    permission_id=permission_id,
                    created_by=current_user.id
                )
                rp_dict = prepare_for_mongo(role_perm.dict())
                rp_dict.pop('_id', None)
                await db.role_permissions.insert_one(rp_dict)
            elif not existing.get("is_active", True):
                # Reactivate existing permission
                await db.role_permissions.update_one(
                    {"id": existing["id"]},
                    {"$set": {"is_active": True, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
        else:
            if existing and existing.get("is_active", True):
                # Deactivate permission (soft delete)
                await db.role_permissions.update_one(
                    {"id": existing["id"]},
                    {"$set": {"is_active": False, "updated_by": current_user.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
    
    await log_activity("user_management", "role_permissions", "update", "success", current_user.id, {
        "role_id": role_id,
        "updates_count": len(updates)
    })
    
    return {"message": "Role permissions updated successfully"}

@api_router.get("/role-permissions/unassigned-modules/{role_id}")
async def get_unassigned_modules(role_id: str, current_user: User = Depends(get_current_user)):
    """Get modules not yet assigned to a role"""
    # Check View permission for Role Permissions
    has_permission = await check_permission(current_user, "User Management", "Role Permissions", "View")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view role permissions")
    
    # Get all modules
    all_modules = await db.modules.find({"status": "active"}).to_list(length=None)
    
    # Get modules already assigned to this role
    assigned_modules = await db.role_permissions.find({
        "role_id": role_id,
        "is_active": True
    }).distinct("module_id")
    
    # Filter unassigned modules
    unassigned = [
        {"id": module["id"], "name": module["name"], "description": module.get("description", "")}
        for module in all_modules
        if module["id"] not in assigned_modules
    ]
    
    return {"modules": unassigned}

@api_router.post("/role-permissions/add-module")
async def add_module_to_role(
    assignment_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Add a module to a role with specified permissions"""
    # Check Add permission for Role Permissions
    has_permission = await check_permission(current_user, "User Management", "Role Permissions", "Add")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to add role permissions")
    
    role_id = assignment_data.get("role_id")
    module_id = assignment_data.get("module_id")
    permissions = assignment_data.get("permissions", [])  # [{"menu_id": "...", "permission_ids": ["..."]}]
    
    if not all([role_id, module_id]):
        raise HTTPException(status_code=400, detail="Role ID and Module ID are required")
    
    # Create role permissions
    created_count = 0
    for perm_data in permissions:
        menu_id = perm_data.get("menu_id")
        permission_ids = perm_data.get("permission_ids", [])
        
        for permission_id in permission_ids:
            # Check if already exists
            existing = await db.role_permissions.find_one({
                "role_id": role_id,
                "module_id": module_id,
                "menu_id": menu_id,
                "permission_id": permission_id
            })
            
            if not existing:
                role_perm = RolePermission(
                    role_id=role_id,
                    module_id=module_id,
                    menu_id=menu_id,
                    permission_id=permission_id,
                    created_by=current_user.id
                )
                rp_dict = prepare_for_mongo(role_perm.dict())
                rp_dict.pop('_id', None)
                await db.role_permissions.insert_one(rp_dict)
                created_count += 1
    
    await log_activity("user_management", "role_permissions", "create", "success", current_user.id, {
        "role_id": role_id,
        "module_id": module_id,
        "permissions_created": created_count
    })
    
    return {"message": f"Module added to role with {created_count} permissions"}

# ================ EXPORT ENDPOINTS ================

@api_router.get("/users/export")
async def export_users(current_user: User = Depends(get_current_user)):
    """Export users to Excel"""
    # Check Export permission
    has_permission = await check_permission(current_user, "User Management", "Users", "Export")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to export users")
    
    # For now, return CSV data (Excel implementation would require additional dependencies)
    users = await db.users.find({"is_active": True}).to_list(length=None)
    
    csv_data = "Username,Email,Status,Created At\n"
    for user in users:
        user.pop('_id', None)
        parsed_user = parse_from_mongo(user)
        csv_data += f"{parsed_user.get('username', '')},{parsed_user.get('email', '')},{parsed_user.get('status', '')},{parsed_user.get('created_at', '')}\n"
    
    await log_activity("user_management", "users", "export", "success", current_user.id)
    
    return {"data": csv_data, "filename": f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}

@api_router.get("/roles/export")
async def export_roles(current_user: User = Depends(get_current_user)):
    """Export roles to Excel"""
    has_permission = await check_permission(current_user, "User Management", "Roles", "Export")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to export roles")
    
    roles = await db.roles.find({"is_active": True}).to_list(length=None)
    
    csv_data = "Name,Code,Description,Created At\n"
    for role in roles:
        role.pop('_id', None)
        parsed_role = parse_from_mongo(role)
        csv_data += f"{parsed_role.get('name', '')},{parsed_role.get('code', '')},{parsed_role.get('description', '')},{parsed_role.get('created_at', '')}\n"
    
    await log_activity("user_management", "roles", "export", "success", current_user.id)
    
    return {"data": csv_data, "filename": f"roles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}

# ================ USER MANAGEMENT ENDPOINTS ================

# Users CRUD
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    """Get all users"""
    # Check View permission
    has_permission = await check_permission(current_user, "User Management", "Users", "View")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view users")
    
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
    # Check Add permission
    has_permission = await check_permission(current_user, "User Management", "Users", "Add")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to create users")
    
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

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_user: User = Depends(get_current_user)):
    """Update user"""
    # Check Edit permission
    has_permission = await check_permission(current_user, "User Management", "Users", "Edit")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit users")
    
    existing = await db.users.find_one({"id": user_id, "is_active": True})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_dict = user_data.dict(exclude_unset=True)
    user_dict['updated_by'] = current_user.id
    user_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"id": user_id}, {"$set": user_dict})
    
    updated_user = await db.users.find_one({"id": user_id})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found after update")
    updated_user.pop('_id', None)
    
    await log_activity("user_management", "users", "update", "success", current_user.id, {"user_id": user_id})
    
    # Create response without password_hash
    user_response = updated_user.copy()
    user_response.pop('password_hash', None)
    return parse_from_mongo(user_response)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete user"""
    # Check Delete permission
    has_permission = await check_permission(current_user, "User Management", "Users", "Delete")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete users")
    
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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    role_dict = role_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
    role_dict['updated_by'] = current_user.id
    role_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    role_dict.pop('_id', None)
    
    await db.roles.update_one({"id": role_id}, {"$set": role_dict})
    
    updated_role = await db.roles.find_one({"id": role_id})
    if not updated_role:
        raise HTTPException(status_code=404, detail="Role not found after update")
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
# Old company endpoint removed - using new company registration endpoint

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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    dept_dict = dept_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    desig_dict = desig_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
    desig_dict['updated_by'] = current_user.id
    desig_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    desig_dict.pop('_id', None)
    
    await db.designations.update_one({"id": desig_id}, {"$set": desig_dict})
    
    updated_desig = await db.designations.find_one({"id": desig_id})
    if not updated_desig:
        raise HTTPException(status_code=404, detail="Designation not found after update")
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
    existing = await db.permissions.find_one({"name": perm_data.name, "is_active": True})
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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    perm_dict = perm_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
    perm_dict['updated_by'] = current_user.id
    perm_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    perm_dict.pop('_id', None)
    
    await db.permissions.update_one({"id": perm_id}, {"$set": perm_dict})
    
    updated_perm = await db.permissions.find_one({"id": perm_id})
    if not updated_perm:
        raise HTTPException(status_code=404, detail="Permission not found after update")
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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    module_dict = module_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
    module_dict['updated_by'] = current_user.id
    module_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    module_dict.pop('_id', None)
    
    await db.modules.update_one({"id": module_id}, {"$set": module_dict})
    
    updated_module = await db.modules.find_one({"id": module_id})
    if not updated_module:
        raise HTTPException(status_code=404, detail="Module not found after update")
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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    menu_dict = menu_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
    menu_dict['updated_by'] = current_user.id
    menu_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    menu_dict.pop('_id', None)
    
    await db.menus.update_one({"id": menu_id}, {"$set": menu_dict})
    
    updated_menu = await db.menus.find_one({"id": menu_id})
    if not updated_menu:
        raise HTTPException(status_code=404, detail="Menu not found after update")
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
    
    # Only update the fields that should be updated, exclude auto-generated fields
    rp_dict = rp_data.dict(exclude={'id', 'created_at', 'created_by', 'is_active'})
    rp_dict['updated_by'] = current_user.id
    rp_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    rp_dict.pop('_id', None)
    
    await db.role_permissions.update_one({"id": rp_id}, {"$set": rp_dict})
    
    updated_rp = await db.role_permissions.find_one({"id": rp_id})
    if not updated_rp:
        raise HTTPException(status_code=404, detail="Role-Permission mapping not found after update")
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

# ================ STARTUP EVENT ================

@app.on_event("startup")
async def startup_event():
    """Initialize default data"""
    try:
        # Create default admin user if not exists
        admin_user = await db.users.find_one({"username": "admin", "is_active": True})
        if not admin_user:
            await initialize_rbac_system()
            logger.info("RBAC system initialized with default admin user: admin/admin123")
        
        # Always check and initialize company master data
        if await db.company_types.count_documents({}) == 0:
            await initialize_company_master_data()
            logger.info("Company master data initialized")
        
        # Initialize Lead Management master data if not exists
        if await db.product_services.count_documents({}) == 0:
            await initialize_lead_master_data()
            logger.info("Lead Management master data initialized")
        
        # Initialize Opportunity Management master data if not exists
        if await db.mst_stages.count_documents({}) == 0:
            await initialize_opportunity_master_data()
            logger.info("Opportunity Management master data initialized")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")

async def initialize_rbac_system():
    """Initialize complete RBAC system with permissions, modules, menus, and roles"""
    
    # 1. Create default permissions (standardized naming)
    permissions_data = [
        {"name": "View", "description": "View and list records"},
        {"name": "Add", "description": "Create new records"},
        {"name": "Edit", "description": "Update existing records"},
        {"name": "Delete", "description": "Delete records (soft delete)"},
        {"name": "Export", "description": "Export data to Excel/CSV"}
    ]
    
    created_permissions = {}
    for perm_data in permissions_data:
        perm = Permission(**perm_data, created_by="system")
        perm_dict = prepare_for_mongo(perm.dict())
        perm_dict.pop('_id', None)
        await db.permissions.insert_one(perm_dict)
        created_permissions[perm_data["name"]] = perm.id
    
    # 2. Create default modules
    modules_data = [
        {"name": "User Management", "description": "User and role management"},
        {"name": "Sales", "description": "Sales and CRM features"},
        {"name": "System", "description": "System administration"}
    ]
    
    created_modules = {}
    for mod_data in modules_data:
        mod = Module(**mod_data, created_by="system")
        mod_dict = prepare_for_mongo(mod.dict())
        mod_dict.pop('_id', None)
        await db.modules.insert_one(mod_dict)
        created_modules[mod_data["name"]] = mod.id
    
    # 3. Create default menus
    menus_data = [
        # User Management menus
        {"name": "Users", "path": "/users", "module_id": created_modules["User Management"], "order_index": 1},
        {"name": "Roles", "path": "/roles", "module_id": created_modules["User Management"], "order_index": 2},
        {"name": "Departments", "path": "/departments", "module_id": created_modules["User Management"], "order_index": 3},
        {"name": "Designations", "path": "/designations", "module_id": created_modules["User Management"], "order_index": 4},
        {"name": "Permissions", "path": "/permissions", "module_id": created_modules["User Management"], "order_index": 5},
        {"name": "Modules", "path": "/modules", "module_id": created_modules["User Management"], "order_index": 6},
        {"name": "Menus", "path": "/menus", "module_id": created_modules["User Management"], "order_index": 7},
        {"name": "Role Permissions", "path": "/role-permissions", "module_id": created_modules["User Management"], "order_index": 8},
        
        # Sales menus
        {"name": "Companies", "path": "/companies", "module_id": created_modules["Sales"], "order_index": 1},
        {"name": "Contacts", "path": "/contacts", "module_id": created_modules["Sales"], "order_index": 2},
        {"name": "Channel Partners", "path": "/channel-partners", "module_id": created_modules["Sales"], "order_index": 3},
        {"name": "Product Services", "path": "/product-services", "module_id": created_modules["Sales"], "order_index": 4},
        {"name": "Sub-Tender Types", "path": "/sub-tender-types", "module_id": created_modules["Sales"], "order_index": 5},
        {"name": "Leads", "path": "/leads", "module_id": created_modules["Sales"], "order_index": 6},
        {"name": "Opportunities", "path": "/opportunities", "module_id": created_modules["Sales"], "order_index": 7},
        
        # System menus
        {"name": "Activity Logs", "path": "/activity-logs", "module_id": created_modules["System"], "order_index": 1}
    ]
    
    created_menus = {}
    for menu_data in menus_data:
        menu = Menu(**menu_data, created_by="system")
        menu_dict = prepare_for_mongo(menu.dict())
        menu_dict.pop('_id', None)
        await db.menus.insert_one(menu_dict)
        created_menus[menu_data["name"]] = menu.id
    
    # 4. Create default role
    admin_role = Role(
        name="Super Admin",
        code="SUPER_ADMIN",
        description="Full system access",
        created_by="system"
    )
    role_dict = prepare_for_mongo(admin_role.dict())
    role_dict.pop('_id', None)
    await db.roles.insert_one(role_dict)
    
    # 5. Create role-permission mappings (give admin all permissions for all menus)
    for menu_name, menu_id in created_menus.items():
        menu_doc = await db.menus.find_one({"id": menu_id})
        if menu_doc:
            for perm_name, perm_id in created_permissions.items():
                role_perm = RolePermission(
                    role_id=admin_role.id,
                    module_id=menu_doc["module_id"],
                    menu_id=menu_id,
                    permission_id=perm_id,
                    created_by="system"
                )
                rp_dict = prepare_for_mongo(role_perm.dict())
                rp_dict.pop('_id', None)
                await db.role_permissions.insert_one(rp_dict)
    
    # 6. Create default department and designation
    default_dept = Department(name="IT", created_by="system")
    dept_dict = prepare_for_mongo(default_dept.dict())
    dept_dict.pop('_id', None)
    await db.departments.insert_one(dept_dict)
    
    default_desig = Designation(name="Administrator", created_by="system")
    desig_dict = prepare_for_mongo(default_desig.dict())
    desig_dict.pop('_id', None)
    await db.designations.insert_one(desig_dict)
    
    # 7. Create default admin user
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

    # Initialize company registration master data
    await initialize_company_master_data()

async def initialize_company_master_data():
    """Initialize master data for company registration"""
    
    # Check if data already exists
    if await db.company_types.count_documents({}) > 0:
        return
    
    logger.info("Initializing company registration master data...")
    
    # Company Types
    company_types = [
        {"id": str(uuid.uuid4()), "name": "Private Limited", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Public Limited", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Partnership", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Sole Proprietorship", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "LLP", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.company_types.insert_many(company_types)
    
    # Account Types
    account_types = [
        {"id": str(uuid.uuid4()), "name": "Customer", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Prospect", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Partner", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Vendor", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.account_types.insert_many(account_types)
    
    # Regions
    regions = [
        {"id": str(uuid.uuid4()), "name": "North India", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "South India", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "East India", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "West India", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Central India", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Northeast India", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.regions.insert_many(regions)
    
    # Business Types
    business_types = [
        {"id": str(uuid.uuid4()), "name": "B2B", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "B2C", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "B2G", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "C2C", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.business_types.insert_many(business_types)
    
    # Industries
    industries_data = [
        {"id": str(uuid.uuid4()), "name": "Technology", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Finance", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Healthcare", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Manufacturing", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Retail", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Education", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Real Estate", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Agriculture", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.industries.insert_many(industries_data)
    
    # Sub-Industries
    tech_id = next(i["id"] for i in industries_data if i["name"] == "Technology")
    finance_id = next(i["id"] for i in industries_data if i["name"] == "Finance")
    healthcare_id = next(i["id"] for i in industries_data if i["name"] == "Healthcare")
    manufacturing_id = next(i["id"] for i in industries_data if i["name"] == "Manufacturing")
    
    sub_industries = [
        # Technology sub-industries
        {"id": str(uuid.uuid4()), "name": "Software Development", "industry_id": tech_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Cloud Services", "industry_id": tech_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "AI/ML", "industry_id": tech_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Cybersecurity", "industry_id": tech_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # Finance sub-industries
        {"id": str(uuid.uuid4()), "name": "Banking", "industry_id": finance_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Insurance", "industry_id": finance_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Investment", "industry_id": finance_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Fintech", "industry_id": finance_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # Healthcare sub-industries
        {"id": str(uuid.uuid4()), "name": "Pharmaceuticals", "industry_id": healthcare_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Medical Devices", "industry_id": healthcare_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Telemedicine", "industry_id": healthcare_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # Manufacturing sub-industries
        {"id": str(uuid.uuid4()), "name": "Automotive", "industry_id": manufacturing_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Electronics", "industry_id": manufacturing_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Textiles", "industry_id": manufacturing_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.sub_industries.insert_many(sub_industries)
    
    # Countries
    countries = [
        {"id": str(uuid.uuid4()), "name": "India", "code": "IN", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "United States", "code": "US", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "United Kingdom", "code": "GB", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Canada", "code": "CA", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Australia", "code": "AU", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Germany", "code": "DE", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "France", "code": "FR", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Japan", "code": "JP", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Singapore", "code": "SG", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.countries.insert_many(countries)
    
    # States (focusing on India)
    india_id = next(c["id"] for c in countries if c["name"] == "India")
    us_id = next(c["id"] for c in countries if c["name"] == "United States")
    
    states = [
        # Indian states
        {"id": str(uuid.uuid4()), "name": "Maharashtra", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Karnataka", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Tamil Nadu", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Gujarat", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Delhi", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Haryana", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Punjab", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Rajasthan", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Uttar Pradesh", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "West Bengal", "country_id": india_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # US states (sample)
        {"id": str(uuid.uuid4()), "name": "California", "country_id": us_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "New York", "country_id": us_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Texas", "country_id": us_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.states.insert_many(states)
    
    # Cities (focusing on major Indian cities)
    maharashtra_id = next(s["id"] for s in states if s["name"] == "Maharashtra")
    karnataka_id = next(s["id"] for s in states if s["name"] == "Karnataka")
    delhi_id = next(s["id"] for s in states if s["name"] == "Delhi")
    gujarat_id = next(s["id"] for s in states if s["name"] == "Gujarat")
    
    cities = [
        # Maharashtra cities
        {"id": str(uuid.uuid4()), "name": "Mumbai", "state_id": maharashtra_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Pune", "state_id": maharashtra_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Nagpur", "state_id": maharashtra_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # Karnataka cities
        {"id": str(uuid.uuid4()), "name": "Bangalore", "state_id": karnataka_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Mysore", "state_id": karnataka_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # Delhi cities
        {"id": str(uuid.uuid4()), "name": "New Delhi", "state_id": delhi_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Gurgaon", "state_id": delhi_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        
        # Gujarat cities
        {"id": str(uuid.uuid4()), "name": "Ahmedabad", "state_id": gujarat_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Surat", "state_id": gujarat_id, "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.cities.insert_many(cities)
    
    # Currencies
    currencies = [
        {"id": str(uuid.uuid4()), "code": "INR", "name": "Indian Rupee", "symbol": "₹", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "code": "USD", "name": "US Dollar", "symbol": "$", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "code": "EUR", "name": "Euro", "symbol": "€", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.currencies.insert_many(currencies)
    
    # Designations
    designations = [
        {"id": str(uuid.uuid4()), "name": "Chief Executive Officer", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Chief Technology Officer", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Chief Financial Officer", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Managing Director", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "General Manager", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Assistant General Manager", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Deputy General Manager", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Senior Manager", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Manager", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Assistant Manager", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Senior Executive", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Executive", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Senior Associate", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Associate", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Team Lead", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Senior Analyst", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Analyst", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Consultant", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Senior Consultant", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Director", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc)},
    ]
    await db.designations.insert_many(designations)
    
    logger.info("Company registration master data initialized successfully")

async def initialize_lead_master_data():
    """Initialize master data for Lead Management"""
    
    # Check if data already exists
    if await db.product_services.count_documents({}) > 0:
        return
    
    logger.info("Initializing Lead Management master data...")
    
    # Product & Services Master Data
    product_services = [
        {"id": str(uuid.uuid4()), "name": "Software Development", "description": "Custom software development services", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Web Development", "description": "Website and web application development", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Mobile App Development", "description": "iOS and Android mobile application development", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Cloud Services", "description": "Cloud infrastructure and migration services", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Digital Marketing", "description": "SEO, SEM, and digital marketing services", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Data Analytics", "description": "Business intelligence and data analytics", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Cybersecurity", "description": "Information security and cybersecurity services", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "AI/ML Solutions", "description": "Artificial Intelligence and Machine Learning solutions", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "IT Consulting", "description": "Technology consulting and advisory services", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "System Integration", "description": "Enterprise system integration services", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
    ]
    await db.product_services.insert_many(product_services)
    
    # Sub-Tender Types Master Data
    sub_tender_types = [
        {"id": str(uuid.uuid4()), "name": "Government - Central", "description": "Central government tenders and contracts", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Government - State", "description": "State government tenders and contracts", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Government - Municipal", "description": "Municipal and local government tenders", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Government - PSU", "description": "Public Sector Undertaking tenders", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Private - Enterprise", "description": "Large private enterprise contracts", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Private - SME", "description": "Small and Medium Enterprise contracts", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Private - Startup", "description": "Startup and emerging company contracts", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
        {"id": str(uuid.uuid4()), "name": "Private - International", "description": "International private sector contracts", "is_active": True, "created_by": "system", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
    ]
    await db.sub_tender_types.insert_many(sub_tender_types)
    
    logger.info("Lead Management master data initialized successfully")

async def initialize_opportunity_master_data():
    """Initialize opportunity management master data"""
    try:
        # Initialize Stages (L1-L8)
        stages_data = [
            {"stage_name": "Prospect", "stage_code": "L1", "stage_order": 1, "description": "Initial prospect identification and qualification"},
            {"stage_name": "Qualification", "stage_code": "L2", "stage_order": 2, "description": "Detailed qualification using BANT/CHAMP methodology"},
            {"stage_name": "Proposal", "stage_code": "L3", "stage_order": 3, "description": "Proposal creation and submission"},
            {"stage_name": "Technical Qualification", "stage_code": "L4", "stage_order": 4, "description": "Technical evaluation and quotation selection"},
            {"stage_name": "Commercial Negotiation", "stage_code": "L5", "stage_order": 5, "description": "Price negotiation and commercial terms"},
            {"stage_name": "Won", "stage_code": "L6", "stage_order": 6, "description": "Deal won and handover to delivery"},
            {"stage_name": "Lost", "stage_code": "L7", "stage_order": 7, "description": "Deal lost - capture learning and feedback"},
            {"stage_name": "Dropped", "stage_code": "L8", "stage_order": 8, "description": "Opportunity dropped - no longer active"}
        ]
        
        for stage_data in stages_data:
            existing = await db.mst_stages.find_one({"stage_code": stage_data["stage_code"]})
            if not existing:
                stage_record = {
                    "id": str(uuid.uuid4()),
                    **stage_data,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
                await db.mst_stages.insert_one(stage_record)
                print(f"Inserted stage: {stage_data['stage_name']}")

        # Initialize Regions
        regions_data = [
            {"region_name": "North India", "region_code": "NORTH", "description": "Delhi, Punjab, Haryana, Uttar Pradesh, Himachal Pradesh"},
            {"region_name": "South India", "region_code": "SOUTH", "description": "Karnataka, Tamil Nadu, Andhra Pradesh, Telangana, Kerala"},
            {"region_name": "West India", "region_code": "WEST", "description": "Maharashtra, Gujarat, Rajasthan, Goa"},
            {"region_name": "East India", "region_code": "EAST", "description": "West Bengal, Odisha, Jharkhand, Bihar"},
            {"region_name": "Central India", "region_code": "CENTRAL", "description": "Madhya Pradesh, Chhattisgarh"},
            {"region_name": "Northeast India", "region_code": "NORTHEAST", "description": "Assam, Meghalaya, Manipur, Mizoram, Nagaland, Tripura, Arunachal Pradesh, Sikkim"}
        ]
        
        for region_data in regions_data:
            existing = await db.mst_regions.find_one({"region_code": region_data["region_code"]})
            if not existing:
                region_record = {
                    "id": str(uuid.uuid4()),
                    **region_data,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
                await db.mst_regions.insert_one(region_record)
                print(f"Inserted region: {region_data['region_name']}")

        # Initialize Competitors
        competitors_data = [
            {"competitor_name": "TCS", "competitor_type": "Direct", "description": "Tata Consultancy Services - Leading IT services company", "strengths": "Brand recognition, large scale operations", "weaknesses": "Higher pricing, slower decision making"},
            {"competitor_name": "Infosys", "competitor_type": "Direct", "description": "Global leader in consulting and technology services", "strengths": "Strong delivery capabilities, innovation focus", "weaknesses": "Premium pricing, complex processes"},
            {"competitor_name": "Wipro", "competitor_type": "Direct", "description": "Leading technology services and consulting company", "strengths": "Domain expertise, global presence", "weaknesses": "Limited market share in certain segments"},
            {"competitor_name": "HCL Technologies", "competitor_type": "Direct", "description": "Technology and services company", "strengths": "Competitive pricing, agile delivery", "weaknesses": "Brand perception in premium segment"},
            {"competitor_name": "Local System Integrators", "competitor_type": "Indirect", "description": "Regional players and system integrators", "strengths": "Local market knowledge, flexible pricing", "weaknesses": "Limited scale, technology capabilities"},
            {"competitor_name": "In-house Development", "competitor_type": "Substitute", "description": "Client building internal capabilities", "strengths": "Full control, no external dependency", "weaknesses": "Higher long-term costs, skill constraints"}
        ]
        
        for competitor_data in competitors_data:
            existing = await db.mst_competitors.find_one({"competitor_name": competitor_data["competitor_name"]})
            if not existing:
                competitor_record = {
                    "id": str(uuid.uuid4()),
                    **competitor_data,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
                await db.mst_competitors.insert_one(competitor_record)
                print(f"Inserted competitor: {competitor_data['competitor_name']}")

        # Initialize Currencies
        currencies_data = [
            {"name": "Indian Rupee", "code": "INR", "symbol": "₹"},
            {"name": "US Dollar", "code": "USD", "symbol": "$"},
            {"name": "Euro", "code": "EUR", "symbol": "€"}
        ]
        
        for currency_data in currencies_data:
            existing = await db.mst_currencies.find_one({"code": currency_data["code"]})
            if not existing:
                currency_record = {
                    "id": str(uuid.uuid4()),
                    **currency_data,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
                await db.mst_currencies.insert_one(currency_record)
                print(f"Inserted currency: {currency_data['name']}")

        # Initialize Primary Categories
        categories_data = [
            {"category_name": "Software Development", "category_code": "SW", "description": "Custom software development and applications"},
            {"category_name": "Hardware Solutions", "category_code": "HW", "description": "Hardware procurement and installation"},
            {"category_name": "Consulting Services", "category_code": "CS", "description": "IT consulting and advisory services"},
            {"category_name": "Support & Maintenance", "category_code": "SM", "description": "Ongoing support and maintenance services"}
        ]
        
        for category_data in categories_data:
            existing = await db.mst_primary_categories.find_one({"category_code": category_data["category_code"]})
            if not existing:
                category_record = {
                    "id": str(uuid.uuid4()),
                    **category_data,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
                await db.mst_primary_categories.insert_one(category_record)
                print(f"Inserted category: {category_data['category_name']}")

        # Initialize Products
        products_data = [
            {"name": "CRM System", "category_id": None, "description": "Customer Relationship Management solution"},
            {"name": "ERP Solution", "category_id": None, "description": "Enterprise Resource Planning system"},
            {"name": "Mobile Application", "category_id": None, "description": "Custom mobile app development"},
            {"name": "Web Portal", "category_id": None, "description": "Web-based portal and dashboard"},
            {"name": "Cloud Migration", "category_id": None, "description": "Cloud infrastructure and migration services"}
        ]
        
        # Get software category ID for products
        sw_category = await db.mst_primary_categories.find_one({"category_code": "SW"})
        sw_category_id = sw_category["id"] if sw_category else None
        
        for product_data in products_data:
            existing = await db.mst_products.find_one({"name": product_data["name"]})
            if not existing:
                product_record = {
                    "id": str(uuid.uuid4()),
                    "category_id": sw_category_id,
                    **product_data,
                    "created_by": "system",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
                await db.mst_products.insert_one(product_record)
                print(f"Inserted product: {product_data['name']}")

        print("✅ Opportunity management master data initialization completed")
        
    except Exception as e:
        print(f"❌ Error initializing opportunity master data: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# ================ COMPANY REGISTRATION MODELS ================

class CompanyType(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True

class AccountType(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True

class Region(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True

class BusinessType(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True

class Industry(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True

class SubIndustry(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    industry_id: str
    is_active: bool = True

class Country(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=3)
    is_active: bool = True

class State(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    country_id: str
    is_active: bool = True

class City(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    state_id: str
    is_active: bool = True

class Currency(BaseAuditModel):
    code: str = Field(..., min_length=3, max_length=3)
    name: str = Field(..., min_length=2, max_length=100)
    symbol: str = Field(..., max_length=5)
    is_active: bool = True

class CompanyTurnover(BaseModel):
    year: int = Field(..., ge=2000, le=2030)
    revenue: float = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)

class CompanyProfit(BaseModel):
    year: int = Field(..., ge=2000, le=2030)
    profit: float
    currency: str = Field(..., min_length=3, max_length=3)

class CompanyDocument(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Company(BaseAuditModel):
    # General Info
    name: str = Field(..., min_length=3, max_length=100)
    domestic_international: str = Field(..., pattern=r"^(Domestic|International)$")
    gst_number: Optional[str] = Field(None, max_length=15)
    pan_number: Optional[str] = Field(None, max_length=10)
    vat_number: Optional[str] = Field(None, max_length=20)
    company_type_id: str
    account_type_id: str
    region_id: str
    business_type_id: str
    industry_id: str
    sub_industry_id: str
    website: Optional[str] = None
    is_child: bool = False
    parent_company_id: Optional[str] = None
    employee_count: int = Field(..., ge=1)
    
    # Location
    address: str = Field(..., min_length=10, max_length=500)
    country_id: str
    state_id: str
    city_id: str
    
    # Financials
    turnover: List[CompanyTurnover] = []
    profit: List[CompanyProfit] = []
    annual_revenue: float = Field(..., ge=0)
    revenue_currency: str = Field(..., min_length=3, max_length=3)
    
    # Documents & Profile
    company_profile: Optional[str] = None
    documents: List[CompanyDocument] = []
    
    # Scoring & Lead Status
    score: int = Field(default=0, ge=0, le=100)
    lead_status: str = Field(default="cold", pattern=r"^(hot|cold)$")
    
    # Checklist validation
    valid_gst: bool = False
    active_status: bool = True
    parent_linkage_valid: bool = True

class CompanyCreate(BaseModel):
    # General Info
    company_name: str = Field(..., min_length=3, max_length=100)
    domestic_international: str = Field(..., pattern=r"^(Domestic|International)$")
    gst_number: Optional[str] = Field(None, max_length=15)
    pan_number: Optional[str] = Field(None, max_length=10)
    vat_number: Optional[str] = Field(None, max_length=20)
    company_type_id: str
    account_type_id: str
    region_id: str
    business_type_id: str
    industry_id: str
    sub_industry_id: str
    website: Optional[str] = None
    is_child: bool = False
    parent_company_id: Optional[str] = None
    employee_count: int = Field(..., ge=1)
    
    # Location
    address: str = Field(..., min_length=10, max_length=500)
    country_id: str
    state_id: str
    city_id: str
    
    # Financials
    turnover: List[CompanyTurnover] = []
    profit: List[CompanyProfit] = []
    annual_revenue: float = Field(..., ge=0)
    revenue_currency: str = Field(..., min_length=3, max_length=3)
    
    # Documents & Profile
    company_profile: Optional[str] = None
    
    # Checklist validation
    valid_gst: bool = False
    active_status: bool = True
    parent_linkage_valid: bool = True

# ================ COMPANY REGISTRATION ENDPOINTS ================

# Master data endpoints
@api_router.get("/company-types")
async def get_company_types(current_user: User = Depends(get_current_user)):
    types = await db.company_types.find({"is_active": True}).to_list(None)
    return [prepare_for_json(t) for t in types]

@api_router.get("/account-types")
async def get_account_types(current_user: User = Depends(get_current_user)):
    types = await db.account_types.find({"is_active": True}).to_list(None)
    return [prepare_for_json(t) for t in types]

@api_router.get("/regions")
async def get_regions(current_user: User = Depends(get_current_user)):
    regions = await db.regions.find({"is_active": True}).to_list(None)
    return [prepare_for_json(r) for r in regions]

@api_router.get("/business-types")
async def get_business_types(current_user: User = Depends(get_current_user)):
    types = await db.business_types.find({"is_active": True}).to_list(None)
    return [prepare_for_json(t) for t in types]

@api_router.get("/industries")
async def get_industries(current_user: User = Depends(get_current_user)):
    industries = await db.industries.find({"is_active": True}).to_list(None)
    return [prepare_for_json(i) for i in industries]

@api_router.get("/sub-industries")
async def get_sub_industries(industry_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_active": True}
    if industry_id:
        query["industry_id"] = industry_id
    sub_industries = await db.sub_industries.find(query).to_list(None)
    return [prepare_for_json(si) for si in sub_industries]

@api_router.get("/countries")
async def get_countries(current_user: User = Depends(get_current_user)):
    countries = await db.countries.find({"is_active": True}).to_list(None)
    return [prepare_for_json(c) for c in countries]

@api_router.get("/states")
async def get_states(country_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_active": True}
    if country_id:
        query["country_id"] = country_id
    states = await db.states.find(query).to_list(None)
    return [prepare_for_json(s) for s in states]

@api_router.get("/cities")
async def get_cities(state_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_active": True}
    if state_id:
        query["state_id"] = state_id
    cities = await db.cities.find(query).to_list(None)
    return [prepare_for_json(c) for c in cities]

@api_router.get("/currencies")
async def get_currencies(current_user: User = Depends(get_current_user)):
    currencies = await db.currencies.find({"is_active": True}).to_list(None)
    return [prepare_for_json(c) for c in currencies]

# Company CRUD endpoints with RBAC
async def check_company_access(current_user: User):
    """Check if user has access to company operations (Admin or Sales Executive)"""
    user_permissions = await get_user_permissions(current_user.id)
    has_company_access = any(
        p.get("module") == "Sales" and p.get("menu") == "Companies" and p.get("permission") in ["View", "Add", "Edit"]
        for p in user_permissions
    )
    if not has_company_access:
        raise HTTPException(status_code=403, detail="Access denied. Only Admins and Sales Executives can access companies.")
    return True

@api_router.get("/companies")
async def get_companies(current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    companies = await db.companies.find({"$or": [{"is_active": True}, {"active_status": True}]}).to_list(None)
    return [prepare_for_json(c) for c in companies]

@api_router.get("/companies/{company_id}")
async def get_company(company_id: str, current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    company = await db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return prepare_for_json(company)

@api_router.post("/companies")
async def create_company(company_data: CompanyCreate, current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    
    # Check for duplicates
    existing = await db.companies.find_one({
        "$or": [
            {"company_name": company_data.company_name},
            {"gst_number": company_data.gst_number} if company_data.gst_number else {},
            {"pan_number": company_data.pan_number} if company_data.pan_number else {},
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Company with this name, GST, or PAN already exists")
    
    # Validate India-specific requirements
    if company_data.domestic_international == "Domestic":
        if not company_data.gst_number and not company_data.pan_number:
            raise HTTPException(status_code=400, detail="GST or PAN number is required for domestic companies")
    
    # Calculate score and lead status
    score = await calculate_company_score(company_data)
    lead_status = "hot" if score >= 70 else "cold"
    
    logger.info(f"Creating company: {company_data.company_name}, Score: {score}, Lead Status: {lead_status}")
    
    # Map CompanyCreate fields to Company model fields
    company_dict = {
        # Use company_name as name for the Company model
        "name": company_data.company_name,
        "domestic_international": company_data.domestic_international,
        "gst_number": company_data.gst_number,
        "pan_number": company_data.pan_number,
        "vat_number": company_data.vat_number,
        "company_type_id": company_data.company_type_id,
        "account_type_id": company_data.account_type_id,
        "region_id": company_data.region_id,
        "business_type_id": company_data.business_type_id,
        "industry_id": company_data.industry_id,
        "sub_industry_id": company_data.sub_industry_id,
        "website": company_data.website,
        "is_child": company_data.is_child,
        "parent_company_id": company_data.parent_company_id,
        "employee_count": company_data.employee_count,
        "address": company_data.address,
        "country_id": company_data.country_id,
        "state_id": company_data.state_id,
        "city_id": company_data.city_id,
        "turnover": [t.dict() for t in company_data.turnover],
        "profit": [p.dict() for p in company_data.profit],
        "annual_revenue": company_data.annual_revenue,
        "revenue_currency": company_data.revenue_currency,
        "company_profile": company_data.company_profile,
        "documents": [],
        "score": score,
        "lead_status": lead_status,
        "valid_gst": company_data.valid_gst,
        "active_status": company_data.active_status,
        "is_active": True,  # Add is_active for compatibility
        "parent_linkage_valid": company_data.parent_linkage_valid,
        "created_by": current_user.id,
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Remove only specific None values that should not be stored
    fields_to_remove_if_none = ['gst_number', 'pan_number', 'vat_number', 'website', 'parent_company_id', 'company_profile']
    for field in fields_to_remove_if_none:
        if company_dict.get(field) is None:
            company_dict.pop(field, None)
    
    await db.companies.insert_one(company_dict)
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="CREATE",
        resource_type="Company",
        resource_id=company_dict["id"],
        details=f"Created company: {company_dict['name']}"
    )
    
    # Log email notification attempt
    logger.info(f"Email notification attempt: New company '{company_dict['name']}' created by {current_user.username}")
    
    return prepare_for_json(company_dict)

@api_router.put("/companies/{company_id}")
async def update_company(company_id: str, company_data: CompanyCreate, current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    
    # Check if company exists
    existing_company = await db.companies.find_one({"id": company_id})
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check for duplicates (excluding current company)
    existing = await db.companies.find_one({
        "$and": [
            {"id": {"$ne": company_id}},
            {"$or": [
                {"name": company_data.company_name},
                {"gst_number": company_data.gst_number} if company_data.gst_number else {},
                {"pan_number": company_data.pan_number} if company_data.pan_number else {},
            ]}
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Company with this name, GST, or PAN already exists")
    
    # Validate India-specific requirements
    if company_data.domestic_international == "Domestic":
        if not company_data.gst_number and not company_data.pan_number:
            raise HTTPException(status_code=400, detail="GST or PAN number is required for domestic companies")
    
    # Calculate score and lead status
    score = await calculate_company_score(company_data)
    lead_status = "hot" if score >= 70 else "cold"
    
    # Map CompanyCreate fields to Company model fields
    update_dict = {
        "name": company_data.company_name,
        "domestic_international": company_data.domestic_international,
        "gst_number": company_data.gst_number,
        "pan_number": company_data.pan_number,
        "vat_number": company_data.vat_number,
        "company_type_id": company_data.company_type_id,
        "account_type_id": company_data.account_type_id,
        "region_id": company_data.region_id,
        "business_type_id": company_data.business_type_id,
        "industry_id": company_data.industry_id,
        "sub_industry_id": company_data.sub_industry_id,
        "website": company_data.website,
        "is_child": company_data.is_child,
        "parent_company_id": company_data.parent_company_id,
        "employee_count": company_data.employee_count,
        "address": company_data.address,
        "country_id": company_data.country_id,
        "state_id": company_data.state_id,
        "city_id": company_data.city_id,
        "turnover": [t.dict() for t in company_data.turnover],
        "profit": [p.dict() for p in company_data.profit],
        "annual_revenue": company_data.annual_revenue,
        "revenue_currency": company_data.revenue_currency,
        "company_profile": company_data.company_profile,
        "score": score,
        "lead_status": lead_status,
        "valid_gst": company_data.valid_gst,
        "active_status": company_data.active_status,
        "parent_linkage_valid": company_data.parent_linkage_valid,
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Remove specific None values that should not be stored
    fields_to_remove_if_none = ['gst_number', 'pan_number', 'vat_number', 'website', 'parent_company_id', 'company_profile']
    for field in fields_to_remove_if_none:
        if update_dict.get(field) is None:
            update_dict.pop(field, None)
    
    await db.companies.update_one({"id": company_id}, {"$set": update_dict})
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="UPDATE",
        resource_type="Company",
        resource_id=company_id,
        details=f"Updated company: {update_dict['name']}"
    )
    
    # Get updated company
    updated_company = await db.companies.find_one({"id": company_id})
    return prepare_for_json(updated_company)

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    
    # Check if company exists
    company = await db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Soft delete - mark as inactive
    await db.companies.update_one(
        {"id": company_id}, 
        {
            "$set": {
                "is_active": False,
                "active_status": False,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="DELETE",
        resource_type="Company",
        resource_id=company_id,
        details=f"Deleted company: {company.get('name', 'Unknown')}"
    )
    
    return {"message": "Company deleted successfully"}

async def calculate_company_score(company_data: CompanyCreate) -> int:
    """Calculate company score based on various factors"""
    score = 0
    
    try:
        # Industry score (40 points)
        industry = await db.industries.find_one({"id": company_data.industry_id})
        if industry:
            # High-value industries get more points
            high_value_industries = ["Technology", "Finance", "Healthcare", "Manufacturing"]
            if industry.get("name") in high_value_industries:
                score += 40
            else:
                score += 20
        
        # Sub-industry score (20 points)
        sub_industry = await db.sub_industries.find_one({"id": company_data.sub_industry_id})
        if sub_industry:
            score += 20
        
        # Revenue score (25 points)
        if company_data.annual_revenue >= 10000000:  # 10M+
            score += 25
        elif company_data.annual_revenue >= 1000000:  # 1M+
            score += 15
        elif company_data.annual_revenue >= 100000:  # 100K+
            score += 10
        else:
            score += 5
        
        # Employee count score (15 points)
        if company_data.employee_count >= 1000:
            score += 15
        elif company_data.employee_count >= 100:
            score += 12
        elif company_data.employee_count >= 50:
            score += 8
        else:
            score += 5
        
        logger.info(f"Calculated score: {score} for company: {company_data.company_name}")
        return min(score, 100)  # Cap at 100
    except Exception as e:
        logger.error(f"Error calculating company score: {e}")
        return 0

# File upload endpoint
@api_router.post("/companies/upload-document")
async def upload_company_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    
    # Validate file
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                     "image/png", "image/jpeg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed. Only PDF, DOCX, PNG, JPG are supported")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/company_documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    document = CompanyDocument(
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type
    )
    
    return document.dict()

# Export companies
@api_router.get("/companies/export")
async def export_companies(current_user: User = Depends(get_current_user)):
    await check_company_access(current_user)
    
    # Check export permission
    user_permissions = await get_user_permissions(current_user.id)
    has_export = any(
        p.get("module") == "Sales" and p.get("menu") == "Companies" and p.get("permission") == "Export"
        for p in user_permissions
    )
    if not has_export:
        raise HTTPException(status_code=403, detail="Export permission required")
    
    companies = await db.companies.find().to_list(None)
    return [prepare_for_json(c) for c in companies]

# ================ CONTACT MANAGEMENT MODELS ================

class Designation(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True

class Contact(BaseAuditModel):
    # Basic Info
    company_id: str = Field(..., description="Reference to company")
    salutation: str = Field(..., pattern=r"^(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.)$")
    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    
    # Contact Details
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    primary_phone: str = Field(..., min_length=10, max_length=15, pattern=r'^\+?[\d\s\-\(\)]{10,15}$')
    designation_id: Optional[str] = None
    decision_maker: bool = Field(default=False)
    spoc: bool = Field(default=False, description="Single Point of Contact")
    
    # Additional Info
    address: Optional[str] = Field(None, max_length=500)
    country_id: Optional[str] = None
    city_id: Optional[str] = None
    comments: Optional[str] = Field(None, max_length=500)
    option: Optional[str] = Field(None, max_length=100, description="Preferred contact method")
    
    # Status fields
    is_active: bool = Field(default=True)
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

class ContactCreate(BaseModel):
    # Basic Info
    company_id: str = Field(..., description="Reference to company")
    salutation: str = Field(..., pattern=r"^(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.)$")
    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    
    # Contact Details
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    primary_phone: str = Field(..., min_length=10, max_length=15, pattern=r'^\+?[\d\s\-\(\)]{10,15}$')
    designation_id: Optional[str] = None
    decision_maker: bool = Field(default=False)
    spoc: bool = Field(default=False)
    
    # Additional Info
    address: Optional[str] = Field(None, max_length=500)
    country_id: Optional[str] = None
    city_id: Optional[str] = None
    comments: Optional[str] = Field(None, max_length=500)
    option: Optional[str] = Field(None, max_length=100)

class ContactUpdate(BaseModel):
    # Basic Info
    company_id: Optional[str] = None
    salutation: Optional[str] = Field(None, pattern=r"^(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.)$")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    
    # Contact Details
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    primary_phone: Optional[str] = Field(None, min_length=10, max_length=15, pattern=r'^\+?[\d\s\-\(\)]{10,15}$')
    designation_id: Optional[str] = None
    decision_maker: Optional[bool] = None
    spoc: Optional[bool] = None
    
    # Additional Info
    address: Optional[str] = Field(None, max_length=500)
    country_id: Optional[str] = None
    city_id: Optional[str] = None
    comments: Optional[str] = Field(None, max_length=500)
    option: Optional[str] = Field(None, max_length=100)
    
    # Status fields
    is_active: Optional[bool] = None

class ContactBulkUpdate(BaseModel):
    contact_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., pattern=r"^(activate|deactivate)$")

# ================ CONTACT MANAGEMENT ENDPOINTS ================

# Helper function for contact access control
async def check_contact_access(current_user: User):
    """Check if user has access to contact operations"""
    user_permissions = await get_user_permissions(current_user.id)
    has_contact_access = any(
        p.get("module") == "Sales" and p.get("menu") == "Contacts" and p.get("permission") in ["View", "Add", "Edit"]
        for p in user_permissions
    )
    if not has_contact_access:
        raise HTTPException(status_code=403, detail="Access denied. Permission required.")
    return True

# Contact similarity matching for duplicate detection
def calculate_contact_similarity(contact1: dict, contact2: dict) -> float:
    """Calculate similarity score between two contacts (0-1 scale)"""
    score = 0.0
    
    # Email similarity (40% weight)
    if contact1.get('email', '').lower() == contact2.get('email', '').lower():
        score += 0.4
    
    # Name similarity (40% weight)
    name1 = f"{contact1.get('first_name', '')} {contact1.get('last_name', '')}".strip().lower()
    name2 = f"{contact2.get('first_name', '')} {contact2.get('last_name', '')}".strip().lower()
    
    if name1 and name2:
        # Simple string similarity
        if name1 == name2:
            score += 0.4
        elif len(name1) > 0 and len(name2) > 0:
            # Check for partial matches
            words1 = set(name1.split())
            words2 = set(name2.split())
            common_words = words1.intersection(words2)
            if common_words:
                score += 0.2 * (len(common_words) / max(len(words1), len(words2)))
    
    # Company similarity (20% weight)
    if contact1.get('company_id') == contact2.get('company_id'):
        score += 0.2
    
    return score

async def detect_duplicate_contacts(contact_data: ContactCreate, exclude_id: str = None) -> List[dict]:
    """Detect potential duplicate contacts using similarity matching"""
    # Build query to find similar contacts
    query = {
        "is_deleted": {"$ne": True},
        "$or": [
            {"email": {"$regex": f"^{contact_data.email}$", "$options": "i"}},
            {
                "$and": [
                    {"first_name": {"$regex": f"^{contact_data.first_name}$", "$options": "i"}},
                    {"company_id": contact_data.company_id}
                ]
            }
        ]
    }
    
    if exclude_id:
        query["id"] = {"$ne": exclude_id}
    
    potential_duplicates = await db.contacts.find(query).to_list(None)
    
    # Calculate similarity scores
    duplicates = []
    for existing_contact in potential_duplicates:
        similarity = calculate_contact_similarity(contact_data.dict(), existing_contact)
        if similarity >= 0.6:  # 60% similarity threshold
            duplicates.append({
                "contact": prepare_for_json(existing_contact),
                "similarity": similarity
            })
    
    return duplicates

# Contact CRUD endpoints
@api_router.get("/contacts")
async def get_contacts(
    company_id: Optional[str] = None,
    designation_id: Optional[str] = None,
    spoc: Optional[bool] = None,
    decision_maker: Optional[bool] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user)
):
    await check_contact_access(current_user)
    
    # Build query
    query = {"is_deleted": {"$ne": True}}
    
    if company_id:
        query["company_id"] = company_id
    if designation_id:
        query["designation_id"] = designation_id
    if spoc is not None:
        query["spoc"] = spoc
    if decision_maker is not None:
        query["decision_maker"] = decision_maker
    if is_active is not None:
        query["is_active"] = is_active
    
    # Search functionality
    if search:
        search_pattern = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"first_name": search_pattern},
            {"last_name": search_pattern},
            {"email": search_pattern}
        ]
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get total count
    total = await db.contacts.count_documents(query)
    
    # Get contacts with sorting
    sort_direction = 1 if sort_order == "asc" else -1
    contacts = await db.contacts.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit).to_list(None)
    
    return {
        "contacts": [prepare_for_json(c) for c in contacts],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@api_router.get("/contacts/export")
async def export_contacts(
    company_id: Optional[str] = None,
    designation_id: Optional[str] = None,
    spoc: Optional[bool] = None,
    decision_maker: Optional[bool] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    await check_contact_access(current_user)
    
    # Check export permission
    user_permissions = await get_user_permissions(current_user.id)
    has_export = any(
        p.get("module") == "Sales" and p.get("menu") == "Contacts" and p.get("permission") == "Export"
        for p in user_permissions
    )
    if not has_export:
        raise HTTPException(status_code=403, detail="Export permission required")
    
    # Build query (same as get_contacts)
    query = {"is_deleted": {"$ne": True}}
    
    if company_id:
        query["company_id"] = company_id
    if designation_id:
        query["designation_id"] = designation_id
    if spoc is not None:
        query["spoc"] = spoc
    if decision_maker is not None:
        query["decision_maker"] = decision_maker
    if is_active is not None:
        query["is_active"] = is_active
    
    contacts = await db.contacts.find(query).to_list(None)
    return [prepare_for_json(c) for c in contacts]

# ================ LEAD MANAGEMENT MODELS ================

class Partner(BaseAuditModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone_number: str = Field(..., min_length=10, max_length=15, pattern=r'^\+?[\d\s\-\(\)]{10,15}$')
    is_active: bool = Field(default=True)

class PartnerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone_number: str = Field(..., min_length=10, max_length=15, pattern=r'^\+?[\d\s\-\(\)]{10,15}$')
    is_active: bool = Field(default=True)

class ProductService(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class SubTenderType(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class ProductServiceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class ProductServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class SubTenderTypeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class SubTenderTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class LeadDocument(BaseModel):
    document_type: str = Field(..., max_length=100)
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    description: Optional[str] = Field(None, max_length=200)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeadProof(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Lead(BaseAuditModel):
    # Auto-generated Lead ID
    lead_id: str = Field(..., pattern=r'^LEAD-[A-Z0-9]{7}$')
    
    # General Info
    tender_type: str = Field(..., pattern=r'^(Tender|Pre-Tender|Non-Tender)$')
    billing_type: Optional[str] = Field(None, pattern=r'^(prepaid|postpaid)$')
    sub_tender_type_id: Optional[str] = None
    project_title: str = Field(..., min_length=2, max_length=200)
    company_id: str = Field(..., description="Reference to company")
    state: str = Field(..., max_length=100)
    partner_id: Optional[str] = None
    
    # Lead Details
    lead_subtype: str = Field(..., pattern=r'^(Direct|Referral)$')
    source: str = Field(..., max_length=100)
    product_service_id: str = Field(..., description="Reference to product/service")
    is_enquiry: Optional[bool] = Field(default=False)
    billing_type: Optional[str] = Field(None, pattern=r'^(prepaid|postpaid)$')
    expected_orc: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    competitors: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="New", pattern=r'^(New|Nurturing|Converted)$')
    lead_owner: str = Field(..., description="User ID of lead owner")
    approval_status: str = Field(default="Pending", pattern=r'^(Pending|Approved|Rejected|Escalated)$')
    
    # Proofs & Documents
    proofs: List[LeadProof] = []
    documents: List[LeadDocument] = []
    checklist_completed: Optional[bool] = Field(default=False)
    
    # Conversion
    opportunity_date: Optional[datetime] = None
    opportunity_id: Optional[str] = None  # Reference to created opportunity
    converted_to_opportunity: bool = Field(default=False)
    
    # Status fields
    is_active: bool = Field(default=True)
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

class LeadCreate(BaseModel):
    # General Info (lead_id will be auto-generated)
    tender_type: str = Field(..., pattern=r'^(Tender|Pre-Tender|Non-Tender)$')
    billing_type: Optional[str] = Field(None, pattern=r'^(prepaid|postpaid)$')
    sub_tender_type_id: Optional[str] = None
    project_title: str = Field(..., min_length=2, max_length=200)
    company_id: str = Field(..., description="Reference to company")
    state: str = Field(..., max_length=100)
    partner_id: Optional[str] = None
    
    # Lead Details
    lead_subtype: str = Field(..., pattern=r'^(Direct|Referral)$')
    source: str = Field(..., max_length=100)
    product_service_id: str = Field(..., description="Reference to product/service")
    is_enquiry: Optional[bool] = Field(default=False)
    expected_orc: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    competitors: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="New", pattern=r'^(New|Nurturing|Converted)$')
    lead_owner: str = Field(..., description="User ID of lead owner")
    approval_status: str = Field(default="Pending", pattern=r'^(Pending|Approved|Rejected|Escalated)$')
    
    # Checklist
    checklist_completed: Optional[bool] = Field(default=False)

class LeadUpdate(BaseModel):
    # Allow partial updates
    tender_type: Optional[str] = Field(None, pattern=r'^(Tender|Pre-Tender|Non-Tender)$')
    sub_tender_type_id: Optional[str] = None
    project_title: Optional[str] = Field(None, min_length=2, max_length=200)
    company_id: Optional[str] = None
    state: Optional[str] = Field(None, max_length=100)
    partner_id: Optional[str] = None
    lead_subtype: Optional[str] = Field(None, pattern=r'^(Direct|Referral)$')
    source: Optional[str] = Field(None, max_length=100)
    product_service_id: Optional[str] = None
    is_enquiry: Optional[bool] = None
    billing_type: Optional[str] = Field(None, pattern=r'^(prepaid|postpaid)$')
    expected_orc: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    competitors: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern=r'^(New|Nurturing|Converted)$')
    lead_owner: Optional[str] = None
    approval_status: Optional[str] = Field(None, pattern=r'^(Pending|Approved|Rejected|Escalated)$')
    checklist_completed: Optional[bool] = None
    opportunity_date: Optional[datetime] = None

class LeadKPIs(BaseModel):
    total_leads: int
    pending_leads: int
    approved_leads: int
    escalated_leads: int

# ================ LEAD MANAGEMENT ENDPOINTS ================

# Helper function for lead access control
async def check_lead_access(current_user: User):
    """Check if user has access to lead operations"""
    user_permissions = await get_user_permissions(current_user.id)
    has_lead_access = any(
        p.get("module") == "Sales" and p.get("menu") == "Leads" and p.get("permission") in ["View", "Add", "Edit"]
        for p in user_permissions
    )
    if not has_lead_access:
        raise HTTPException(status_code=403, detail="Access denied. Permission required.")
    return True

# Helper function to generate unique Lead ID
async def generate_lead_id() -> str:
    """Generate unique LEAD-XXXXXXX format ID"""
    import random
    import string
    
    while True:
        # Generate 7 character alphanumeric string
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        lead_id = f"LEAD-{suffix}"
        
        # Check if it already exists
        existing = await db.leads.find_one({"lead_id": lead_id})
        if not existing:
            return lead_id

# Partner CRUD endpoints
@api_router.get("/partners")
async def get_partners(current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    partners = await db.partners.find({"is_active": True}).to_list(None)
    return [prepare_for_json(p) for p in partners]

@api_router.get("/partners/{partner_id}")
async def get_partner(partner_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    partner = await db.partners.find_one({"id": partner_id, "is_active": True})
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return prepare_for_json(partner)

@api_router.post("/partners")
async def create_partner(partner_data: PartnerCreate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check email uniqueness
    existing_email = await db.partners.find_one({
        "email": {"$regex": f"^{partner_data.email}$", "$options": "i"},
        "is_active": True
    })
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    try:
        partner_dict = {
            **partner_data.dict(),
            "id": str(uuid.uuid4()),
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.partners.insert_one(partner_dict)
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CREATE",
            resource_type="Partner",
            resource_id=partner_dict["id"],
            details=f"Created partner: {partner_dict['first_name']} {partner_dict['last_name']}"
        )
        
        return prepare_for_json(partner_dict)
        
    except Exception as e:
        logger.error(f"Failed to create partner: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create partner")

@api_router.put("/partners/{partner_id}")
async def update_partner(partner_id: str, partner_data: PartnerCreate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if partner exists
    existing_partner = await db.partners.find_one({"id": partner_id, "is_active": True})
    if not existing_partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    # Check email uniqueness (excluding current partner)
    existing_email = await db.partners.find_one({
        "email": {"$regex": f"^{partner_data.email}$", "$options": "i"},
        "id": {"$ne": partner_id},
        "is_active": True
    })
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    try:
        update_data = {
            **partner_data.dict(),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.partners.update_one(
            {"id": partner_id},
            {"$set": update_data}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="UPDATE",
            resource_type="Partner",
            resource_id=partner_id,
            details=f"Updated partner: {partner_data.first_name} {partner_data.last_name}"
        )
        
        updated_partner = await db.partners.find_one({"id": partner_id})
        return prepare_for_json(updated_partner)
        
    except Exception as e:
        logger.error(f"Failed to update partner: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update partner")

@api_router.delete("/partners/{partner_id}")
async def delete_partner(partner_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if partner exists
    partner = await db.partners.find_one({"id": partner_id, "is_active": True})
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    try:
        # Soft delete
        await db.partners.update_one(
            {"id": partner_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="DELETE",
            resource_type="Partner",
            resource_id=partner_id,
            details=f"Deleted partner: {partner['first_name']} {partner['last_name']}"
        )
        
        return {"message": "Partner deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete partner: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete partner")

# Product & Services CRUD endpoints
@api_router.get("/product-services")
async def get_product_services(current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    products = await db.product_services.find({"is_active": True}).to_list(None)
    return [prepare_for_json(p) for p in products]

@api_router.get("/product-services/{product_id}")
async def get_product_service(product_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    product = await db.product_services.find_one({"id": product_id, "is_active": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product/Service not found")
    return prepare_for_json(product)

@api_router.post("/product-services")
async def create_product_service(product_data: ProductServiceCreate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check name uniqueness
    existing_name = await db.product_services.find_one({
        "name": {"$regex": f"^{product_data.name}$", "$options": "i"},
        "is_active": True
    })
    if existing_name:
        raise HTTPException(status_code=400, detail="Product/Service name already exists")
    
    try:
        product_dict = {
            **product_data.dict(),
            "id": str(uuid.uuid4()),
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.product_services.insert_one(product_dict)
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CREATE",
            resource_type="ProductService",
            resource_id=product_dict["id"],
            details=f"Created product/service: {product_dict['name']}"
        )
        
        return prepare_for_json(product_dict)
        
    except Exception as e:
        logger.error(f"Failed to create product/service: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create product/service")

@api_router.put("/product-services/{product_id}")
async def update_product_service(product_id: str, product_data: ProductServiceUpdate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if product exists
    existing_product = await db.product_services.find_one({"id": product_id, "is_active": True})
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product/Service not found")
    
    # Check name uniqueness (excluding current product)
    if product_data.name:
        existing_name = await db.product_services.find_one({
            "name": {"$regex": f"^{product_data.name}$", "$options": "i"},
            "id": {"$ne": product_id},
            "is_active": True
        })
        if existing_name:
            raise HTTPException(status_code=400, detail="Product/Service name already exists")
    
    try:
        update_data = {k: v for k, v in product_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.product_services.update_one(
            {"id": product_id},
            {"$set": update_data}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="UPDATE",
            resource_type="ProductService",
            resource_id=product_id,
            details=f"Updated product/service: {product_data.name or existing_product['name']}"
        )
        
        updated_product = await db.product_services.find_one({"id": product_id})
        return prepare_for_json(updated_product)
        
    except Exception as e:
        logger.error(f"Failed to update product/service: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update product/service")

@api_router.delete("/product-services/{product_id}")
async def delete_product_service(product_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if product exists
    product = await db.product_services.find_one({"id": product_id, "is_active": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product/Service not found")
    
    # Check if product is being used in any leads
    leads_using_product = await db.leads.find_one({"product_service_id": product_id, "is_active": True})
    if leads_using_product:
        raise HTTPException(status_code=400, detail="Cannot delete product/service as it is being used in leads")
    
    try:
        # Soft delete
        await db.product_services.update_one(
            {"id": product_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="DELETE",
            resource_type="ProductService",
            resource_id=product_id,
            details=f"Deleted product/service: {product['name']}"
        )
        
        return {"message": "Product/Service deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete product/service: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete product/service")

# Sub-Tender Types CRUD endpoints
@api_router.get("/sub-tender-types")
async def get_sub_tender_types(current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    sub_tenders = await db.sub_tender_types.find({"is_active": True}).to_list(None)
    return [prepare_for_json(st) for st in sub_tenders]

@api_router.get("/sub-tender-types/{sub_tender_id}")
async def get_sub_tender_type(sub_tender_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    sub_tender = await db.sub_tender_types.find_one({"id": sub_tender_id, "is_active": True})
    if not sub_tender:
        raise HTTPException(status_code=404, detail="Sub-Tender Type not found")
    return prepare_for_json(sub_tender)

@api_router.post("/sub-tender-types")
async def create_sub_tender_type(sub_tender_data: SubTenderTypeCreate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check name uniqueness
    existing_name = await db.sub_tender_types.find_one({
        "name": {"$regex": f"^{sub_tender_data.name}$", "$options": "i"},
        "is_active": True
    })
    if existing_name:
        raise HTTPException(status_code=400, detail="Sub-Tender Type name already exists")
    
    try:
        sub_tender_dict = {
            **sub_tender_data.dict(),
            "id": str(uuid.uuid4()),
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.sub_tender_types.insert_one(sub_tender_dict)
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CREATE",
            resource_type="SubTenderType",
            resource_id=sub_tender_dict["id"],
            details=f"Created sub-tender type: {sub_tender_dict['name']}"
        )
        
        return prepare_for_json(sub_tender_dict)
        
    except Exception as e:
        logger.error(f"Failed to create sub-tender type: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create sub-tender type")

@api_router.put("/sub-tender-types/{sub_tender_id}")
async def update_sub_tender_type(sub_tender_id: str, sub_tender_data: SubTenderTypeUpdate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if sub-tender type exists
    existing_sub_tender = await db.sub_tender_types.find_one({"id": sub_tender_id, "is_active": True})
    if not existing_sub_tender:
        raise HTTPException(status_code=404, detail="Sub-Tender Type not found")
    
    # Check name uniqueness (excluding current sub-tender type)
    if sub_tender_data.name:
        existing_name = await db.sub_tender_types.find_one({
            "name": {"$regex": f"^{sub_tender_data.name}$", "$options": "i"},
            "id": {"$ne": sub_tender_id},
            "is_active": True
        })
        if existing_name:
            raise HTTPException(status_code=400, detail="Sub-Tender Type name already exists")
    
    try:
        update_data = {k: v for k, v in sub_tender_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.sub_tender_types.update_one(
            {"id": sub_tender_id},
            {"$set": update_data}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="UPDATE",
            resource_type="SubTenderType",
            resource_id=sub_tender_id,
            details=f"Updated sub-tender type: {sub_tender_data.name or existing_sub_tender['name']}"
        )
        
        updated_sub_tender = await db.sub_tender_types.find_one({"id": sub_tender_id})
        return prepare_for_json(updated_sub_tender)
        
    except Exception as e:
        logger.error(f"Failed to update sub-tender type: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update sub-tender type")

@api_router.delete("/sub-tender-types/{sub_tender_id}")
async def delete_sub_tender_type(sub_tender_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if sub-tender type exists
    sub_tender = await db.sub_tender_types.find_one({"id": sub_tender_id, "is_active": True})
    if not sub_tender:
        raise HTTPException(status_code=404, detail="Sub-Tender Type not found")
    
    # Check if sub-tender type is being used in any leads
    leads_using_sub_tender = await db.leads.find_one({"sub_tender_type_id": sub_tender_id, "is_active": True})
    if leads_using_sub_tender:
        raise HTTPException(status_code=400, detail="Cannot delete sub-tender type as it is being used in leads")
    
    try:
        # Soft delete
        await db.sub_tender_types.update_one(
            {"id": sub_tender_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="DELETE",
            resource_type="SubTenderType",
            resource_id=sub_tender_id,
            details=f"Deleted sub-tender type: {sub_tender['name']}"
        )
        
        return {"message": "Sub-Tender Type deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete sub-tender type: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete sub-tender type")

# Lead CRUD endpoints
@api_router.get("/leads")
async def get_leads(
    company_id: Optional[str] = None,
    partner_id: Optional[str] = None,
    status: Optional[str] = None,
    tender_type: Optional[str] = None,
    sub_tender_type_id: Optional[str] = None,
    approval_status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user)
):
    await check_lead_access(current_user)
    
    # Build query
    query = {"is_deleted": {"$ne": True}}
    
    if company_id:
        query["company_id"] = company_id
    if partner_id:
        query["partner_id"] = partner_id
    if status:
        query["status"] = status
    if tender_type:
        query["tender_type"] = tender_type
    if sub_tender_type_id:
        query["sub_tender_type_id"] = sub_tender_type_id
    if approval_status:
        query["approval_status"] = approval_status
    
    # Search functionality
    if search:
        search_pattern = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"lead_id": search_pattern},
            {"project_title": search_pattern},
            {"competitors": search_pattern}
        ]
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get total count
    total = await db.leads.count_documents(query)
    
    # Get leads with sorting
    sort_direction = 1 if sort_order == "asc" else -1
    leads = await db.leads.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit).to_list(None)
    
    return {
        "leads": [prepare_for_json(l) for l in leads],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@api_router.get("/leads/kpis")
async def get_lead_kpis(current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Count leads by different statuses
    total_leads = await db.leads.count_documents({"is_active": True})
    pending_leads = await db.leads.count_documents({"approval_status": "Pending", "is_active": True})
    approved_leads = await db.leads.count_documents({"approval_status": "Approved", "is_active": True})
    escalated_leads = await db.leads.count_documents({"approval_status": "Escalated", "is_active": True})
    
    return {
        "total": total_leads,
        "pending": pending_leads,
        "approved": approved_leads,
        "escalated": escalated_leads
    }

@api_router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    lead = await db.leads.find_one({"id": lead_id, "is_deleted": {"$ne": True}})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return prepare_for_json(lead)

@api_router.post("/leads")
async def create_lead(lead_data: LeadCreate, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Generate unique Lead ID
    lead_id = await generate_lead_id()
    
    # Validate tender type logic
    if lead_data.tender_type in ["Tender", "Pre-Tender"]:
        if not lead_data.sub_tender_type_id:
            raise HTTPException(status_code=400, detail="Sub-Tender Type required for Tender and Pre-Tender leads")
        if not lead_data.billing_type:
            raise HTTPException(status_code=400, detail="Billing Type required for Tender and Pre-Tender leads")
        if not lead_data.expected_orc:
            raise HTTPException(status_code=400, detail="Expected ORC required for Tender and Pre-Tender leads")
    
    # Verify related entities exist
    company = await db.companies.find_one({
        "id": lead_data.company_id, 
        "$or": [{"is_active": True}, {"active_status": True}]
    })
    if not company:
        raise HTTPException(status_code=400, detail="Invalid company")
    
    if lead_data.partner_id:
        partner = await db.partners.find_one({"id": lead_data.partner_id, "is_active": True})
        if not partner:
            raise HTTPException(status_code=400, detail="Invalid partner")
    
    product_service = await db.product_services.find_one({"id": lead_data.product_service_id, "is_active": True})
    if not product_service:
        raise HTTPException(status_code=400, detail="Invalid product/service")
    
    if lead_data.sub_tender_type_id:
        sub_tender = await db.sub_tender_types.find_one({"id": lead_data.sub_tender_type_id, "is_active": True})
        if not sub_tender:
            raise HTTPException(status_code=400, detail="Invalid sub-tender type")
    
    # Check for conflicts (same project + company)
    existing_lead = await db.leads.find_one({
        "project_title": {"$regex": f"^{lead_data.project_title}$", "$options": "i"},
        "company_id": lead_data.company_id,
        "is_deleted": {"$ne": True}
    })
    if existing_lead:
        raise HTTPException(status_code=409, detail="Lead conflict detected. Escalated for review.")
    
    try:
        lead_dict = {
            **lead_data.dict(),
            "lead_id": lead_id,
            "id": str(uuid.uuid4()),
            "proofs": [],
            "documents": [],
            "converted_to_opportunity": False,
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "is_deleted": False
        }
        
        await db.leads.insert_one(lead_dict)
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CREATE",
            resource_type="Lead",
            resource_id=lead_dict["id"],
            details=f"Created lead: {lead_dict['lead_id']} - {lead_dict['project_title']}"
        )
        
        # Log email notification attempt
        logger.info(f"Email notification attempt: New lead '{lead_dict['lead_id']}' created by {current_user.username}")
        
        return prepare_for_json(lead_dict)
        
    except Exception as e:
        logger.error(f"Failed to create lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create lead")

@api_router.put("/leads/{lead_id}")
async def update_lead(
    lead_id: str, 
    lead_data: LeadUpdate, 
    current_user: User = Depends(get_current_user)
):
    await check_lead_access(current_user)
    
    # Check if lead exists
    existing_lead = await db.leads.find_one({"id": lead_id, "is_deleted": {"$ne": True}})
    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if lead is approved - approved leads cannot be edited
    if existing_lead.get("approval_status") == "Approved":
        raise HTTPException(status_code=400, detail="Approved leads cannot be edited")
    
    # Prepare update data (only include non-None values)
    update_data = {k: v for k, v in lead_data.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    # Validate tender type logic if being updated
    if "tender_type" in update_data or "sub_tender_type_id" in update_data:
        tender_type = update_data.get("tender_type", existing_lead.get("tender_type"))
        sub_tender_type_id = update_data.get("sub_tender_type_id", existing_lead.get("sub_tender_type_id"))
        billing_type = update_data.get("billing_type", existing_lead.get("billing_type"))
        expected_orc = update_data.get("expected_orc", existing_lead.get("expected_orc"))
        
        if tender_type in ["Tender", "Pre-Tender"]:
            if not sub_tender_type_id:
                raise HTTPException(status_code=400, detail="Sub-Tender Type required for Tender and Pre-Tender leads")
            if not billing_type:
                raise HTTPException(status_code=400, detail="Billing Type required for Tender and Pre-Tender leads")
            if not expected_orc:
                raise HTTPException(status_code=400, detail="Expected ORC required for Tender and Pre-Tender leads")
    
    # Validate related entities if being updated
    if "company_id" in update_data:
        company = await db.companies.find_one({
            "id": update_data["company_id"], 
            "$or": [{"is_active": True}, {"active_status": True}]
        })
        if not company:
            raise HTTPException(status_code=400, detail="Invalid company")
    
    if "partner_id" in update_data and update_data["partner_id"]:
        partner = await db.partners.find_one({"id": update_data["partner_id"], "is_active": True})
        if not partner:
            raise HTTPException(status_code=400, detail="Invalid partner")
    
    if "product_service_id" in update_data:
        product_service = await db.product_services.find_one({"id": update_data["product_service_id"], "is_active": True})
        if not product_service:
            raise HTTPException(status_code=400, detail="Invalid product/service")
    
    if "sub_tender_type_id" in update_data and update_data["sub_tender_type_id"]:
        sub_tender = await db.sub_tender_types.find_one({"id": update_data["sub_tender_type_id"], "is_active": True})
        if not sub_tender:
            raise HTTPException(status_code=400, detail="Invalid sub-tender type")
    
    try:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.leads.update_one(
            {"id": lead_id},
            {"$set": update_data}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="UPDATE",
            resource_type="Lead",
            resource_id=lead_id,
            details=f"Updated lead: {existing_lead['lead_id']} - {existing_lead['project_title']}"
        )
        
        # Get updated lead
        updated_lead = await db.leads.find_one({"id": lead_id})
        return prepare_for_json(updated_lead)
        
    except Exception as e:
        logger.error(f"Failed to update lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update lead")

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Check if lead exists
    lead = await db.leads.find_one({"id": lead_id, "is_deleted": {"$ne": True}})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        # Soft delete
        await db.leads.update_one(
            {"id": lead_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="DELETE",
            resource_type="Lead",
            resource_id=lead_id,
            details=f"Deleted lead: {lead['lead_id']} - {lead['project_title']}"
        )
        
        return {"message": "Lead deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete lead")

# Lead nurturing and conversion
# Lead Status Change endpoint
@api_router.post("/leads/{lead_id}/status")
async def change_lead_status(
    lead_id: str, 
    status_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Change lead status with opportunity conversion support"""
    await check_lead_access(current_user)
    
    try:
        # Get the lead
        lead = await db.leads.find_one({"id": lead_id, "is_active": True})
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        converted = False
        opportunity_id = None
        
        # Handle convert to opportunity
        if new_status == "convert_to_opp":
            if lead.get("approval_status") != "Approved":
                raise HTTPException(status_code=400, detail="Lead must be approved before conversion")
            
            # Generate opportunity ID in OPP-XXXXXXX format  
            opportunity_id = f"OPP-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=7))}"
            
            # Create opportunity with proper structure matching OpportunityBase model
            # Get default currency ID (INR)
            inr_currency = await db.mst_currencies.find_one({"currency_code": "INR"})
            currency_id = inr_currency["id"] if inr_currency else "default-inr-id"
            
            opportunity_data = {
                "id": opportunity_id,
                "project_title": lead.get("project_title", "Converted Opportunity"),
                "company_id": lead.get("company_id"),
                "lead_id": lead_id,
                "current_stage": 1,  # L1 - Prospect
                "status": "Active",
                "expected_revenue": float(lead.get("expected_orc", 0)),
                "currency_id": currency_id,
                "win_probability": 25.0,
                "weighted_revenue": float(lead.get("expected_orc", 0)) * 0.25,
                "lead_owner_id": lead.get("lead_owner"),
                "created_by": current_user.id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                # Stage history for audit trail
                "stage_history": [{
                    "from_stage": 0,
                    "to_stage": 1,
                    "changed_by": current_user.id,
                    "changed_at": datetime.now(timezone.utc),
                    "notes": "Initial stage after lead conversion"
                }]
            }
            
            await db.opportunities.insert_one(opportunity_data)
            
            # Update lead status
            await db.leads.update_one(
                {"id": lead_id},
                {
                    "$set": {
                        "status": "Converted",
                        "approval_status": "Approved",
                        "converted_to_opportunity": True,
                        "opportunity_date": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            converted = True
            
            # Log audit trail
            await log_audit_trail(
                user_id=current_user.id,
                action="CONVERT",
                resource_type="Lead",
                resource_id=lead_id,
                details=f"Converted lead to opportunity: {opportunity_id}"
            )
            
        elif new_status in ["approved", "Rejected"]:
            # Map to proper approval status
            approval_status = "Approved" if new_status == "approved" else "Rejected"
            
            await db.leads.update_one(
                {"id": lead_id},
                {
                    "$set": {
                        "approval_status": approval_status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Log audit trail
            await log_audit_trail(
                user_id=current_user.id,
                action="UPDATE",
                resource_type="Lead",
                resource_id=lead_id,
                details=f"Changed lead approval status to: {approval_status}"
            )
            
            # For approval/rejection, converted should be False
            converted = False
        else:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        # Get updated lead
        updated_lead = await db.leads.find_one({"id": lead_id})
        
        return {
            "success": True,
            "lead": prepare_for_json(updated_lead),
            "converted": converted,
            "opportunity_id": opportunity_id
        }
        
    except Exception as e:
        logger.error(f"Failed to change lead status: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to change lead status")

def generate_opportunity_id():
    """Generate opportunity ID in POT-XXXXXXXX format"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    suffix = ''.join(random.choices(chars, k=8))
    return f'POT-{suffix}'

@api_router.post("/leads/{lead_id}/nurture")

@api_router.post("/leads/{lead_id}/convert")
async def convert_lead_to_opportunity(
    lead_id: str, 
    opportunity_date: datetime,
    current_user: User = Depends(get_current_user)
):
    await check_lead_access(current_user)
    
    # Check if lead exists
    lead = await db.leads.find_one({"id": lead_id, "is_deleted": {"$ne": True}})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if lead is approved
    if lead.get("approval_status") != "Approved":
        raise HTTPException(status_code=400, detail="Only approved leads can be converted to opportunities")
    
    # Check if already converted
    if lead.get("converted_to_opportunity"):
        raise HTTPException(status_code=400, detail="Lead already converted to opportunity")
    
    if not opportunity_date:
        raise HTTPException(status_code=400, detail="Opportunity date required to convert lead")
    
    try:
        # Generate opportunity ID
        opportunity_id = f"OPP-{generate_id()}"
        
        # Get default currency (INR)
        default_currency = await db.mst_currencies.find_one({"code": "INR"})
        currency_id = default_currency["id"] if default_currency else None
        
        # Create opportunity data from lead
        opportunity_data = {
            "id": str(uuid.uuid4()),
            "opportunity_id": opportunity_id,
            "project_title": lead.get("project_title", f"Opportunity from Lead {lead.get('lead_id', '')}"),
            "company_id": lead.get("company_id"),
            "lead_id": lead_id,
            "current_stage": 1,  # L1 - Prospect
            "status": "Active",
            "expected_revenue": float(lead.get("expected_orc", 0) or lead.get("revenue", 0) or 0),
            "currency_id": currency_id,
            "win_probability": 25.0,  # Default for L1 stage
            "weighted_revenue": 0.0,
            
            # L1 - Prospect fields from lead data
            "region_id": None,  # Will be set in stage management
            "product_interest": f"Converted from lead. Original service: {lead.get('product_service_id', 'Not specified')}",
            "assigned_representatives": [current_user.id],
            "lead_owner_id": current_user.id,
            
            # Initialize empty stage data for future stages
            "scorecard": None,
            "budget": None,
            "authority": None,
            "need": None,
            "timeline": None,
            "qualification_status": None,
            "proposal_documents": [],
            "submission_date": None,
            "internal_stakeholder_id": None,
            "client_response": None,
            "selected_quotation_id": None,
            "updated_price": None,
            "margin": None,
            "cpc_overhead": None,
            "po_number": None,
            "po_date": None,
            "po_file": None,
            "final_value": None,
            "client_poc": None,
            "delivery_team": [],
            "kickoff_task": None,
            "lost_reason": None,
            "competitor_id": None,
            "followup_reminder": None,
            "internal_learning": None,
            "drop_reason": None,
            "reminder_date": None,
            
            # Locking and stage management
            "is_locked": False,
            "locked_stages": [],
            "stage_history": [{
                "from_stage": 0,
                "to_stage": 1,
                "changed_by": current_user.id,
                "changed_at": datetime.now(timezone.utc),
                "notes": f"Opportunity created from lead conversion. Original Lead ID: {lead.get('lead_id')}",
                "stage_data": {}
            }],
            
            # Audit fields
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Calculate weighted revenue
        opportunity_data["weighted_revenue"] = (opportunity_data["expected_revenue"] * opportunity_data["win_probability"]) / 100
        
        # Convert for MongoDB storage
        opportunity_data = prepare_for_mongo(opportunity_data)
        
        # Insert opportunity into database
        await db.opportunities.insert_one(opportunity_data)
        
        # Update lead status with opportunity reference
        await db.leads.update_one(
            {"id": lead_id},
            {
                "$set": {
                    "status": "Converted",
                    "converted_to_opportunity": True,
                    "opportunity_date": opportunity_date,
                    "opportunity_id": opportunity_id,  # Store reference to created opportunity
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CONVERT",
            resource_type="Lead",
            resource_id=lead_id,
            details=f"Converted lead to opportunity: {lead['lead_id']} -> {opportunity_id} - {lead.get('project_title', '')}"
        )
        
        # Log email notification attempt
        logger.info(f"Email notification attempt: Lead '{lead['lead_id']}' converted to opportunity {opportunity_id} by {current_user.username}")
        
        return {
            "message": "Lead converted to opportunity successfully",
            "opportunity_id": opportunity_id,
            "opportunity_uuid": opportunity_data["id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to convert lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to convert lead")

# File upload for lead proofs and documents
@api_router.post("/leads/upload-proof")
async def upload_lead_proof(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    await check_lead_access(current_user)
    
    # Validate file
    if file.size > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed. Only PDF, PNG, JPG are supported")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/lead_proofs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    proof = LeadProof(
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type
    )
    
    return proof.dict()

@api_router.post("/leads/upload-document")
async def upload_lead_document(
    file: UploadFile = File(...), 
    document_type: str = "",
    description: str = "",
    current_user: User = Depends(get_current_user)
):
    await check_lead_access(current_user)
    
    # Validate file
    if file.size > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                     "image/png", "image/jpeg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed. Only PDF, DOCX, PNG, JPG are supported")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/lead_documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    document = LeadDocument(
        document_type=document_type,
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        description=description
    )
    
    return document.dict()

# Export leads
@api_router.get("/leads/export")
async def export_leads(
    company_id: Optional[str] = None,
    partner_id: Optional[str] = None,
    status: Optional[str] = None,
    tender_type: Optional[str] = None,
    approval_status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    await check_lead_access(current_user)
    
    # Check export permission
    user_permissions = await get_user_permissions(current_user.id)
    has_export = any(
        p.get("module") == "Sales" and p.get("menu") == "Leads" and p.get("permission") == "Export"
        for p in user_permissions
    )
    if not has_export:
        raise HTTPException(status_code=403, detail="Export permission required")
    
    # Build query (same as get_leads)
    query = {"is_deleted": {"$ne": True}}
    
    if company_id:
        query["company_id"] = company_id
    if partner_id:
        query["partner_id"] = partner_id
    if status:
        query["status"] = status
    if tender_type:
        query["tender_type"] = tender_type
    if approval_status:
        query["approval_status"] = approval_status
    
    leads = await db.leads.find(query).to_list(None)
    return [prepare_for_json(l) for l in leads]

@api_router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    await check_contact_access(current_user)
    
    contact = await db.contacts.find_one({"id": contact_id, "is_deleted": {"$ne": True}})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return prepare_for_json(contact)

@api_router.post("/contacts")
async def create_contact(contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    await check_contact_access(current_user)
    
    # Check email uniqueness
    existing_email = await db.contacts.find_one({
        "email": {"$regex": f"^{contact_data.email}$", "$options": "i"},
        "is_deleted": {"$ne": True}
    })
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use.")
    
    # Check SPOC uniqueness per company
    if contact_data.spoc:
        existing_spoc = await db.contacts.find_one({
            "company_id": contact_data.company_id,
            "spoc": True,
            "is_deleted": {"$ne": True}
        })
        if existing_spoc:
            raise HTTPException(status_code=400, detail="Another contact is already SPOC for this company.")
    
    # Detect potential duplicates
    duplicates = await detect_duplicate_contacts(contact_data)
    if duplicates:
        raise HTTPException(status_code=400, detail="Possible duplicate contact detected. Review and confirm.")
    
    # Verify company exists
    company = await db.companies.find_one({
        "id": contact_data.company_id, 
        "$or": [{"is_active": True}, {"active_status": True}]
    })
    if not company:
        raise HTTPException(status_code=400, detail="Company not found or inactive")
    
    try:
        # Create contact
        contact_dict = {
            **contact_data.dict(),
            "id": str(uuid.uuid4()),
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "is_deleted": False
        }
        
        await db.contacts.insert_one(contact_dict)
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="CREATE",
            resource_type="Contact",
            resource_id=contact_dict["id"],
            details=f"Created contact: {contact_dict['first_name']} {contact_dict.get('last_name', '')} ({contact_dict['email']})"
        )
        
        return prepare_for_json(contact_dict)
        
    except Exception as e:
        logger.error(f"Failed to create contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save contact. Try again.")

@api_router.put("/contacts/{contact_id}")
async def update_contact(
    contact_id: str, 
    contact_data: ContactUpdate, 
    force_spoc_update: bool = False,
    current_user: User = Depends(get_current_user)
):
    await check_contact_access(current_user)
    
    # Check if contact exists
    existing_contact = await db.contacts.find_one({"id": contact_id, "is_deleted": {"$ne": True}})
    if not existing_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Prepare update data (only include non-None values)
    update_data = {k: v for k, v in contact_data.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    # Check email uniqueness if email is being updated
    if "email" in update_data:
        existing_email = await db.contacts.find_one({
            "email": {"$regex": f"^{update_data['email']}$", "$options": "i"},
            "id": {"$ne": contact_id},
            "is_deleted": {"$ne": True}
        })
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already in use.")
    
    # Check SPOC uniqueness if SPOC is being set to True
    if "spoc" in update_data and update_data["spoc"]:
        company_id = update_data.get("company_id", existing_contact["company_id"])
        existing_spoc = await db.contacts.find_one({
            "company_id": company_id,
            "spoc": True,
            "id": {"$ne": contact_id},
            "is_deleted": {"$ne": True}
        })
        
        if existing_spoc and not force_spoc_update:
            raise HTTPException(
                status_code=409, 
                detail={
                    "message": "Another contact is already SPOC for this company.",
                    "existing_spoc": prepare_for_json(existing_spoc),
                    "requires_confirmation": True
                }
            )
        elif existing_spoc and force_spoc_update:
            # Remove SPOC status from existing contact
            await db.contacts.update_one(
                {"id": existing_spoc["id"]},
                {"$set": {"spoc": False, "updated_at": datetime.now(timezone.utc)}}
            )
    
    # Detect potential duplicates if key fields are being updated
    if any(field in update_data for field in ["email", "first_name", "company_id"]):
        # Create a merged data object for duplicate detection
        merged_data = {**existing_contact, **update_data}
        contact_create_data = ContactCreate(**{k: v for k, v in merged_data.items() if k in ContactCreate.__fields__})
        
        duplicates = await detect_duplicate_contacts(contact_create_data, exclude_id=contact_id)
        if duplicates:
            raise HTTPException(status_code=400, detail="Possible duplicate contact detected. Review and confirm.")
    
    try:
        # Update contact
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.contacts.update_one(
            {"id": contact_id},
            {"$set": update_data}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="UPDATE",
            resource_type="Contact",
            resource_id=contact_id,
            details=f"Updated contact: {existing_contact['first_name']} {existing_contact.get('last_name', '')} ({existing_contact['email']})"
        )
        
        # Get updated contact
        updated_contact = await db.contacts.find_one({"id": contact_id})
        return prepare_for_json(updated_contact)
        
    except Exception as e:
        logger.error(f"Failed to update contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save contact. Try again.")

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    await check_contact_access(current_user)
    
    # Check if contact exists
    contact = await db.contacts.find_one({"id": contact_id, "is_deleted": {"$ne": True}})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        # Soft delete - mark as deleted
        await db.contacts.update_one(
            {"id": contact_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="DELETE",
            resource_type="Contact",
            resource_id=contact_id,
            details=f"Deleted contact: {contact['first_name']} {contact.get('last_name', '')} ({contact['email']})"
        )
        
        return {"message": "Contact deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete contact. Try again.")

@api_router.post("/contacts/bulk")
async def bulk_update_contacts(bulk_data: ContactBulkUpdate, current_user: User = Depends(get_current_user)):
    await check_contact_access(current_user)
    
    if not bulk_data.contact_ids:
        raise HTTPException(status_code=400, detail="No contacts selected")
    
    try:
        # Prepare update based on action
        if bulk_data.action == "activate":
            update_data = {"is_active": True}
        elif bulk_data.action == "deactivate":
            update_data = {"is_active": False}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update contacts
        result = await db.contacts.update_many(
            {
                "id": {"$in": bulk_data.contact_ids},
                "is_deleted": {"$ne": True}
            },
            {"$set": update_data}
        )
        
        # Log audit trail
        await log_audit_trail(
            user_id=current_user.id,
            action="BULK_UPDATE",
            resource_type="Contact",
            resource_id=",".join(bulk_data.contact_ids),
            details=f"Bulk {bulk_data.action} on {result.modified_count} contacts"
        )
        
        return {
            "message": f"Successfully {bulk_data.action}d {result.modified_count} contacts",
            "updated_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk update contacts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update contacts. Try again.")

# ================ OPPORTUNITY MANAGEMENT MODELS ================

# Master Data Models
class MstPrimaryCategory(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    is_active: bool = Field(default=True)

class MstProduct(BaseAuditModel):
    name: str = Field(..., min_length=2, max_length=100)
    primary_category_id: str = Field(..., description="Reference to primary category")
    unit: str = Field(..., max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class MstCurrency(BaseAuditModel):
    code: str = Field(..., min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')
    name: str = Field(..., min_length=2, max_length=50)
    symbol: str = Field(..., max_length=5)
    is_active: bool = Field(default=True)

class MstStage(BaseAuditModel):
    stage_code: str = Field(..., pattern=r'^L[1-8]$')
    stage_name: str = Field(..., min_length=2, max_length=100)
    stage_order: int = Field(..., ge=1, le=8)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class MstRateCard(BaseAuditModel):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    effective_from: datetime = Field(...)
    effective_to: Optional[datetime] = None
    is_active: bool = Field(default=True)

class MstSalesPrice(BaseAuditModel):
    rate_card_id: str = Field(..., description="Reference to rate card")
    product_id: str = Field(..., description="Reference to product")
    price_type: str = Field(..., pattern=r'^(recurring|one_time)$')
    price: float = Field(..., ge=0)
    currency_id: str = Field(..., description="Reference to currency")
    is_active: bool = Field(default=True)

class MstPurchaseCost(BaseAuditModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Reference to product")
    purchase_cost: float = Field(..., ge=0)
    purchase_date: date = Field(...)
    currency_id: str = Field(..., description="Reference to currency")
    cost_type: str = Field(default="Direct", pattern=r'^(Direct|Indirect|Overhead)$')
    remark: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

# Master Region Model
class MstRegion(BaseAuditModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    region_name: str = Field(..., min_length=2, max_length=100)
    region_code: str = Field(..., min_length=2, max_length=10)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

# Master Competitor Model
class MstCompetitor(BaseAuditModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitor_name: str = Field(..., min_length=2, max_length=100)
    competitor_type: str = Field(default="Direct", pattern=r'^(Direct|Indirect|Substitute)$')
    description: Optional[str] = Field(None, max_length=500)
    strengths: Optional[str] = Field(None, max_length=1000)
    weaknesses: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(default=True)

# Opportunity Models with Stage-Specific Fields
class OpportunityBase(BaseModel):
    project_title: str = Field(..., min_length=1, max_length=200)
    company_id: str = Field(..., min_length=1)
    lead_id: Optional[str] = None
    current_stage: int = Field(default=1, ge=1, le=8)  # L1 to L8
    status: str = Field(default="Active")  # Active, Won, Lost, Dropped
    expected_revenue: float = Field(default=0, ge=0)
    currency_id: str = Field(..., min_length=1)
    win_probability: float = Field(default=0, ge=0, le=100)
    weighted_revenue: float = Field(default=0, ge=0)
    
    # Stage L1 - Prospect Fields
    region_id: Optional[str] = None
    product_interest: Optional[str] = None
    assigned_representatives: List[str] = Field(default_factory=list)
    lead_owner_id: Optional[str] = None
    
    # Stage L2 - Qualification Fields
    scorecard: Optional[str] = None  # BANT, CHAMP
    budget: Optional[str] = None
    authority: Optional[str] = None
    need: Optional[str] = None
    timeline: Optional[str] = None
    qualification_status: Optional[str] = None  # Qualified, Not Now, Disqualified
    
    # Stage L3 - Proposal/Bid Fields
    proposal_documents: List[str] = Field(default_factory=list)  # File paths
    submission_date: Optional[date] = None
    internal_stakeholder_id: Optional[str] = None
    client_response: Optional[str] = None
    
    # Stage L4 - Technical Qualification Fields
    selected_quotation_id: Optional[str] = None
    
    # Stage L5 - Commercial Negotiation Fields
    updated_price: Optional[float] = None
    margin: Optional[float] = None
    cpc_overhead: Optional[float] = None
    po_number: Optional[str] = None
    po_date: Optional[date] = None
    po_file: Optional[str] = None
    
    # Stage L6 - Won Fields
    final_value: Optional[float] = None
    client_poc: Optional[str] = None
    delivery_team: List[str] = Field(default_factory=list)
    kickoff_task: Optional[str] = None
    
    # Stage L7 - Lost Fields
    lost_reason: Optional[str] = None
    competitor_id: Optional[str] = None
    followup_reminder: Optional[date] = None
    internal_learning: Optional[str] = None
    
    # Stage L8 - Dropped Fields
    drop_reason: Optional[str] = None
    reminder_date: Optional[date] = None
    
    # Locking mechanism
    is_locked: bool = Field(default=False)
    locked_stages: List[int] = Field(default_factory=list)
    
    # Audit fields
    stage_history: List[dict] = Field(default_factory=list)

class Opportunity(OpportunityBase, BaseAuditModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = Field(..., min_length=1)

# Quotation Models
class QuotationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Reference to product")
    qty: int = Field(..., ge=1)
    unit: str = Field(..., max_length=20)
    recurring_sale_price: float = Field(default=0, ge=0)
    one_time_sale_price: float = Field(default=0, ge=0)
    purchase_cost_snapshot: float = Field(default=0, ge=0)
    tenure_months: int = Field(default=1, ge=1, le=120)
    total_recurring: float = Field(default=0, ge=0)
    total_one_time: float = Field(default=0, ge=0)
    total_cost: float = Field(default=0, ge=0)

class Quotation(BaseAuditModel):
    quotation_id: str = Field(..., pattern=r'^QUO-[A-Z0-9]{7}$')
    opportunity_id: str = Field(..., description="Reference to opportunity")
    quotation_name: str = Field(..., min_length=2, max_length=100)
    rate_card_id: str = Field(..., description="Reference to rate card")
    validity_date: datetime = Field(...)
    version_no: int = Field(default=1, ge=1)
    status: str = Field(default="Draft", pattern=r'^(Draft|Approved|Rejected|Expired)$')
    items: List[QuotationItem] = Field(default_factory=list)
    total_recurring: float = Field(default=0, ge=0)
    total_one_time: float = Field(default=0, ge=0)
    grand_total: float = Field(default=0, ge=0)
    total_cost: float = Field(default=0, ge=0)
    profitability_percent: float = Field(default=0)

# Create/Update Models
class MstPrimaryCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    is_active: bool = Field(default=True)

class MstProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    primary_category_id: str = Field(..., description="Reference to primary category")
    unit: str = Field(..., max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    project_title: Optional[str] = None
    current_stage: Optional[int] = None
    status: Optional[str] = None
    expected_revenue: Optional[float] = None
    win_probability: Optional[float] = None
    
    # Stage-specific fields (all optional for updates)
    region_id: Optional[str] = None
    product_interest: Optional[str] = None
    assigned_representatives: Optional[List[str]] = None
    lead_owner_id: Optional[str] = None
    scorecard: Optional[str] = None
    budget: Optional[str] = None
    authority: Optional[str] = None
    need: Optional[str] = None
    timeline: Optional[str] = None
    qualification_status: Optional[str] = None
    proposal_documents: Optional[List[str]] = None
    submission_date: Optional[date] = None
    internal_stakeholder_id: Optional[str] = None
    client_response: Optional[str] = None
    selected_quotation_id: Optional[str] = None
    updated_price: Optional[float] = None
    margin: Optional[float] = None
    cpc_overhead: Optional[float] = None
    po_number: Optional[str] = None
    po_date: Optional[date] = None
    po_file: Optional[str] = None
    final_value: Optional[float] = None
    client_poc: Optional[str] = None
    delivery_team: Optional[List[str]] = None
    kickoff_task: Optional[str] = None
    lost_reason: Optional[str] = None
    competitor_id: Optional[str] = None
    followup_reminder: Optional[date] = None
    internal_learning: Optional[str] = None
    drop_reason: Optional[str] = None
    reminder_date: Optional[date] = None

class StageTransition(BaseModel):
    target_stage: int = Field(..., ge=1, le=8)
    stage_data: dict = Field(default_factory=dict)
    notes: Optional[str] = None

class QuotationCreate(BaseModel):
    quotation_name: str = Field(..., min_length=2, max_length=100)
    rate_card_id: str = Field(..., description="Reference to rate card")
    validity_date: datetime = Field(...)
    items: List[QuotationItem] = Field(default_factory=list)

# ================ OPPORTUNITY MANAGEMENT ENDPOINTS ================

# Helper functions
def generate_opportunity_id():
    """Generate opportunity ID in OPP-XXXXXXX format"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    suffix = ''.join(random.choices(chars, k=7))
    return f'OPP-{suffix}'

def generate_quotation_id():
    """Generate quotation ID in QUO-XXXXXXX format"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    suffix = ''.join(random.choices(chars, k=7))
    return f'QUO-{suffix}'

async def calculate_quotation_totals(quotation_data):
    """Calculate quotation totals and profitability"""
    total_recurring = 0
    total_one_time = 0
    total_cost = 0
    
    for item in quotation_data.get('items', []):
        # Calculate item totals
        item_recurring = item['recurring_sale_price'] * item['qty'] * item.get('tenure_months', 1)
        item_one_time = item['one_time_sale_price'] * item['qty']
        item_cost = item['purchase_cost_snapshot'] * item['qty']
        
        # Update item totals
        item['total_recurring'] = item_recurring
        item['total_one_time'] = item_one_time
        item['total_cost'] = item_cost
        
        # Add to grand totals
        total_recurring += item_recurring
        total_one_time += item_one_time
        total_cost += item_cost
    
    grand_total = total_recurring + total_one_time
    profitability_percent = ((grand_total - total_cost) / grand_total * 100) if grand_total > 0 else 0
    
    return {
        'total_recurring': total_recurring,
        'total_one_time': total_one_time,
        'grand_total': grand_total,
        'total_cost': total_cost,
        'profitability_percent': round(profitability_percent, 2)
    }

async def get_min_purchase_cost(product_id: str, purchase_date: datetime = None):
    """Get minimum purchase cost for a product by purchase date"""
    query = {"product_id": product_id, "is_active": True}
    if purchase_date:
        query["purchase_date"] = {"$lte": purchase_date}
    
    costs = await db.mst_purchase_costs.find(query).sort("purchase_date", -1).to_list(length=None)
    
    if not costs:
        return 0
    
    # Return minimum cost from available data
    min_cost = min(cost['purchase_cost'] for cost in costs)
    return min_cost

# Master Data APIs
@api_router.get("/mst/primary-categories")
async def get_primary_categories(current_user: User = Depends(get_current_user)):
    """Get all primary categories"""
    categories = await db.mst_primary_categories.find({"is_active": True}).to_list(None)
    return [prepare_for_json(cat) for cat in categories]

@api_router.post("/mst/primary-categories")
async def create_primary_category(category_data: MstPrimaryCategoryCreate, current_user: User = Depends(get_current_user)):
    """Create new primary category"""
    category_dict = {
        **category_data.dict(),
        "id": str(uuid.uuid4()),
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.mst_primary_categories.insert_one(category_dict)
    return prepare_for_json(category_dict)

@api_router.get("/mst/products")
async def get_products(current_user: User = Depends(get_current_user)):
    """Get all products"""
    products = await db.mst_products.find({"is_active": True}).to_list(None)
    return [prepare_for_json(product) for product in products]

@api_router.post("/mst/products")
async def create_product(product_data: MstProductCreate, current_user: User = Depends(get_current_user)):
    """Create new product"""
    product_dict = {
        **product_data.dict(),
        "id": str(uuid.uuid4()),
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.mst_products.insert_one(product_dict)
    return prepare_for_json(product_dict)

@api_router.get("/mst/currencies")
async def get_currencies(current_user: User = Depends(get_current_user)):
    """Get all currencies"""
    currencies = await db.mst_currencies.find({"is_active": True}).to_list(None)
    return [prepare_for_json(currency) for currency in currencies]

@api_router.get("/mst/stages")
async def get_stages(current_user: User = Depends(get_current_user)):
    """Get all opportunity stages (L1-L8)"""
    stages = await db.mst_stages.find({"is_active": True}).sort("stage_order", 1).to_list(None)
    return [prepare_for_json(stage) for stage in stages]

@api_router.get("/mst/rate-cards")
async def get_rate_cards(current_user: User = Depends(get_current_user)):
    """Get all active rate cards"""
    current_date = datetime.now(timezone.utc)
    query = {
        "is_active": True,
        "effective_from": {"$lte": current_date},
        "$or": [
            {"effective_to": None},
            {"effective_to": {"$gte": current_date}}
        ]
    }
    rate_cards = await db.mst_rate_cards.find(query).to_list(None)
    return [prepare_for_json(card) for card in rate_cards]

@api_router.get("/mst/sales-prices/{rate_card_id}")
async def get_sales_prices_by_rate_card(rate_card_id: str, current_user: User = Depends(get_current_user)):
    """Get sales prices for a specific rate card"""
    prices = await db.mst_sales_prices.find({
        "rate_card_id": rate_card_id,
        "is_active": True
    }).to_list(None)
    return [prepare_for_json(price) for price in prices]

@api_router.get("/mst/purchase-costs")
async def get_purchase_costs(current_user: User = Depends(get_current_user)):
    """Get all purchase costs"""
    costs = await db.mst_purchase_costs.find({"is_active": True}).sort("purchase_date", -1).to_list(None)
    return [prepare_for_json(cost) for cost in costs]

@api_router.get("/mst/regions")
async def get_regions(current_user: User = Depends(get_current_user)):
    """Get all regions"""
    regions = await db.mst_regions.find({"is_active": True}).sort("region_name", 1).to_list(None)
    return [prepare_for_json(region) for region in regions]

@api_router.get("/mst/competitors")
async def get_competitors(current_user: User = Depends(get_current_user)):
    """Get all competitors"""
    competitors = await db.mst_competitors.find({"is_active": True}).sort("competitor_name", 1).to_list(None)
    return [prepare_for_json(competitor) for competitor in competitors]

# Remove manual opportunity creation - opportunities only come from lead conversion
# @api_router.post("/opportunities") - REMOVED

@api_router.get("/opportunities")
async def get_opportunities(current_user: User = Depends(get_current_user)):
    """Get all opportunities (from lead conversion only)"""
    try:
        # Get all opportunities (handle both old and new data structures)
        opportunities = await db.opportunities.find({
            "$and": [
                {"is_active": {"$ne": False}},
                {"$or": [
                    {"status": {"$ne": "Dropped"}},  # New structure
                    {"status": {"$exists": False}}   # Old structure (no status field)
                ]}
            ]
        }).to_list(None)
        
        # Normalize data for frontend compatibility
        normalized_opportunities = []
        for opp in opportunities:
            normalized = prepare_for_json(opp)
            
            # Handle data structure differences
            if not normalized.get("project_title") and normalized.get("name"):
                normalized["project_title"] = normalized["name"]
            
            if not normalized.get("current_stage"):
                if normalized.get("stage") == "Qualification":
                    normalized["current_stage"] = 1
                else:
                    normalized["current_stage"] = 1
            
            if not normalized.get("status"):
                normalized["status"] = "Active"
                
            if not normalized.get("win_probability") and normalized.get("probability"):
                normalized["win_probability"] = normalized["probability"]
                
            if not normalized.get("expected_revenue") and normalized.get("expected_value"):
                normalized["expected_revenue"] = normalized["expected_value"]
                
            if not normalized.get("lead_owner_id") and normalized.get("owner_user_id"):
                normalized["lead_owner_id"] = normalized["owner_user_id"]
            
            # FIX: Add frontend-expected fields
            normalized["opportunity_id"] = normalized["id"]  # Frontend expects opportunity_id
            normalized["stage_id"] = normalized.get("current_stage", 1)  # Frontend expects stage_id
            
            # FIX: Resolve company name
            if normalized.get("company_id"):
                try:
                    company = await db.companies.find_one({"id": normalized["company_id"]})
                    normalized["company_name"] = company["company_name"] if company else "Unknown Company"
                except:
                    normalized["company_name"] = "Unknown Company"
            else:
                normalized["company_name"] = "No Company"
                
            normalized_opportunities.append(normalized)
        
        return {
            "opportunities": normalized_opportunities,
            "total": len(normalized_opportunities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching opportunities: {str(e)}")

@api_router.get("/opportunities/{opportunity_id}")
async def get_opportunity_by_id(opportunity_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific opportunity by ID"""
    opportunity = await db.opportunities.find_one({"id": opportunity_id})
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return prepare_for_json(opportunity)

@api_router.post("/opportunities/{opportunity_id}/change-stage")
async def change_opportunity_stage(
    opportunity_id: str, 
    stage_transition: StageTransition, 
    current_user: User = Depends(get_current_user)
):
    """Change opportunity stage with validation and locking rules"""
    
    # Get existing opportunity
    opportunity = await db.opportunities.find_one({"id": opportunity_id})
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    current_stage = opportunity.get("current_stage", 1)
    target_stage = stage_transition.target_stage
    stage_data = stage_transition.stage_data
    
    # Check if opportunity is locked
    if opportunity.get("is_locked", False):
        raise HTTPException(status_code=400, detail="Opportunity is locked and cannot be modified")
    
    # Check if trying to modify locked stages (after L4)
    if current_stage >= 4 and target_stage < current_stage:
        raise HTTPException(status_code=400, detail="Cannot move backward from L4 and beyond")
    
    # Stage-specific validation
    if target_stage > current_stage:
        # Progressing to next stage - validate current stage data
        validation_errors = await validate_stage_data(current_stage, stage_data, opportunity_id)
        if validation_errors:
            raise HTTPException(status_code=400, detail={"validation_errors": validation_errors})
    elif target_stage == current_stage:
        # Draft save - no validation required (allow incomplete data)
        pass
    else:
        # Moving backward - validate target stage data
        validation_errors = await validate_stage_data(target_stage, stage_data, opportunity_id)
        if validation_errors:
            raise HTTPException(status_code=400, detail={"validation_errors": validation_errors})
    
    # Prepare update data
    update_data = {
        "current_stage": target_stage,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": current_user.id
    }
    
    # Add stage-specific data
    update_data.update(stage_data)
    
    # Handle special stage transitions
    if target_stage == 6:  # Won
        update_data["status"] = "Won"
        update_data["is_locked"] = True
        update_data["close_date"] = datetime.now(timezone.utc)
    elif target_stage == 7:  # Lost
        update_data["status"] = "Lost"
        update_data["is_locked"] = True
        update_data["close_date"] = datetime.now(timezone.utc)
    elif target_stage == 8:  # Dropped
        update_data["status"] = "Dropped"
        update_data["is_locked"] = True
        update_data["close_date"] = datetime.now(timezone.utc)
    
    # Lock stages L1-L3 after reaching L4
    if target_stage >= 4:
        update_data["locked_stages"] = [1, 2, 3]
    
    # Add to stage history
    stage_history_entry = {
        "from_stage": current_stage,
        "to_stage": target_stage,
        "changed_by": current_user.id,
        "changed_at": datetime.now(timezone.utc),
        "notes": stage_transition.notes,
        "stage_data": stage_data
    }
    
    # Update stage history
    if "stage_history" not in opportunity:
        opportunity["stage_history"] = []
    
    opportunity["stage_history"].append(stage_history_entry)
    update_data["stage_history"] = opportunity["stage_history"]
    
    # Update opportunity
    await db.opportunities.update_one(
        {"id": opportunity_id},
        {"$set": prepare_for_mongo(update_data)}
    )
    
    return {"message": f"Opportunity stage changed from L{current_stage} to L{target_stage}"}

async def validate_stage_data(stage: int, data: dict, opportunity_id: str) -> List[str]:
    """Validate stage-specific required fields"""
    errors = []
    
    if stage == 1:  # L1 - Prospect
        if not data.get("region_id"):
            errors.append("Region is required for L1 - Prospect")
        if not data.get("product_interest"):
            errors.append("Product Interest is required for L1 - Prospect")
        if not data.get("assigned_representatives") or len(data["assigned_representatives"]) == 0:
            errors.append("At least one Assigned Representative is required for L1 - Prospect")
        if not data.get("lead_owner_id"):
            errors.append("Lead Owner is required for L1 - Prospect")
    
    elif stage == 2:  # L2 - Qualification
        if not data.get("scorecard"):
            errors.append("Scorecard is required for L2 - Qualification")
        if not data.get("budget"):
            errors.append("Budget is required for L2 - Qualification")
        if not data.get("authority"):
            errors.append("Authority is required for L2 - Qualification")
        if not data.get("need"):
            errors.append("Need is required for L2 - Qualification")
        if not data.get("timeline"):
            errors.append("Timeline is required for L2 - Qualification")
        if not data.get("qualification_status"):
            errors.append("Status is required for L2 - Qualification")
    
    elif stage == 3:  # L3 - Proposal/Bid
        # Check for uploaded documents in database
        uploaded_documents = await db.opportunity_documents.find({
            "opportunity_id": opportunity_id,
            "is_active": True
        }).to_list(None)
        
        if not uploaded_documents:
            errors.append("Proposal Documents are required for L3 - Proposal/Bid")
        if not data.get("submission_date"):
            errors.append("Submission Date is required for L3 - Proposal/Bid")
        if not data.get("internal_stakeholder_id"):
            errors.append("Internal Stakeholder is required for L3 - Proposal/Bid")
    
    elif stage == 4:  # L4 - Technical Qualification
        if not data.get("selected_quotation_id"):
            errors.append("Selected Quotation is required for L4 - Technical Qualification")
        
        # Verify quotation exists
        if data.get("selected_quotation_id"):
            quotation = await db.quotations.find_one({
                "id": data["selected_quotation_id"],
                "opportunity_id": opportunity_id
            })
            if not quotation:
                errors.append("Selected quotation not found or not associated with this opportunity")
    
    elif stage == 5:  # L5 - Commercial Negotiation
        if not data.get("updated_price"):
            errors.append("Updated Price is required for L5 - Commercial Negotiation")
        if not data.get("po_number"):
            errors.append("PO Number is required for L5 - Commercial Negotiation")
        if not data.get("po_date"):
            errors.append("PO Date is required for L5 - Commercial Negotiation")
    
    elif stage == 6:  # L6 - Won
        if not data.get("final_value"):
            errors.append("Final Value is required for L6 - Won")
        if not data.get("client_poc"):
            errors.append("Client POC is required for L6 - Won")
        if not data.get("delivery_team") or len(data["delivery_team"]) == 0:
            errors.append("Delivery Team is required for L6 - Won")
    
    elif stage == 7:  # L7 - Lost
        if not data.get("lost_reason"):
            errors.append("Lost Reason is required for L7 - Lost")
    
    elif stage == 8:  # L8 - Dropped
        if not data.get("drop_reason"):
            errors.append("Drop Reason is required for L8 - Dropped")
    
    return errors

# Quotation APIs
@api_router.get("/opportunities/{opportunity_id}/quotations")
async def get_opportunity_quotations(opportunity_id: str, current_user: User = Depends(get_current_user)):
    """Get all quotations for an opportunity"""
    quotations = await db.quotations.find({
        "opportunity_id": opportunity_id,
        "is_active": True
    }).to_list(None)
    
    return [prepare_for_json(quot) for quot in quotations]

@api_router.post("/opportunities/{opportunity_id}/quotations")
async def create_quotation(
    opportunity_id: str,
    quotation_data: QuotationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new quotation for opportunity"""
    
    # Verify opportunity exists
    opportunity = await db.opportunities.find_one({"id": opportunity_id, "is_active": True})
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    quotation_dict = quotation_data.dict()
    quotation_dict.update({
        "id": str(uuid.uuid4()),
        "quotation_id": generate_quotation_id(),
        "opportunity_id": opportunity_id,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    })
    
    # Calculate totals and profitability
    totals = await calculate_quotation_totals(quotation_dict)
    quotation_dict.update(totals)
    
    await db.quotations.insert_one(quotation_dict)
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="CREATE",
        resource_type="Quotation",
        resource_id=quotation_dict["id"],
        details=f"Created quotation: {quotation_dict['quotation_id']}"
    )
    
    return prepare_for_json(quotation_dict)

@api_router.get("/quotations/{quotation_id}")
async def get_quotation(quotation_id: str, current_user: User = Depends(get_current_user)):
    """Get quotation by ID"""
    quotation = await db.quotations.find_one({"id": quotation_id, "is_active": True})
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    return prepare_for_json(quotation)

@api_router.patch("/opportunities/{opportunity_id}/quotations/{quotation_id}/select")
async def select_quotation(opportunity_id: str, quotation_id: str, current_user: User = Depends(get_current_user)):
    """Select a quotation as the chosen one for the opportunity"""
    # Check if opportunity exists
    existing_opportunity = await db.opportunities.find_one({"id": opportunity_id})
    if not existing_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Check if quotation exists
    existing_quotation = await db.quotations.find_one({"id": quotation_id, "opportunity_id": opportunity_id})
    if not existing_quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # Deselect all other quotations for this opportunity
    await db.quotations.update_many(
        {"opportunity_id": opportunity_id},
        {
            "$set": {
                "is_selected": False,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Select this quotation
    await db.quotations.update_one(
        {"id": quotation_id},
        {
            "$set": {
                "is_selected": True,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Quotation selected successfully"}

@api_router.get("/opportunities/{opportunity_id}/quotations/{quotation_id}")
async def get_quotation_by_id(opportunity_id: str, quotation_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific quotation by ID"""
    quotation = await db.quotations.find_one({"id": quotation_id, "opportunity_id": opportunity_id})
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    return parse_from_mongo(quotation)

@api_router.put("/opportunities/{opportunity_id}/quotations/{quotation_id}")
async def update_quotation(opportunity_id: str, quotation_id: str, quotation: QuotationCreate, current_user: User = Depends(get_current_user)):
    """Update an existing quotation"""
    existing_quotation = await db.quotations.find_one({"id": quotation_id, "opportunity_id": opportunity_id})
    if not existing_quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    quotation_data = quotation.dict()
    quotation_data["updated_at"] = datetime.now(timezone.utc)
    quotation_data = prepare_for_mongo(quotation_data)
    
    await db.quotations.update_one(
        {"id": quotation_id},
        {"$set": quotation_data}
    )
    
    updated_quotation = await db.quotations.find_one({"id": quotation_id})
    return parse_from_mongo(updated_quotation)

@api_router.patch("/opportunities/{opportunity_id}/stage")
async def update_opportunity_stage(opportunity_id: str, stage_data: dict, current_user: User = Depends(get_current_user)):
    """Update opportunity stage"""
    existing_opportunity = await db.opportunities.find_one({"id": opportunity_id})
    if not existing_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Validate stage exists
    stage_id = stage_data.get("stage_id")
    if not stage_id:
        raise HTTPException(status_code=400, detail="Stage ID is required")
    
    existing_stage = await db.mst_stages.find_one({"id": stage_id})
    if not existing_stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    # Update opportunity stage
    update_data = {
        "stage_id": stage_id,
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Add stage change notes if provided
    if stage_data.get("stage_change_notes"):
        update_data["stage_change_notes"] = stage_data["stage_change_notes"]
    
    await db.opportunities.update_one(
        {"id": opportunity_id},
        {"$set": update_data}
    )
    
    return {"message": "Stage updated successfully"}

# File upload for opportunity documents
@api_router.post("/opportunities/{opportunity_id}/upload-document")
async def upload_opportunity_document(
    opportunity_id: str,
    file: UploadFile = File(...), 
    document_type: str = "proposal",
    description: str = "",
    current_user: User = Depends(get_current_user)
):
    """Upload document for opportunity (proposals, contracts, etc.)"""
    
    # Check if opportunity exists
    opportunity = await db.opportunities.find_one({"id": opportunity_id})
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Validate file
    if file.size > 10 * 1024 * 1024:  # 10MB limit for opportunity documents
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                     "application/msword", "image/png", "image/jpeg", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed. Only PDF, DOC, DOCX, PNG, JPG, TXT are supported")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/opportunity_documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create document record
    document = {
        "id": str(uuid.uuid4()),
        "opportunity_id": opportunity_id,
        "document_type": document_type,
        "filename": filename,
        "original_filename": file.filename,
        "file_path": str(file_path),
        "file_size": len(content),
        "mime_type": file.content_type,
        "description": description,
        "uploaded_by": current_user.id,
        "uploaded_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.opportunity_documents.insert_one(document)
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="UPLOAD",
        resource_type="OpportunityDocument",
        resource_id=document["id"],
        details=f"Uploaded document: {file.filename} for opportunity {opportunity_id}"
    )
    
    return prepare_for_json(document)

@api_router.get("/opportunities/{opportunity_id}/documents")
async def get_opportunity_documents(opportunity_id: str, current_user: User = Depends(get_current_user)):
    """Get all documents for an opportunity"""
    
    documents = await db.opportunity_documents.find({
        "opportunity_id": opportunity_id,
        "is_active": True
    }).to_list(None)
    
    return [prepare_for_json(doc) for doc in documents]

@api_router.delete("/opportunities/{opportunity_id}/documents/{document_id}")
async def delete_opportunity_document(
    opportunity_id: str, 
    document_id: str, 
    current_user: User = Depends(get_current_user)
):
    """Delete an opportunity document"""
    
    document = await db.opportunity_documents.find_one({
        "id": document_id,
        "opportunity_id": opportunity_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Mark as inactive (soft delete)
    await db.opportunity_documents.update_one(
        {"id": document_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="DELETE",
        resource_type="OpportunityDocument",
        resource_id=document_id,
        details=f"Deleted document: {document['original_filename']}"
    )
    
    return {"message": "Document deleted successfully"}

# Include router after all endpoints are defined
app.include_router(api_router)