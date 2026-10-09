# -*- coding: utf-8 -*-
"""
认证核心业务层 - 涵盖账号注册、登录认证、验证码核验、JWT 签发
"""
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from agent.auth.db import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_user_last_login,
    update_user_password,
    update_user_profile,
    has_recent_code,
    save_verification_code,
    get_valid_verification_code,
    mark_code_as_used
)
from agent.auth.email_service import generate_code, send_verification_email

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kaoyan-english-eval-jwt-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_format(email: str) -> bool:
    """验证邮箱格式是否合规"""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def create_token(user_id: int, email: str, nickname: str) -> str:
    """签发 7 天有效期的 JWT Token"""
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "email": email,
        "nickname": nickname,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码并校验 JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def sanitize_user_dict(user: Dict[str, Any]) -> Dict[str, Any]:
    """过滤脱敏用户数据，杜绝泄露密码哈希"""
    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": user["nickname"],
        "avatar_style": user.get("avatar_style", "ink_scholar"),
        "role": user.get("role", "student"),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at")
    }


# ─────────────────────────────────────────────────────────────
# 业务 API 方法
# ─────────────────────────────────────────────────────────────

def send_code_flow(email: str, action_type: str = "login") -> Dict[str, Any]:
    """发送邮箱验证码主流程"""
    email = (email or "").strip().lower()
    if not validate_email_format(email):
        return {"success": False, "error": "邮箱格式不正确，请输入有效的邮箱地址"}

    # 1. 防刷检查：60 秒内只能发送 1 次
    if has_recent_code(email, action_type, window_seconds=60):
        return {"success": False, "error": "验证码发送过于频繁，请在 60 秒后重试"}

    # 2. 生成验证码
    code = generate_code(6)

    # 3. 存储进数据库（有效期 5 分钟）
    save_verification_code(email=email, code=code, action_type=action_type, expires_minutes=5)

    # 4. 发送邮件
    success, msg, dev_code = send_verification_email(email=email, code=code, action_type=action_type)

    resp = {
        "success": success,
        "message": msg
    }
    # 若在开发测试环境下，返回 dev_code 以便无障碍本地测试
    if dev_code:
        resp["dev_code"] = dev_code

    return resp


def register_with_password(email: str, password: str, nickname: Optional[str] = None) -> Dict[str, Any]:
    """邮箱 + 密码 自主注册"""
    email = (email or "").strip().lower()
    password = (password or "").strip()
    nickname = (nickname or "").strip()

    if not validate_email_format(email):
        return {"success": False, "error": "邮箱格式不正确"}

    if len(password) < 6:
        return {"success": False, "error": "密码长度不能少于 6 个字符"}

    if len(password) > 32:
        return {"success": False, "error": "密码长度不能超过 32 个字符"}

    # 检查邮箱是否已被注册
    existing = get_user_by_email(email)
    if existing:
        return {"success": False, "error": "该邮箱已注册，请直接登录或使用验证码找回密码"}

    # 生成工业级安全加盐哈希
    pwd_hash = generate_password_hash(password, method="pbkdf2:sha256")
    user = create_user(email=email, password_hash=pwd_hash, nickname=nickname)

    # 签发 JWT
    token = create_token(user["id"], user["email"], user["nickname"])

    return {
        "success": True,
        "message": "注册成功，已自动登录",
        "token": token,
        "user": sanitize_user_dict(user)
    }


