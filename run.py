#!/usr/bin/env python3
"""
Complete workflow for news crawling and AI processing
Chains together crawl.py and process_with_ai.py functionality
"""

import os
import sys
import subprocess
from datetime import datetime
import time

class TeeOutput:
    """Class to output to both terminal and file simultaneously"""
    def __init__(self, file_path):
        self.terminal = sys.stdout
        self.log_file = open(file_path, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        self.log_file.write(message)
        self.log_file.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log_file.flush()
    
    def close(self):
        if self.log_file:
            self.log_file.close()

def run_crawl():
    """Execute crawler script"""
    print("=" * 60)
    print("步骤 1/2: 新闻爬取")
    print("=" * 60)
    
    try:
        # Directly execute crawl.py
        result = subprocess.run(
            [sys.executable, 'crawl.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True,
            capture_output=False
        )
        print("\n✓ 爬取完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 爬取失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 爬取过程出错: {e}")
        return False

def run_ai_processing():
    """Execute AI processing script"""
    print("\n" + "=" * 60)
    print("步骤 2/2: AI处理与报告生成")
    print("=" * 60)
    
    try:
        # Import and execute main function from process_with_ai
        from process_with_ai import main as process_main
        process_main()
        print("\n✓ AI处理完成")
        return True
    except ImportError as e:
        print(f"\n❌ 导入 process_with_ai 失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ AI处理过程出错: {e}")
        return False

def main():
    """Main function: execute complete workflow"""
    start_time = datetime.now()
    
    # Create log directory
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file (named with timestamp)
    timestamp = start_time.strftime('%Y%m%d_%H%M%S')
    log_file_path = os.path.join(log_dir, f'run_{timestamp}.log')
    
    # Set up simultaneous output to terminal and file
    tee = TeeOutput(log_file_path)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        sys.stdout = tee
        sys.stderr = tee
        
        print("\n" + "=" * 60)
        print("🚀 开始执行完整工作流程")
        print("=" * 60)
        print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"日志文件: {log_file_path}")
        print()
        
        # Step 1: Crawl news
        crawl_success = run_crawl()
        
        if not crawl_success:
            print("\n⚠️  爬取失败，但继续尝试AI处理（如果有已存在的文章文件）...")
        
        # Wait a short time to ensure file is written
        time.sleep(2)
        
        # Step 2: AI processing
        ai_success = run_ai_processing()
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 工作流程执行总结")
        print("=" * 60)
        print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration}")
        print()
        
        if crawl_success and ai_success:
            print("✅ 完整工作流程执行成功！")
            print("\n生成的文件：")
            today = datetime.now().strftime("%Y%m%d")
            report_dir = os.path.join('report', today)
            if os.path.exists(report_dir):
                print(f"  📁 报告目录: {report_dir}/")
                for file in ['report.json', 'report.md', 'report.html']:
                    filepath = os.path.join(report_dir, file)
                    if os.path.exists(filepath):
                        print(f"     ✓ {file}")
            print(f"\n📝 完整日志已保存到: {log_file_path}")
            exit_code = 0
        elif crawl_success:
            print("⚠️  爬取成功，但AI处理失败")
            print(f"\n📝 完整日志已保存到: {log_file_path}")
            exit_code = 1
        elif ai_success:
            print("⚠️  爬取失败，但AI处理成功（可能使用了已存在的文章文件）")
            print(f"\n📝 完整日志已保存到: {log_file_path}")
            exit_code = 1
        else:
            print("❌ 工作流程执行失败")
            print(f"\n📝 完整日志已保存到: {log_file_path}")
            exit_code = 2
        
        # Send email (if email is configured)
        try:
            from send_email import send_report_email
            print("\n" + "=" * 60)
            print("📧 发送邮件通知")
            print("=" * 60)
            send_report_email()
        except ImportError:
            print("\n⚠️  邮件发送模块未找到，跳过邮件发送")
        except Exception as e:
            print(f"\n⚠️  邮件发送失败: {e}")
        
        return exit_code
    
    finally:
        # Restore standard output
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        tee.close()

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
