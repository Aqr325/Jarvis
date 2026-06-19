"""
JWT Token 处理
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt  # PyJWT
from pydantic import BaseModel


class JWTHandler:
    """
    JWT Token 处理器
    
    提供：
    - Token 生成
    - Token 验证
    - Token 刷新
    - 密码哈希
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_minutes: int = 1440,  # 24 小时
    ):
        self.secret_key = secret_key or self._generate_secret()
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_minutes = refresh_token_expire_minutes

    def _generate_secret(self) -> str:
        """生成随机密钥"""
        import secrets
        return secrets.token_urlsafe(32)

    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """
        哈希密码
        
        Returns:
            (hashed_password, salt)
        """
        if salt is None:
            salt = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        
        # 使用 PBKDF2 哈希
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return hashed.hex(), salt

    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """验证密码"""
        hashed, _ = self.hash_password(password, salt)
        return hmac.compare_digest(hashed, hashed_password)

    def create_token(
        self,
        user_id: str,
        username: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        token_type: str = "access"
    ) -> str:
        """
        创建 Token
        
        Args:
            user_id: 用户 ID
            username: 用户名
            role: 用户角色
            additional_claims: 额外声明
            token_type: 令牌类型 (access/refresh)
        
        Returns:
            JWT Token 字符串
        """
        expire_minutes = (
            self.access_token_expire_minutes if token_type == "access"
            else self.refresh_token_expire_minutes
        )
        
        now = datetime.utcnow()
        expire = now + timedelta(minutes=expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": expire,
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码 Token
        
        Args:
            token: JWT Token 字符串
        
        Returns:
            Token 载荷，如果无效则返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def validate_token(self, token: str) -> tuple:
        """
        验证 Token
        
        Returns:
            (is_valid, payload_or_error)
        """
        payload = self.decode_token(token)
        
        if payload is None:
            return False, "Invalid or expired token"
        
        # 检查必要字段
        required_fields = ["sub", "username", "role", "type"]
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"
        
        return True, payload

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的访问令牌，如果无效则返回 None
        """
        payload = self.decode_token(refresh_token)
        
        if payload is None:
            return None
        
        # 检查是否为刷新令牌
        if payload.get("type") != "refresh":
            return None
        
        # 创建新的访问令牌
        return self.create_token(
            user_id=payload["sub"],
            username=payload["username"],
            role=payload["role"],
            token_type="access"
        )

    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌（简实现：实际应该使用令牌黑名单）
        
        注意：JWT 本身是无状态的，无法真正撤销。
        生产环境应实现令牌黑名单机制。
        """
        # 这里只是示意，实际应该将 token 的 jti 加入黑名单
        payload = self.decode_token(token)
        if payload:
            # 实际实现：将 token 的 jti 或 exp 记录到黑名单
            pass
        return True

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """获取令牌过期时间"""
        payload = self.decode_token(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None


class TokenInfo(BaseModel):
    """Token 信息"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    username: str
    role: str
