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
        # Get module, menu, and permission details
        module = await db.modules.find_one({"id": rp["module_id"], "status": "active"})
        menu = await db.menus.find_one({"id": rp["menu_id"]})
        permission = await db.permissions.find_one({"id": rp["permission_id"], "status": "active"})
        
        if module and menu and permission:
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
async def get_user_permissions(current_user: User = Depends(get_current_user)):
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
        # Get module, menu, and permission details
        module = await db.modules.find_one({"id": rp["module_id"], "status": "active"})
        menu = await db.menus.find_one({"id": rp["menu_id"]})
        permission = await db.permissions.find_one({"id": rp["permission_id"], "status": "active"})
        
        if module and menu and permission:
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
            await initialize_rbac_system()
            logger.info("RBAC system initialized with default admin user: admin/admin123")
            
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
        {"name": "Leads", "path": "/leads", "module_id": created_modules["Sales"], "order_index": 4},
        {"name": "Opportunities", "path": "/opportunities", "module_id": created_modules["Sales"], "order_index": 5},
        
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
    
    logger.info("Company registration master data initialized successfully")

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
    companies = await db.companies.find().to_list(None)
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
            {"name": company_data.name},
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
    
    # Create company
    company = Company(
        **company_data.dict(),
        score=score,
        lead_status=lead_status,
        created_by=current_user.id
    )
    
    company_dict = prepare_for_mongo(company.dict())
    company_dict.pop('_id', None)
    await db.companies.insert_one(company_dict)
    
    # Log audit trail
    await log_audit_trail(
        user_id=current_user.id,
        action="CREATE",
        resource_type="Company",
        resource_id=company.id,
        details=f"Created company: {company.name}"
    )
    
    # Log email notification attempt
    logger.info(f"Email notification attempt: New company '{company.name}' created by {current_user.username}")
    
    return prepare_for_json(company.dict())

async def calculate_company_score(company_data: CompanyCreate) -> int:
    """Calculate company score based on various factors"""
    score = 0
    
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
    
    return min(score, 100)  # Cap at 100

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