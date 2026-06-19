"""
认证中间件
"""

from typing import Optional, Callable, Awaitable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from .jwt_handler import JWTHandler


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    
    提供：
    - JWT Token 验证
    - 受保护路由的认证检查
    - 用户信息注入
    """

    # 公开路由（无需认证）
    PUBLIC_ROUTES = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/refresh",
        "/api/auth/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/",
    ]

    def __init__(
        self,
        app,
        jwt_handler: JWTHandler,
        exclude_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.jwt_handler = jwt_handler
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Awaitable:
        """处理请求"""
        path = request.url.path

        # 检查是否排除
        if path in self.PUBLIC_ROUTES or path in self.exclude_paths:
            return await call_next(request)

        # 获取认证头
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ", 1)[1]
        
        # 验证 Token
        is_valid, payload_or_error = self.jwt_handler.validate_token(token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=payload_or_error,
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将用户信息注入到请求中
        request.state.user_id = payload_or_error["sub"]
        request.state.username = payload_or_error["username"]
        request.state.user_role = payload_or_error["role"]
        request.state.token_payload = payload_or_error

        # 继续处理请求
        response = await call_next(request)
        return response


class PermissionMiddleware:
    """
    权限检查装饰器
    
    用法：
    @require_permission("agent:execute")
    async def some_endpoint(request: Request):
        ...
    """

    def __init__(self, jwt_handler: JWTHandler):
        self.jwt_handler = jwt_handler

    def require_permission(self, permission: str):
        """
        权限检查装饰器
        
        Args:
            permission: 需要的权限，如 "agent:execute"
        """
        def decorator(func: Callable):
            async def wrapper(request: Request, *args, **kwargs):
                # 从 request.state 获取用户信息
                user_role = getattr(request.state, "user_role", None)
                
                if not user_role:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not authenticated",
                    )

                # 管理员拥有所有权限
                if user_role == "admin":
                    return await func(request, *args, **kwargs)

                # 检查权限（简化实现）
                user_permissions = getattr(request.state, "user_permissions", [])
                
                # 注意：实际应该从数据库获取用户权限
                # 这里简化处理
                if permission not in user_permissions and permission != "*":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: required '{permission}'",
                    )

                return await func(request, *args, **kwargs)

            return wrapper
        return decorator


def get_current_user(request: Request) -> dict:
    """
    获取当前认证用户
    
    Args:
        request: FastAPI 请求对象
    
    Returns:
        用户信息字典
    """
    user_id = getattr(request.state, "user_id", None)
    username = getattr(request.state, "username", None)
    role = getattr(request.state, "user_role", None)

    if not user_id or not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    return {
        "user_id": user_id,
        "username": username,
        "role": role,
    }
