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
import glob

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
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_to_clean  # Multiple emails separated by comma
    msg['Subject'] = f'每日新闻报告 - {datetime.now().strftime("%Y-%m-%d")}'
    
    # Email body
    body = f"""
    今日新闻处理完成！
    
    日期: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    报告文件:
    """
    for name, filepath in existing_files.items():
        body += f"  - report.{name}\n"
    
    # Add log file information
    log_files = glob.glob('log/run_*.log')
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        body += f"\n    日志文件: {os.path.basename(latest_log)}\n"
    
    body += "\n    所有文件已作为附件发送。"
    
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
