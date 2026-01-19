import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import time
import hashlib

# 导入配置和AI客户端
from config import config, get_config, is_available, set_provider
from ai_client import AIClient

# 配置
PROMPT_TEMPLATE_FILE = os.getenv('PROMPT_TEMPLATE_FILE', 'prompt_template.txt')
DATA_DIR = 'data'
REPORT_DIR = 'report'

# 从环境变量或配置文件获取AI提供商
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower()

def load_prompt_template() -> str:
    """加载prompt模板文件"""
    try:
        if os.path.exists(PROMPT_TEMPLATE_FILE):
            with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                print("成功加载 prompt")
                return f.read().strip()
        else:
            # 如果文件不存在，返回默认模板
            print(f"⚠️  Prompt模板文件不存在: {PROMPT_TEMPLATE_FILE}，使用默认模板")
            return """请你将以下新闻翻译为中文。"""
    except Exception as e:
        print(f"⚠️  加载prompt模板失败: {e}，使用默认模板")
        return """请你将以下新闻翻译为中文。"""

def process_article_with_ai(ai_client: AIClient, article: Dict) -> Optional[Dict]:
    """
    使用AI处理单篇文章：
    1. 过滤低质量或不相关文章
    2. 提取关键信息
    3. 翻译为中文
    """
    if not ai_client:
        return None
    
    # 准备文章内容
    title = article.get('title', '')
    description = article.get('description', '')
    maintext = article.get('maintext', '')
    authors = article.get('authors', [])
    date_publish = article.get('date_publish', '')
    source = article.get('source_domain', '')
    
    # 如果正文太短，可能不是完整文章
    if not maintext or len(maintext) < 100:
        return None
    
    # 限制正文长度（避免token限制）
    maintext_preview = maintext[:3000] if len(maintext) > 3000 else maintext
    if len(maintext) > 3000:
        maintext_preview += "\n\n[文章内容较长，已截断]"
    
    # 加载并格式化prompt模板
    prompt_template = load_prompt_template()
    prompt = prompt_template.format(
        title=title,
        description=description,
        authors=', '.join(authors) if authors else '未知',
        date_publish=date_publish,
        source=source,
        maintext_preview=maintext_preview
    )

    try:
        # 使用统一的AI客户端接口
        response = ai_client.generate_content(prompt)
        
        # 检查错误
        if 'error' in response:
            error = response['error']
            if '安全过滤器' in error or 'SAFETY' in str(response.get('finish_reason', '')):
                print(f"  ⚠️  内容被安全过滤器阻止")
                # 返回基础数据
                return {
                    "original": {
                        "title": title,
                        "description": description,
                        "maintext": maintext,
                        "authors": authors,
                        "date_publish": date_publish,
                        "source_domain": source,
                        "url": article.get('url', ''),
                        "homepage_source": article.get('homepage_source', ''),
                    },
                    "processed": {
                        "is_valid": True,
                        "category": "其他",
                        "key_points": [],
                        "title_zh": "",
                        "description_zh": "",
                        "summary_zh": "内容被安全过滤器阻止，无法进行AI处理",
                        "maintext_zh": "",
                    },
                    "metadata": {
                        "processed_at": datetime.now().isoformat(),
                        "source": f"blocked_by_safety_filter_{ai_client.provider}"
                    }
                }
            else:
                print(f"  ⚠️  AI处理失败: {error}")
                return None
        
        result_text = response.get('text', '')
        if not result_text:
            print(f"  ⚠️  响应中没有文本内容")
            return None
        
        # 尝试提取JSON（可能返回markdown格式的代码块）
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            parts = result_text.split('```')
            for i, part in enumerate(parts):
                if i % 2 == 1:  # 代码块内容
                    try:
                        json.loads(part.strip())
                        result_text = part.strip()
                        break
                    except:
                        continue
        
        # 如果仍然包含JSON对象，尝试提取
        if '{' in result_text and '}' in result_text:
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            result_text = result_text[start:end]
        
        # 解析JSON
        ai_result = json.loads(result_text)
        
        # 合并原始数据和AI处理结果
        is_valid = ai_result.get('is_valid', False)
        
        # 如果文章无效（被过滤），确保所有字段为空
        if not is_valid:
            processed_article = {
                "original": {
                    "title": title,
                    "description": description,
                    "maintext": maintext,
                    "authors": authors,
                    "date_publish": date_publish,
                    "source_domain": source,
                    "url": article.get('url', ''),
                    "homepage_source": article.get('homepage_source', ''),
                },
                "processed": {
                    "is_valid": False,
                    "category": "",  # 无效文章，分类为空
                    "key_points": [],  # 无效文章，关键点为空
                    "title_zh": "",  # 无效文章，不翻译
                    "description_zh": "",  # 无效文章，不翻译
                    "summary_zh": "",  # 无效文章，不翻译
                    "maintext_zh": "",  # 无效文章，不翻译
                },
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "source": f"{ai_client.provider}-{ai_client.model_name}",
                    "filtered_reason": "非严肃新闻（花边/娱乐/体育/养生保健等）"
                }
            }
        else:
            # 有效文章，正常处理
            processed_article = {
                "original": {
                    "title": title,
                    "description": description,
                    "maintext": maintext,
                    "authors": authors,
                    "date_publish": date_publish,
                    "source_domain": source,
                    "url": article.get('url', ''),
                    "homepage_source": article.get('homepage_source', ''),
                },
                "processed": {
                    "is_valid": True,
                    "category": ai_result.get('category', '其他无关新闻'),
                    "key_points": ai_result.get('key_points', []),
                    "title_zh": ai_result.get('title_zh', ''),
                    "description_zh": ai_result.get('description_zh', ''),
                    "summary_zh": ai_result.get('summary_zh', ''),
                    "maintext_zh": ai_result.get('maintext_zh', ''),
                },
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "source": f"{ai_client.provider}-{ai_client.model_name}"
                }
            }
        
        return processed_article
        
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON解析失败: {e}")
        if 'result_text' in locals():
            print(f"  响应内容: {result_text[:200]}")
        return None
    except Exception as e:
        print(f"  ⚠️  AI处理失败: {e}")
        return None

