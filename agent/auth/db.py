# -*- coding: utf-8 -*-
"""
认证数据访问层 - SQLite 数据库管理
存储用户账户信息、密码哈希与邮箱验证码
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "english_evaluate.db"


def init_db():
    """初始化数据库与表结构"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. 用户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        nickname TEXT NOT NULL,
        avatar_style TEXT DEFAULT 'ink_scholar',
        role TEXT DEFAULT 'student',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login_at DATETIME,
        is_active INTEGER DEFAULT 1
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

    # 2. 邮箱验证码表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        code TEXT NOT NULL,
        action_type TEXT NOT NULL,
        expires_at DATETIME NOT NULL,
        is_used INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verifications_email ON email_verifications(email);")

    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（行格式为 sqlite3.Row 便于字典式访问）"""
    if not DB_PATH.exists():
        init_db()
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────
# 用户表 CRUD 操作
# ─────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """根据邮箱查询用户"""
    email_clean = email.strip().lower()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email_clean,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 查询用户"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_user(
    email: str,
    password_hash: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar_style: str = "ink_scholar"
) -> Dict[str, Any]:
    """创建新用户"""
    email_clean = email.strip().lower()
    if not nickname or not nickname.strip():
        # 默认取邮箱前缀作为昵称
        nickname = email_clean.split("@")[0]
        if len(nickname) > 20:
            nickname = nickname[:20]

    conn = get_connection()
    try:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (email, password_hash, nickname, avatar_style, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email_clean, password_hash, nickname.strip(), avatar_style, now_str, now_str))
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "email": email_clean,
            "nickname": nickname.strip(),
            "avatar_style": avatar_style,
            "role": "student",
            "created_at": now_str
        }
    finally:
        conn.close()


def update_user_last_login(user_id: int):
    """更新用户最后登录时间"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_str, user_id))
        conn.commit()
    finally:
        conn.close()


def update_user_password(user_id: int, new_password_hash: str):
    """修改用户密码"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
        conn.commit()
    finally:
        conn.close()


def update_user_profile(user_id: int, nickname: str, avatar_style: Optional[str] = None):
    """更新用户昵称或学者头像风格"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if avatar_style:
            cursor.execute("UPDATE users SET nickname = ?, avatar_style = ? WHERE id = ?", (nickname.strip(), avatar_style, user_id))
        else:
            cursor.execute("UPDATE users SET nickname = ? WHERE id = ?", (nickname.strip(), user_id))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# 验证码操作
# ─────────────────────────────────────────────────────────────

def has_recent_code(email: str, action_type: str, window_seconds: int = 60) -> bool:
    """检查是否在指定秒数内已发过验证码（防刷限制）"""
    email_clean = email.strip().lower()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        threshold = (datetime.now() - timedelta(seconds=window_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT id FROM email_verifications
            WHERE email = ? AND action_type = ? AND created_at > ?
            ORDER BY id DESC LIMIT 1
        """, (email_clean, action_type, threshold))
        row = cursor.fetchone()
        return row is not None
    finally:
        conn.close()


def save_verification_code(email: str, code: str, action_type: str, expires_minutes: int = 5) -> int:
    """保存新生成的验证码"""
    email_clean = email.strip().lower()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now()
        expires_at = (now + timedelta(minutes=expires_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO email_verifications (email, code, action_type, expires_at, created_at, is_used)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (email_clean, code, action_type, expires_at, now_str))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_valid_verification_code(email: str, code: str, action_type: str) -> Optional[Dict[str, Any]]:
    """查找匹配且未过期、未使用的有效验证码记录"""
    email_clean = email.strip().lower()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT * FROM email_verifications
            WHERE email = ? AND code = ? AND action_type = ? AND is_used = 0 AND expires_at >= ?
            ORDER BY id DESC LIMIT 1
        """, (email_clean, code.strip(), action_type, now_str))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def mark_code_as_used(record_id: int):
    """将验证码标记为已使用（单次消费作废）"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE email_verifications SET is_used = 1 WHERE id = ?", (record_id,))
        conn.commit()
    finally:
        conn.close()