def login_with_password(email: str, password: str) -> Dict[str, Any]:
    """邮箱 + 密码 登录"""
    email = (email or "").strip().lower()
    password = (password or "").strip()

    if not validate_email_format(email):
        return {"success": False, "error": "请输入有效的邮箱地址"}

    if not password:
        return {"success": False, "error": "请输入登录密码"}

    user = get_user_by_email(email)
    if not user:
        return {"success": False, "error": "该邮箱尚未注册，请先注册或使用验证码快捷登录"}

    if not user.get("password_hash"):
        return {"success": False, "error": "该账号此前通过免密验证码登录，尚未设置密码，请使用验证码登录或重置密码"}

    if not check_password_hash(user["password_hash"], password):
        return {"success": False, "error": "邮箱或密码错误，请重新输入"}

    # 更新最后登录时间
    update_user_last_login(user["id"])
    token = create_token(user["id"], user["email"], user["nickname"])

    return {
        "success": True,
        "message": "登录成功",
        "token": token,
        "user": sanitize_user_dict(user)
    }


def login_with_code(email: str, code: str) -> Dict[str, Any]:
    """邮箱 + 验证码 快捷免密登录（未注册则自动建档）"""
    email = (email or "").strip().lower()
    code = (code or "").strip()

    if not validate_email_format(email):
        return {"success": False, "error": "请输入有效的邮箱地址"}

    if not code or len(code) != 6:
        return {"success": False, "error": "请输入完整的 6 位数字验证码"}

    # 核验验证码
    record = get_valid_verification_code(email, code, action_type="login")
    if not record:
        return {"success": False, "error": "验证码错误或已过期，请重新获取"}

    # 核销作废
    mark_code_as_used(record["id"])

    # 查找或自动创建用户
    user = get_user_by_email(email)
    is_new_user = False
    if not user:
        user = create_user(email=email, password_hash=None, nickname=None)
        is_new_user = True
    else:
        update_user_last_login(user["id"])

    token = create_token(user["id"], user["email"], user["nickname"])

    return {
        "success": True,
        "message": "登录成功" if not is_new_user else "欢迎新学子，已为您自动完成注册并登录",
        "is_new_user": is_new_user,
        "token": token,
        "user": sanitize_user_dict(user)
    }


def reset_password_with_code(email: str, code: str, new_password: str) -> Dict[str, Any]:
    """通过邮箱验证码重置密码"""
    email = (email or "").strip().lower()
    code = (code or "").strip()
    new_password = (new_password or "").strip()

    if not validate_email_format(email):
        return {"success": False, "error": "请输入有效的邮箱地址"}

    if not code or len(code) != 6:
        return {"success": False, "error": "请输入 6 位数字验证码"}

    if len(new_password) < 6:
        return {"success": False, "error": "新密码长度不能少于 6 个字符"}

    record = get_valid_verification_code(email, code, action_type="reset_pwd")
    if not record:
        return {"success": False, "error": "验证码错误或已过期"}

    user = get_user_by_email(email)
    if not user:
        return {"success": False, "error": "该邮箱用户不存在"}

    mark_code_as_used(record["id"])
    pwd_hash = generate_password_hash(new_password, method="pbkdf2:sha256")
    update_user_password(user["id"], pwd_hash)

    # 签发新 Token 自动登录
    token = create_token(user["id"], user["email"], user["nickname"])

    return {
        "success": True,
        "message": "密码重置成功，已自动登录",
        "token": token,
        "user": sanitize_user_dict(user)
    }


def get_current_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    """根据 Token 获取当前有效用户信息"""
    payload = decode_token(token)
    if not payload or "user_id" not in payload:
        return None
    user = get_user_by_id(payload["user_id"])
    if not user:
        return None
    return sanitize_user_dict(user)


def update_user_profile_service(user_id: int, nickname: str, avatar_style: Optional[str] = None) -> Dict[str, Any]:
    """修改个人资料"""
    nickname = (nickname or "").strip()
    if not nickname:
        return {"success": False, "error": "昵称不能为空"}
    if len(nickname) > 20:
        return {"success": False, "error": "昵称长度不能超过 20 个字"}

    update_user_profile(user_id, nickname=nickname, avatar_style=avatar_style)
    user = get_user_by_id(user_id)
    return {
        "success": True,
        "message": "资料修改成功",
        "user": sanitize_user_dict(user)
    }
