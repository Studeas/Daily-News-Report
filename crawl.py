from newsplease import NewsPlease
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import os

LIMIT_NUM = 25

# 新闻平台首页列表
homepage_urls = [
    'https://punchng.com/',
    'https://dailypost.ng/',
    'https://dailytrust.com/',
    'https://thesun.ng/',
    # 'https://guardian.ng/'
]

# 设置请求头，模拟浏览器访问以避免 403 错误
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

request_args = {'headers': headers}

def extract_article_links(homepage_url, soup):
    """
    从首页HTML中提取新闻文章链接和标题
    这个方法需要根据每个网站的具体HTML结构来调整
    """
    article_links = []
    base_domain = urlparse(homepage_url).netloc
    
    # 常见的新闻链接选择器（需要根据实际网站调整）
    # 尝试多种可能的选择器
    selectors = [
        'article a',           # 文章标签内的链接
        '.post a',             # 文章类内的链接
        '.article a',          # article类内的链接
        'h2 a', 'h3 a',        # 标题内的链接
        '.entry-title a',      # 标题类内的链接
        '.news-item a',        # 新闻项内的链接
        'a[href*="/article/"]',  # 包含/article/的链接
        'a[href*="/news/"]',      # 包含/news/的链接
        'a[href*="/story/"]',     # 包含/story/的链接
    ]
    
    found_links = set()  # 用于去重
    
    for selector in selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            # 转换为绝对URL
            full_url = urljoin(homepage_url, href)
            parsed = urlparse(full_url)
            
            # 过滤条件：只保留同域名的链接，排除首页、分类页等
            if (parsed.netloc == base_domain and 
                full_url not in found_links and
                full_url != homepage_url and
                not any(x in full_url.lower() for x in ['/category/', '/tag/', '/author/', '/page/', '/archive/'])):
                
                title = link.get_text(strip=True)
                if title and len(title) > 10:  # 标题长度过滤
                    found_links.add(full_url)
                    article_links.append({
                        'title': title,
                        'url': full_url,
                        'source': homepage_url
                    })
    
    # 如果上面的选择器没找到，尝试更通用的方法
    if not article_links:
        # 查找所有链接，过滤出可能是文章的链接
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            full_url = urljoin(homepage_url, href)
            parsed = urlparse(full_url)
            
            if (parsed.netloc == base_domain and 
                full_url not in found_links and
                full_url != homepage_url and
                len(full_url) > len(homepage_url) + 10 and  # URL长度过滤
                not any(x in full_url.lower() for x in ['/category/', '/tag/', '/author/', '/page/', '/archive/', '#'])):
                
                title = link.get_text(strip=True)
                if title and len(title) > 10:
                    found_links.add(full_url)
                    article_links.append({
                        'title': title,
                        'url': full_url,
                        'source': homepage_url
                    })
    
    # 去重并限制数量
    seen = set()
    unique_links = []
    for item in article_links:
        if item['url'] not in seen:
            seen.add(item['url'])
            unique_links.append(item)
            if len(unique_links) >= LIMIT_NUM:
                break
    
    return unique_links

def serialize_article(article):
    """将文章对象或字典转换为可序列化的字典"""
    if article is None:
        return None
    
    # 如果已经是字典，直接使用
    if isinstance(article, dict):
        data = article
    # 如果是对象，转换为字典
    elif hasattr(article, '__dict__'):
        data = article.__dict__
    else:
        # 其他类型，直接返回
        return article
    
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            # 将 datetime 转换为字符串
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            # 递归处理嵌套字典
            result[key] = serialize_article(value)
        elif hasattr(value, '__dict__'):
            # 递归处理嵌套对象
            result[key] = serialize_article(value)
        elif isinstance(value, (list, tuple)):
            # 处理列表和元组
            result[key] = [serialize_article(item) for item in value]
        else:
            # 其他类型直接赋值
            result[key] = value
    return result

# 主程序
print("=" * 60)
print("开始抓取新闻...")
print("=" * 60)

all_articles = []
total_links_found = 0
total_articles_extracted = 0

# 第一步：从每个首页提取新闻链接
for homepage_url in homepage_urls:
    print(f"\n📰 处理首页: {homepage_url}")
    try:
        # 获取首页HTML
        response = requests.get(homepage_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取新闻链接
        article_links = extract_article_links(homepage_url, soup)
        total_links_found += len(article_links)
        
        print(f"  ✓ 找到 {len(article_links)} 个新闻链接")
        
        # 第二步：对每个链接提取文章内容
        for i, link_info in enumerate(article_links, 1):
            article_url = link_info['url']
            homepage_title = link_info['title']
            
            print(f"  [{i}/{len(article_links)}] 提取: {homepage_title[:50]}...")
            
            try:
                # 使用 newsplease 提取文章内容
                article = NewsPlease.from_url(article_url, request_args=request_args)
                
                if article and article.title:
                    # 序列化文章数据
                    article_data = serialize_article(article)
                    
                    # 添加首页信息
                    if article_data:
                        article_data['homepage_title'] = homepage_title
                        article_data['homepage_source'] = homepage_url
                        article_data['extracted_at'] = datetime.now().isoformat()
                    
                    all_articles.append(article_data)
                    total_articles_extracted += 1
                    print(f"    ✓ 成功提取")
                else:
                    print(f"    ✗ 无法提取内容")
                
                # 添加延迟，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"    ✗ 提取失败: {str(e)[:50]}")
                continue
        
    except Exception as e:
        print(f"  ✗ 处理首页失败: {str(e)}")
        continue

# 第三步：保存到JSON文件
print(f"\n" + "=" * 60)
print(f"抓取完成！")
print(f"  找到链接: {total_links_found} 个")
print(f"  成功提取: {total_articles_extracted} 篇文章")
print("=" * 60)


time_stamp = datetime.today().date()
output_dir = 'data'
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f'news_{time_stamp}.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)

print(f"\n✅ 所有文章数据已保存到 {output_file}")
print(f"   共 {len(all_articles)} 篇文章")
