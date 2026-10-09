# -*- coding: utf-8 -*-
"""
邮件服务适配器 - 支持真实 SMTP 发送与本地终端仿真模式双模式
"""
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, Any, Tuple, Optional


def generate_code(length: int = 6) -> str:
    """生成 6 位数字验证码"""
    return "".join(random.choices("0123456789", k=length))


def get_smtp_config() -> Dict[str, Any]:
    """获取 SMTP 配置"""
    return {
        "server": os.getenv("SMTP_SERVER", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "465")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "sender_name": os.getenv("SMTP_SENDER_NAME", "考研英语二写作智能评卷系统").strip(),
        "use_ssl": os.getenv("SMTP_USE_SSL", "true").lower() in ("true", "1", "yes")
    }


def is_smtp_configured() -> bool:
    """判断是否配置了可用的真实 SMTP 服务凭据"""
    cfg = get_smtp_config()
    return bool(cfg["server"] and cfg["user"] and cfg["password"])


def build_email_html(code: str, action_name: str, email: str) -> str:
    """生成具有学术研读台风格的雅致 HTML 邮件内容"""
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <title>验证码</title>
      <style>
        body {{
          margin: 0;
          padding: 0;
          background-color: #f6f4ee;
          font-family: -apple-system, BlinkMacSystemFont, 'Noto Serif SC', 'Songti SC', 'Source Han Serif SC', serif;
          color: #0c1222;
        }}
        .email-wrapper {{
          max-width: 580px;
          margin: 30px auto;
          background: #ffffff;
          border-radius: 12px;
          border: 1px solid #e5e0d4;
          overflow: hidden;
          box-shadow: 0 4px 20px rgba(12, 18, 34, 0.06);
        }}
        .email-header {{
          background: #0c1222;
          padding: 24px 30px;
          color: #fcfbf9;
          text-align: center;
          border-bottom: 2px solid #b45309;
        }}
        .brand-title {{
          margin: 0;
          font-size: 20px;
          letter-spacing: 1px;
          font-weight: 700;
        }}
        .brand-sub {{
          margin: 6px 0 0 0;
          font-size: 12px;
          color: #d5d0c7;
        }}
        .email-body {{
          padding: 36px 30px;
          line-height: 1.7;
          color: #1f2937;
        }}
        .greeting {{
          font-size: 15px;
          font-weight: 600;
          margin-bottom: 12px;
        }}
        .action-desc {{
          font-size: 14px;
          color: #4b5563;
          margin-bottom: 24px;
        }}
        .code-display {{
          text-align: center;
          background: #fbf9f4;
          border: 1px dashed #d5d0c7;
          border-radius: 8px;
          padding: 20px;
          margin: 20px 0;
        }}
        .code-digits {{
          font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
          font-size: 32px;
          font-weight: 800;
          letter-spacing: 8px;
          color: #991b1b;
        }}
        .validity-tip {{
          font-size: 13px;
          color: #6b7280;
          margin-top: 10px;
        }}
        .security-notice {{
          font-size: 12px;
          color: #9ca3af;
          border-top: 1px solid #f3f0e8;
          padding-top: 18px;
          margin-top: 24px;
        }}
      </style>
    </head>
    <body>
      <div class="email-wrapper">
        <div class="email-header">
          <h1 class="brand-title">考研英语二写作智能评卷系统</h1>
          <p class="brand-sub">教育部考试大纲评分细则 · 智能研读台</p>
        </div>
        <div class="email-body">
          <div class="greeting">尊敬的考生用户：</div>
          <p class="action-desc">您正在进行<strong>【{action_name}】</strong>操作，请在验证码输入框中填入下方 6 位数字以完成身份核验：</p>
          
          <div class="code-display">
            <div class="code-digits">{code}</div>
            <div class="validity-tip">验证码有效期为 <strong>5 分钟</strong>。请勿泄露给他人。</div>
          </div>

          <div class="security-notice">
            * 若非您本人申请，请忽略此邮件，您的账号安全不会受到任何影响。
          </div>
        </div>
      </div>
    </body>
    </html>
    """


def send_verification_email(email: str, code: str, action_type: str = "login") -> Tuple[bool, str, Optional[str]]:
    """
    发送邮箱验证码
    返回: (是否成功, 提示消息, 模拟测试码[仅在未配置SMTP时提供])
    """
    action_dict = {
        "login": "快捷免密登录",
        "register": "账号注册",
        "reset_pwd": "重置密码"
    }
    action_name = action_dict.get(action_type, "账户验证")

    # 1. 检查是否开启真实 SMTP
    if not is_smtp_configured():
        # 本地开发仿真模式：在控制台高亮醒目输出
        sep = "=" * 65
        print("\n" + sep)
        print(f"[Email Service] 模拟邮件发送成功 (本地开发模式)")
        print(f"   收件人: {email}")
        print(f"   场景:   {action_name}")
        print(f"   验证码: {code} (5分钟内有效)")
        print(f"   提示:   如需真实发信，请在 .env 中配置 SMTP_SERVER、SMTP_USER、SMTP_PASSWORD")
        print(sep + "\n")
        return True, "验证码已成功发出，请查收邮件（开发模式已输出至控制台）", code

    # 2. 真实 SMTP 发送模式
    cfg = get_smtp_config()
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(f"【英语二评卷】您的{action_name}验证码为 {code}", "utf-8")
        msg["From"] = f"{Header(cfg['sender_name'], 'utf-8').encode()} <{cfg['user']}>"
        msg["To"] = email

        html_content = build_email_html(code=code, action_name=action_name, email=email)
        text_content = f"【考研英语二智能评卷系统】您的{action_name}验证码为：{code}，有效期 5 分钟。请勿泄露。"

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if cfg["use_ssl"]:
            server = smtplib.SMTP_SSL(cfg["server"], cfg["port"], timeout=10)
        else:
            server = smtplib.SMTP(cfg["server"], cfg["port"], timeout=10)
            server.starttls()

        server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["user"], [email], msg.as_string())
        server.quit()

        print(f"[OK] [Email Service] 真实邮件已成功发送至: {email}")
        return True, "验证码已发送至您的邮箱，请前往查收", None

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERR] [Email Service] 邮件发送失败: {str(e)}")
        # 回退友好模式：即使外网 SMTP 发信失败，也打印到控制台避免用户被完全卡死
        return False, f"邮件发送失败: {str(e)}", code
