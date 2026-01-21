#!/usr/bin/env python3
"""
Send report email
Automatically send email after run.py execution completes
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from zoneinfo import ZoneInfo
import glob

# Nigeria timezone (Africa/Lagos, UTC+1)
NIGERIA_TZ = ZoneInfo('Africa/Lagos')
EMAIL_TEMPLATE_FILE = os.getenv('EMAIL_TEMPLATE_FILE', 'email_template.txt')

def get_greeting():
    """Get greeting based on Nigeria time, with weather information"""
    try:
        # Import greeting generator
        from greeting import generate_greeting
        # Generate greeting using AI (will fallback to default if AI fails)
        result = generate_greeting(use_ai=True, include_weather=True)
        
        # Handle both string (legacy) and dict (new) return types
        if isinstance(result, dict):
            return result
        else:
            # Legacy string format, convert to dict
            return {
                'greeting': result,
                'weather_summary': '',
                'weather_advice': ''
            }
    except ImportError:
        # Fallback if greeting module is not available
        print("  ⚠️  问候语生成模块未找到，使用默认问候语")
        return {
            'greeting': "你好！",
            'weather_summary': '',
            'weather_advice': ''
        }
    except Exception as e:
        # Fallback on any error
        print(f"  ⚠️  生成问候语时出错: {str(e)[:50]}，使用默认问候语")
        return {
            'greeting': "你好！",
            'weather_summary': '',
            'weather_advice': ''
        }

def load_email_template():
    """Load email template from file"""
    try:
        if os.path.exists(EMAIL_TEMPLATE_FILE):
            with open(EMAIL_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            # Fallback to default template if file doesn't exist
            print(f"⚠️  邮件模板文件不存在: {EMAIL_TEMPLATE_FILE}，使用默认模板")
            return """{greeting}

今日新闻处理完成！

日期: {date}
时间: {time}
{weather_section}

报告文件:
{report_files}

{log_file_info}

所有文件已作为附件发送。"""
    except Exception as e:
        print(f"⚠️  加载邮件模板失败: {e}，使用默认模板")
        return """{greeting}

今日新闻处理完成！

日期: {date}
时间: {time}
{weather_section}

报告文件:
{report_files}

{log_file_info}

所有文件已作为附件发送。"""

def send_report_email():
    """Send report email"""
    # Read configuration from environment variables
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    email_to = os.getenv('EMAIL_TO')
    
    if not all([smtp_user, smtp_password, email_to]):
        print("⚠️  邮件配置不完整，跳过发送")
        print("   需要设置环境变量: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO")
        return False
    
    # Support multiple email addresses (comma-separated)
    # Clean email addresses (remove spaces)
    email_list = [email.strip() for email in email_to.split(',')]
    email_to_clean = ', '.join(email_list)  # For display
    
    # Find latest report
    today = datetime.now().strftime("%Y%m%d")
    report_dir = f'report/{today}'
    
    if not os.path.exists(report_dir):
        print(f"⚠️  报告目录不存在: {report_dir}")
        return False
    
    # Check report files
    report_files = {
        'html': f'{report_dir}/report.html',
        'json': f'{report_dir}/report.json',
        'md': f'{report_dir}/report.md',
    }
    
    existing_files = {k: v for k, v in report_files.items() if os.path.exists(v)}
    
    if not existing_files:
        print(f"⚠️  报告目录中没有找到报告文件: {report_dir}")
        return False
    
    print(f"\n📧 准备发送邮件到: {email_to_clean}")
    print(f"   收件人数量: {len(email_list)} 个邮箱")
    
    # Get current time in Nigeria timezone
    now_nigeria = datetime.now(NIGERIA_TZ)
    greeting_data = get_greeting()
    
    # Extract greeting and weather info
    greeting = greeting_data.get('greeting', '你好！') if isinstance(greeting_data, dict) else greeting_data
    weather_summary = greeting_data.get('weather_summary', '') if isinstance(greeting_data, dict) else ''
    weather_advice = greeting_data.get('weather_advice', '') if isinstance(greeting_data, dict) else ''
    
    # Load email template
    template = load_email_template()
    
    # Prepare template variables
    report_files_list = []
    for name, filepath in existing_files.items():
        report_files_list.append(f"  - report.{name}")
    report_files_text = "\n".join(report_files_list) if report_files_list else "  (无)"
    
    # Add log file information
    log_files = glob.glob('log/run_*.log')
    log_file_info = ""
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        log_file_info = f"日志文件: {os.path.basename(latest_log)}"
    else:
        log_file_info = ""
    
    # Format weather section
    weather_section = ""
    if weather_summary:
        weather_section = f"\n\n天气信息：\n{weather_summary}"
        if weather_advice:
            weather_section += f"\n\n天气建议：\n{weather_advice}"
    
    # Format email body using template
    body = template.format(
        greeting=greeting,
        date=now_nigeria.strftime("%Y-%m-%d"),
        time=now_nigeria.strftime("%H:%M:%S"),
        report_files=report_files_text,
        log_file_info=log_file_info,
        weather_section=weather_section
    )
    
    print(f"  📝 使用问候语: {greeting}")
    if weather_summary:
        print(f"  🌤️  已包含天气信息")
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_to_clean  # Multiple emails separated by comma
    msg['Subject'] = f'每日新闻报告 - {now_nigeria.strftime("%Y-%m-%d")}'
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Add attachments
    attachments_added = 0
    for name, filepath in existing_files.items():
        try:
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(filepath)}'
                )
                msg.attach(part)
                attachments_added += 1
                print(f"  ✓ 添加附件: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ⚠️  添加附件失败 {filepath}: {e}")
    
    # Add latest log file
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        try:
            with open(latest_log, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(latest_log)}'
                )
                msg.attach(part)
                attachments_added += 1
                print(f"  ✓ 添加附件: {os.path.basename(latest_log)}")
        except Exception as e:
            print(f"  ⚠️  添加日志文件失败: {e}")
    
    if attachments_added == 0:
        print("  ⚠️  没有可附加的文件")
        return False
    
    # Send email
    try:
        print(f"  🔄 连接到邮件服务器: {smtp_host}:{smtp_port}")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"  ✓ 邮件已成功发送到: {email_to_clean}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ❌ 邮件认证失败: {e}")
        print("   提示: 如果使用 Gmail，请使用'应用专用密码'而不是普通密码")
        return False
    except Exception as e:
        print(f"  ❌ 发送邮件失败: {e}")
        return False

if __name__ == '__main__':
    send_report_email()
