"""
权限系统数据模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"           # 管理员：完全权限
    USER = "user"             # 普通用户：基本权限
    GUEST = "guest"           # 访客：只读权限
    DEVELOPER = "developer"   # 开发者：开发权限
    OPERATOR = "operator"     # 操作员：运维权限


class PermissionLevel(int, Enum):
    """权限级别"""
    READ = 1                  # 只读
    WRITE = 2                 # 写入
    DELETE = 3                # 删除
    ADMIN = 4                 # 管理


class User(BaseModel):
    """用户模型"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: UserRole = UserRole.USER
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None  # 实际存储哈希值

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        if self.role == UserRole.ADMIN:
            return True
        return permission in self.permissions

    def has_role(self, role: UserRole) -> bool:
        """检查是否有特定角色"""
        return self.role == role or self.role == UserRole.ADMIN

    def get_permission_level(self, resource: str) -> PermissionLevel:
        """获取对某资源的权限级别"""
        # 简化实现：基于角色和权限列表
        if self.role == UserRole.ADMIN:
            return PermissionLevel.ADMIN
        elif f"{resource}:write" in self.permissions:
            return PermissionLevel.WRITE
        elif f"{resource}:read" in self.permissions or self.role in [UserRole.USER, UserRole.DEVELOPER]:
            return PermissionLevel.READ
        return PermissionLevel.READ


class Role(BaseModel):
    """角色模型"""
    role_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: UserRole
    description: str
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "name": self.name.value,
            "description": self.description,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def get_default_roles() -> List["Role"]:
        """获取默认角色配置"""
        return [
            Role(
                name=UserRole.ADMIN,
                description="系统管理员，拥有所有权限",
                permissions=[
                    "user:read", "user:write", "user:delete",
                    "agent:read", "agent:write", "agent:delete",
                    "system:read", "system:write", "system:admin",
                    "plugin:read", "plugin:write", "plugin:delete",
                ]
            ),
            Role(
                name=UserRole.USER,
                description="普通用户，基本使用权限",
                permissions=[
                    "user:read",
                    "agent:read", "agent:execute",
                    "plugin:read",
                ]
            ),
            Role(
                name=UserRole.GUEST,
                description="访客，只读权限",
                permissions=[
                    "user:read",
                    "agent:read",
                    "plugin:read",
                ]
            ),
            Role(
                name=UserRole.DEVELOPER,
                description="开发者，开发调试权限",
                permissions=[
                    "user:read", "user:write",
                    "agent:read", "agent:write", "agent:execute",
                    "plugin:read", "plugin:write",
                    "system:read", "system:debug",
                ]
            ),
            Role(
                name=UserRole.OPERATOR,
                description="操作员，运维管理权限",
                permissions=[
                    "user:read",
                    "agent:read", "agent:execute", "agent:manage",
                    "system:read", "system:write", "system:monitor",
                    "plugin:read", "plugin:write",
                ]
            ),
        ]


class Permission(BaseModel):
    """权限模型"""
    permission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    resource: str  # 资源类型：user, agent, plugin, system 等
    action: str    # 操作类型：read, write, delete, admin 等
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> dict:
        return {
            "permission_id": self.permission_id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def format_permission(resource: str, action: str) -> str:
        """格式化权限名称"""
        return f"{resource}:{action}"

    @staticmethod
    def parse_permission(permission: str) -> tuple:
        """解析权限名称"""
        parts = permission.split(":")
        if len(parts) >= 2:
            return parts[0], parts[1]
        return permission, "read"


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    user: Optional[dict] = None
    message: Optional[str] = None


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: str
    password: str
    confirm_password: str


class TokenRefreshRequest(BaseModel):
    """刷新 token 请求"""
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """刷新 token 响应"""
    success: bool
    access_token: Optional[str] = None
    expires_in: Optional[int] = None
    message: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str
    confirm_password: str


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    page: int
    page_size: int
    users: List[dict]


class RoleListResponse(BaseModel):
    """角色列表响应"""
    roles: List[dict]