def find_latest_articles_file() -> Optional[str]:
    """从data文件夹中查找最新的文章JSON文件"""
    if not os.path.exists(DATA_DIR):
        print(f"❌ 数据文件夹不存在: {DATA_DIR}")
        return None
    
    # 查找所有JSON文件
    json_files = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.isfile(filepath):
                mtime = os.path.getmtime(filepath)
                json_files.append((mtime, filepath, filename))
    
    if not json_files:
        print(f"❌ 在 {DATA_DIR} 文件夹中未找到JSON文件")
        return None
    
    # 按修改时间排序，返回最新的
    json_files.sort(reverse=True)
    latest_file = json_files[0][1]
    print(f"✓ 找到最新文章文件: {json_files[0][2]}")
    return latest_file

def get_article_id(article: Dict) -> str:
    """生成文章唯一ID（基于URL）"""
    url = article.get('url', '')
    if url:
        return hashlib.md5(url.encode()).hexdigest()
    # 如果没有URL，使用标题+来源的组合
    title = article.get('title', '')
    source = article.get('source_domain', '')
    return hashlib.md5(f"{title}_{source}".encode()).hexdigest()

def load_processed_cache(cache_file: str) -> Dict[str, Dict]:
    """加载已处理的文章缓存"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                print(f"  ✓ 加载缓存: {len(cache_data)} 篇已处理文章")
                return cache_data
        except Exception as e:
            print(f"  ⚠️  加载缓存失败: {e}")
            return {}
    return {}

def save_processed_cache(cache_file: str, processed_dict: Dict[str, Dict]):
    """保存已处理的文章缓存"""
    try:
        # 使用临时文件确保原子性写入
        temp_file = cache_file + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(processed_dict, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, cache_file)
    except Exception as e:
        print(f"  ⚠️  保存缓存失败: {e}")

def save_intermediate_results(processed_articles: List[Dict], report_dir: str):
    """保存中间结果"""
    try:
        intermediate_file = os.path.join(report_dir, 'report_intermediate.json')
        report = generate_report(processed_articles)
        with open(intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠️  保存中间结果失败: {e}")

def load_articles() -> List[Dict]:
    """加载文章数据（从data文件夹中加载最新的文件）"""
    # 优先使用环境变量指定的文件
    articles_file = os.getenv('ARTICLES_FILE')
    
    if articles_file:
        # 如果指定了文件，直接使用
        if not os.path.isabs(articles_file):
            articles_file = os.path.join(DATA_DIR, articles_file) if not os.path.exists(articles_file) else articles_file
    else:
        # 否则查找最新的文件
        articles_file = find_latest_articles_file()
    
    if not articles_file:
        return []
    
    try:
        with open(articles_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"✓ 成功加载 {len(articles)} 篇文章")
        return articles
    except FileNotFoundError:
        print(f"❌ 文件不存在: {articles_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return []

def generate_report(processed_articles: List[Dict]) -> Dict:
    """生成汇总报告"""
    total = len(processed_articles)
    valid_articles = [a for a in processed_articles if a['processed']['is_valid']]
    invalid_count = total - len(valid_articles)
    
    # 按分类统计
    category_stats = {}
    for article in valid_articles:
        category = article['processed']['category']
        category_stats[category] = category_stats.get(category, 0) + 1
    
    # 按来源统计
    source_stats = {}
    for article in valid_articles:
        source = article['original']['source_domain']
        source_stats[source] = source_stats.get(source, 0) + 1
    
    report = {
        "summary": {
            "total_articles": total,
            "valid_articles": len(valid_articles),
            "invalid_articles": invalid_count,
            "processing_date": datetime.now().isoformat(),
        },
        "statistics": {
            "by_category": category_stats,
            "by_source": source_stats,
        },
        "articles": valid_articles
    }
    
    return report

def generate_markdown_report(report: Dict) -> str:
    """生成Markdown格式的报告"""
    md = []
    
    # 标题
    md.append("# 尼日利亚新闻汇总报告\n")
    md.append(f"**生成时间**: {report['summary']['processing_date']}\n")
    
    # 摘要
    md.append("## 📊 数据摘要\n")
    md.append(f"- **总文章数**: {report['summary']['total_articles']}")
    md.append(f"- **有效文章**: {report['summary']['valid_articles']}")
    md.append(f"- **无效文章**: {report['summary']['invalid_articles']}\n")
    
    # 分类统计
    md.append("## 📁 分类统计\n")
    for category, count in sorted(report['statistics']['by_category'].items(), 
                                  key=lambda x: x[1], reverse=True):
        md.append(f"- **{category}**: {count} 篇")
    md.append("")
    
    # 来源统计
    md.append("## 📰 来源统计\n")
    for source, count in sorted(report['statistics']['by_source'].items(), 
                               key=lambda x: x[1], reverse=True):
        md.append(f"- **{source}**: {count} 篇")
    md.append("")
    
    # 文章列表
    md.append("## 📄 文章详情\n")
    md.append("---\n")
    
    for i, article in enumerate(report['articles'], 1):
        original = article['original']
        processed = article['processed']
        
        md.append(f"### {i}. {processed['title_zh'] or original['title']}\n")
        md.append(f"**原文标题**: {original['title']}\n")
        md.append(f"**分类**: {processed['category']}\n")
        md.append(f"**来源**: {original['source_domain']}\n")
        md.append(f"**作者**: {', '.join(original['authors']) if original['authors'] else '未知'}\n")
        md.append(f"**发布日期**: {original['date_publish']}\n")
        md.append(f"**链接**: {original['url']}\n")
        
        if processed['description_zh']:
            md.append(f"\n**描述**:\n{processed['description_zh']}\n")
        
        if processed['key_points']:
            md.append("\n**关键要点**:\n")
            for point in processed['key_points']:
                md.append(f"- {point}")
            md.append("")
        
        if processed['summary_zh']:
            md.append(f"\n**摘要**:\n{processed['summary_zh']}\n")
        
        if processed['maintext_zh']:
            md.append("\n**正文（中文）**:\n")
            md.append(f"{processed['maintext_zh']}\n")
        
        md.append("\n---\n")
    
    return "\n".join(md)

def generate_html_report(report: Dict) -> str:
    """生成HTML格式的报告"""
    html = []
    
    # HTML头部
    processing_date = report['summary']['processing_date']
    html.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>尼日利亚新闻汇总报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            margin: 10px 0;
            font-size: 16px;
        }}
        .summary-item strong {{
            color: #2980b9;
        }}
        .stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            min-width: 200px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-card h4 {{
            margin: 0 0 10px 0;
            color: #7f8c8d;
            font-size: 14px;
        }}
        .stat-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .article {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
            background: #fafafa;
        }}
        .article-header {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .article-title {{
            font-size: 20px;
            color: #2c3e50;
            margin: 0;
        }}
        .article-meta {{
            color: #7f8c8d;
            font-size: 14px;
            margin: 10px 0;
        }}
        .article-meta span {{
            margin-right: 15px;
        }}
        .key-points {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .key-points ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .key-points li {{
            margin: 8px 0;
        }}
        .content {{
            margin: 15px 0;
            line-height: 1.8;
        }}
        .link {{
            color: #3498db;
            text-decoration: none;
        }}
        .link:hover {{
            text-decoration: underline;
        }}
        .category-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            background: #3498db;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 尼日利亚新闻汇总报告</h1>
        <div class="summary">
            <div class="summary-item"><strong>生成时间</strong>: {processing_date}</div>
        </div>
    """)
    
    # 数据摘要
    total_articles = report['summary']['total_articles']
    valid_articles = report['summary']['valid_articles']
    invalid_articles = report['summary']['invalid_articles']
    html.append(f"""
        <h2>📊 数据摘要</h2>
        <div class="stats">
            <div class="stat-card">
                <h4>总文章数</h4>
                <div class="value">{total_articles}</div>
            </div>
            <div class="stat-card">
                <h4>有效文章</h4>
                <div class="value">{valid_articles}</div>
            </div>
            <div class="stat-card">
                <h4>无效文章</h4>
                <div class="value">{invalid_articles}</div>
            </div>
        </div>
    """)
    
    # 分类统计
    html.append("<h2>📁 分类统计</h2>")
    html.append('<div class="stats">')
    for category, count in sorted(report['statistics']['by_category'].items(), 
                                  key=lambda x: x[1], reverse=True):
        html.append(f"""
            <div class="stat-card">
                <h4>{category}</h4>
                <div class="value">{count} 篇</div>
            </div>
        """)
    html.append("</div>")
    
    # 来源统计
    html.append("<h2>📰 来源统计</h2>")
    html.append('<div class="stats">')
    for source, count in sorted(report['statistics']['by_source'].items(), 
                               key=lambda x: x[1], reverse=True):
        html.append(f"""
            <div class="stat-card">
                <h4>{source}</h4>
                <div class="value">{count} 篇</div>
            </div>
        """)
    html.append("</div>")
    
    # 文章列表
    html.append("<h2>📄 文章详情</h2>")
    
    for i, article in enumerate(report['articles'], 1):
        original = article['original']
        processed = article['processed']
        
        html.append('<div class="article">')
        html.append('<div class="article-header">')
        html.append(f'<h3 class="article-title">{i}. {processed["title_zh"] or original["title"]}</h3>')
        html.append(f'<span class="category-badge">{processed["category"]}</span>')
        html.append('</div>')
        
        html.append('<div class="article-meta">')
        html.append(f'<span><strong>原文标题</strong>: {original["title"]}</span>')
        html.append(f'<span><strong>来源</strong>: {original["source_domain"]}</span>')
        if original['authors']:
            html.append(f'<span><strong>作者</strong>: {", ".join(original["authors"])}</span>')
        if original['date_publish']:
            html.append(f'<span><strong>发布日期</strong>: {original["date_publish"]}</span>')
        html.append('</div>')
        
        if original['url']:
            html.append(f'<p><a href="{original["url"]}" class="link" target="_blank">查看原文</a></p>')
        
        if processed['description_zh']:
            html.append(f'<div class="content"><strong>描述</strong>:<br>{processed["description_zh"]}</div>')
        
        if processed['key_points']:
            html.append('<div class="key-points"><strong>关键要点</strong>:<ul>')
            for point in processed['key_points']:
                html.append(f'<li>{point}</li>')
            html.append('</ul></div>')
        
        if processed['summary_zh']:
            html.append(f'<div class="content"><strong>摘要</strong>:<br>{processed["summary_zh"]}</div>')
        
        if processed['maintext_zh']:
            html.append(f'<div class="content"><strong>正文（中文）</strong>:<br>{processed["maintext_zh"]}</div>')
        
        html.append('</div>')
    
    # HTML尾部
    html.append("""
    </div>
</body>
</html>
    """)
    
    return "\n".join(html)

def main():
    """主函数"""
    print("=" * 60)
    print("AI新闻处理与报告生成")
    print("=" * 60)
    
    # 显示配置状态
    config.print_status()
    
    # 获取AI提供商（使用局部变量避免作用域问题）
    current_provider = AI_PROVIDER
    
    # 初始化AI客户端
    if not is_available(current_provider):
        print(f"\n⚠️  {current_provider} 不可用，尝试查找可用的提供商...")
        available = config.get_available_providers()
        if available:
            current_provider = available[0]
            print(f"✓ 使用 {current_provider} 作为AI提供商")
        else:
            print("\n❌ 没有可用的AI提供商")
            print("   请设置相应的API密钥环境变量：")
            print("   - GEMINI_API_KEY (for gemini)")
            print("   - DASHSCOPE_API_KEY (for tongyi)")
            print("   - DEEPSEEK_API_KEY (for deepseek)")
            print("   - OPENAI_API_KEY (for openai)")
            print("   - ANTHROPIC_API_KEY (for claude)")
            print("   - TENCENT_SECRET_ID & TENCENT_SECRET_KEY (for hunyuan)")
            return
    
    try:
        ai_client = AIClient(current_provider)
        print(f"✓ AI客户端初始化成功: {ai_client.provider} ({ai_client.model_name})")
    except Exception as e:
        print(f"\n❌ AI客户端初始化失败: {e}")
        print("   将使用基础处理模式（无AI功能）")
        ai_client = None
    
    # 加载文章
    print(f"\n📂 加载文章数据...")
    articles = load_articles()
    
    if not articles:
        print("❌ 没有可处理的文章")
        return
    
    # 创建报告目录和缓存文件路径
    today = datetime.now().strftime("%Y%m%d")
    report_date_dir = os.path.join(REPORT_DIR, today)
    os.makedirs(report_date_dir, exist_ok=True)
    cache_file = os.path.join(report_date_dir, 'processed_cache.json')
    
    # 加载已处理的文章缓存（断点续传）
    print(f"\n📋 检查已处理缓存...")
    processed_cache = load_processed_cache(cache_file)
    if processed_cache:
        print(f"  ✓ 发现 {len(processed_cache)} 篇已处理文章，将跳过这些文章")
    
    # 处理文章
    print(f"\n🤖 使用AI处理文章...")
    processed_articles = []
    save_interval = 5  # 每处理5篇文章保存一次中间结果
    skipped_count = 0
    
    try:
        for i, article in enumerate(articles, 1):
            article_id = get_article_id(article)
            
            # 检查是否已处理（断点续传）
            if article_id in processed_cache:
                print(f"\n[{i}/{len(articles)}] ⏭️  跳过（已处理）: {article.get('title', '无标题')[:50]}...")
                processed_articles.append(processed_cache[article_id])
                skipped_count += 1
                continue
            
            print(f"\n[{i}/{len(articles)}] 处理: {article.get('title', '无标题')[:50]}...")
            
            if ai_client:
                processed = process_article_with_ai(ai_client, article)
                if processed:
                    processed_articles.append(processed)
                    # 立即保存到缓存（断点续传）
                    processed_cache[article_id] = processed
                    save_processed_cache(cache_file, processed_cache)
                    
                    # 每处理N篇保存一次中间结果
                    new_processed_count = len(processed_articles) - skipped_count
                    if new_processed_count > 0 and new_processed_count % save_interval == 0:
                        print(f"  💾 保存中间结果（已处理 {len(processed_articles)} 篇，其中新处理 {new_processed_count} 篇）...")
                        save_intermediate_results(processed_articles, report_date_dir)
                    
                    if processed['processed']['is_valid']:
                        print(f"  ✓ 有效文章 - 分类: {processed['processed']['category']}")
                    else:
                        print(f"  ✗ 无效文章（已过滤）")
                else:
                    print(f"  ⚠️  处理失败")
                    # 检查是否是余额不足错误，如果是，提示用户
                    if i == 1:  # 只在第一篇文章失败时提示
                        print(f"\n💡 提示: 如果看到'余额不足'错误，可以：")
                        print(f"   1. 为当前AI提供商充值")
                        print(f"   2. 切换到其他可用提供商: export AI_PROVIDER='gemini' 或 'tongyi'")
                        print(f"   3. 查看可用提供商: python -c 'from config import config; config.print_status()'")
                
                # 添加延迟，避免API限流
                time.sleep(1)
            else:
                # 如果没有AI模型，使用基础处理
                processed = {
                    "original": {
                        "title": article.get('title', ''),
                        "description": article.get('description', ''),
                        "maintext": article.get('maintext', ''),
                        "authors": article.get('authors', []),
                        "date_publish": article.get('date_publish', ''),
                        "source_domain": article.get('source_domain', ''),
                        "url": article.get('url', ''),
                        "homepage_source": article.get('homepage_source', ''),
                    },
                    "processed": {
                        "is_valid": bool(article.get('maintext')),
                        "category": "其他",
                        "key_points": [],
                        "title_zh": "",
                        "description_zh": "",
                        "summary_zh": "",
                        "maintext_zh": "",
                    },
                    "metadata": {
                        "processed_at": datetime.now().isoformat(),
                        "source": "basic"
                    }
                }
                processed_articles.append(processed)
                processed_cache[article_id] = processed
                save_processed_cache(cache_file, processed_cache)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，保存已处理的结果...")
    except Exception as e:
        print(f"\n\n❌ 处理过程出错: {e}")
        print("💾 尝试保存已处理的结果...")
    finally:
        # 无论是否异常，都保存已处理的结果
        if processed_articles:
            print(f"\n💾 保存最终结果（共 {len(processed_articles)} 篇，其中跳过 {skipped_count} 篇）...")
            save_intermediate_results(processed_articles, report_date_dir)
    
    # 生成最终报告（使用已处理的结果）
    if not processed_articles:
        print("\n⚠️  没有已处理的文章，无法生成报告")
        return
    
    print(f"\n📊 生成最终报告...")
    report = generate_report(processed_articles)
    
    # 保存JSON报告
    report_json_file = os.path.join(report_date_dir, 'report.json')
    with open(report_json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON报告已保存: {report_json_file}")
    
    # 生成并保存Markdown报告
    md_report = generate_markdown_report(report)
    report_md_file = os.path.join(report_date_dir, 'report.md')
    with open(report_md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"✓ Markdown报告已保存: {report_md_file}")
    
    # 生成并保存HTML报告
    html_report = generate_html_report(report)
    report_html_file = os.path.join(report_date_dir, 'report.html')
    with open(report_html_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"✓ HTML报告已保存: {report_html_file}")
    
    # 清理中间结果文件（保留最终报告）
    intermediate_file = os.path.join(report_date_dir, 'report_intermediate.json')
    if os.path.exists(intermediate_file):
        try:
            os.remove(intermediate_file)
            print(f"✓ 已清理中间结果文件")
        except:
            pass
    
    # 打印摘要
    print(f"\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
    print(f"总文章数: {report['summary']['total_articles']}")
    print(f"有效文章: {report['summary']['valid_articles']}")
    print(f"无效文章: {report['summary']['invalid_articles']}")
    print(f"\n分类统计:")
    for category, count in sorted(report['statistics']['by_category'].items(), 
                                  key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count} 篇")

if __name__ == '__main__':
    main()
