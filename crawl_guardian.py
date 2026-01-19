#!/usr/bin/env python3
"""
Guardian.ng 新闻抓取补丁程序
由于guardian.ng使用了Cloudflare保护，需要特殊处理
"""

from newsplease import NewsPlease
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import os

# 尝试导入cloudscraper（专门用于绕过Cloudflare）
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

# 尝试导入selenium（用于模拟真实浏览器）
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Guardian.ng 特定配置
GUARDIAN_HOMEPAGE = 'https://guardian.ng/'

# 增强的请求头，模拟真实浏览器
def get_headers():
    """获取请求头，支持多种User-Agent轮换"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    import random
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Referer': 'https://www.google.com/',
    }

# request_args会在运行时动态生成

def extract_guardian_article_links(homepage_url, soup):
    """
    专门针对guardian.ng的链接提取方法
    尝试多种选择器策略
    """
    article_links = []
    base_domain = urlparse(homepage_url).netloc
    found_links = set()
    
    # Guardian.ng 特定的选择器
    guardian_selectors = [
        # 尝试常见的WordPress/新闻主题选择器
        'article a',
        '.post a',
        '.entry-title a',
        '.post-title a',
        'h1 a', 'h2 a', 'h3 a', 'h4 a',
        '.title a',
        '.headline a',
        '.news-title a',
        '.article-title a',
        # 尝试特定的类名
        '.story-link',
        '.article-link',
        '.news-link',
        # 尝试包含特定路径的链接
        'a[href*="/news/"]',
        'a[href*="/article/"]',
        'a[href*="/story/"]',
        'a[href*="/202"]',  # 包含年份的链接（通常是文章）
        # 尝试列表项中的链接
        'li.article a',
        'li.post a',
        'li.news-item a',
        '.list-item a',
        '.item a',
    ]
    
    print(f"  🔍 尝试 {len(guardian_selectors)} 种选择器策略...")
    
    for selector in guardian_selectors:
        try:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # 转换为绝对URL
                full_url = urljoin(homepage_url, href)
                parsed = urlparse(full_url)
                
                # 过滤条件
                if (parsed.netloc == base_domain and 
                    full_url not in found_links and
                    full_url != homepage_url and
                    not any(x in full_url.lower() for x in [
                        '/category/', '/tag/', '/author/', '/page/', 
                        '/archive/', '/search/', '/contact/', '/about/',
                        '/privacy/', '/terms/', '/sitemap/', '/feed/',
                        '/amp/', '/#', 'javascript:', 'mailto:'
                    ]) and
                    len(full_url) > len(homepage_url) + 10):  # URL长度过滤
                    
                    # 尝试获取标题
                    title = None
                    # 先尝试从链接文本获取
                    title = link.get_text(strip=True)
                    # 如果链接文本为空，尝试从父元素获取
                    if not title or len(title) < 10:
                        parent = link.parent
                        if parent:
                            title = parent.get_text(strip=True)
                    # 如果还是为空，尝试从data属性获取
                    if not title or len(title) < 10:
                        title = link.get('title', '') or link.get('data-title', '')
                    
                    if title and len(title) > 10:
                        found_links.add(full_url)
                        article_links.append({
                            'title': title,
                            'url': full_url,
                            'source': homepage_url
                        })
        except Exception as e:
            continue
    
    # 如果上面的选择器都没找到，尝试更通用的方法
    if not article_links:
        print(f"  ⚠️  标准选择器未找到链接，尝试通用方法...")
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if not href:
                continue
            
            full_url = urljoin(homepage_url, href)
            parsed = urlparse(full_url)
            
            # 更严格的过滤
            if (parsed.netloc == base_domain and 
                full_url not in found_links and
                full_url != homepage_url and
                len(full_url) > len(homepage_url) + 15 and  # 更长的URL通常是文章
                not any(x in full_url.lower() for x in [
                    '/category/', '/tag/', '/author/', '/page/', '/archive/',
                    '/search/', '/contact/', '/about/', '/privacy/', '/terms/',
                    '/sitemap/', '/feed/', '/amp/', '/#', 'javascript:', 'mailto:',
                    '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip'
                ]) and
                # 检查URL路径是否包含日期或文章标识
                (any(x in full_url.lower() for x in ['/news/', '/article/', '/story/', '/202', '/2025', '/2026']) or
                 len(parsed.path.split('/')) >= 3)):  # 路径至少3段
                
                title = link.get_text(strip=True)
                if not title or len(title) < 10:
                    # 尝试从父元素获取
                    parent = link.parent
                    if parent:
                        title = parent.get_text(strip=True)
                
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
            if len(unique_links) >= 20:  # 限制最多20条
                break
    
    return unique_links

def serialize_article(article):
    """将文章对象或字典转换为可序列化的字典"""
    if article is None:
        return None
    
    if isinstance(article, dict):
        data = article
    elif hasattr(article, '__dict__'):
        data = article.__dict__
    else:
        return article
    
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_article(value)
        elif hasattr(value, '__dict__'):
            result[key] = serialize_article(value)
        elif isinstance(value, (list, tuple)):
            result[key] = [serialize_article(item) for item in value]
        else:
            result[key] = value
    return result

def try_selenium_method():
    """使用Selenium模拟真实浏览器获取文章链接"""
    article_links = []
    driver = None
    
    try:
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 尝试创建Chrome驱动
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            if 'chromedriver' in str(e).lower() or 'path' in str(e).lower():
                print(f"    ⚠️  Chrome驱动未找到，请安装: sudo apt-get install chromium-chromedriver")
                print(f"    或下载: https://chromedriver.chromium.org/")
                return []
            raise
        
        # 访问首页
        print(f"    🔄 访问首页: {GUARDIAN_HOMEPAGE}")
        driver.get(GUARDIAN_HOMEPAGE)
        
        # 等待页面加载（等待Cloudflare验证完成）
        try:
            WebDriverWait(driver, 15).until(
                lambda d: 'Just a moment' not in d.page_source and 
                         'challenge-platform' not in d.page_source
            )
            print(f"    ✓ 页面加载完成")
        except TimeoutException:
            print(f"    ⚠️  页面加载超时（可能仍在Cloudflare验证中）")
            # 继续尝试解析
        
        # 解析页面获取链接
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = extract_guardian_article_links(GUARDIAN_HOMEPAGE, soup)
        article_links.extend(links)
        
        # 如果首页没有找到，尝试访问分类页面
        if not article_links:
            news_sections = [
                'https://guardian.ng/news/',
                'https://guardian.ng/politics/',
                'https://guardian.ng/business/',
            ]
            
            for section_url in news_sections:
                try:
                    print(f"    🔄 访问分类页面: {section_url}")
                    driver.get(section_url)
                    time.sleep(3)  # 等待页面加载
                    
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    section_links = extract_guardian_article_links(section_url, soup)
                    if section_links:
                        article_links.extend(section_links)
                        print(f"    ✓ 从 {section_url} 提取了 {len(section_links)} 个链接")
                        if len(article_links) >= 20:
                            break
                except Exception as e:
                    continue
        
        return article_links
        
    except Exception as e:
        print(f"    ⚠️  Selenium方法失败: {str(e)[:50]}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def crawl_guardian():
    """专门抓取Guardian.ng的新闻"""
    print("=" * 60)
    print("Guardian.ng 新闻抓取补丁程序")
    print("=" * 60)
    
    all_articles = []
    total_links_found = 0
    total_articles_extracted = 0
    article_links = []  # 初始化
    
    print(f"\n📰 处理首页: {GUARDIAN_HOMEPAGE}")
    
    try:
        # 策略1: 尝试使用Selenium（最可靠，但需要浏览器驱动）
        if SELENIUM_AVAILABLE:
            print(f"  🔄 尝试使用Selenium（模拟真实浏览器）...")
            article_links = try_selenium_method()
            if article_links:
                print(f"  ✓ Selenium方法成功，找到 {len(article_links)} 个链接")
            else:
                print(f"  ⚠️  Selenium方法失败，尝试其他方法...")
        
        # 策略2: 如果Selenium失败或不可用，尝试cloudscraper
        if not article_links:
            print(f"  🔄 尝试使用cloudscraper...")
            if CLOUDSCRAPER_AVAILABLE:
                print(f"  ✓ 使用 cloudscraper 库（专门绕过Cloudflare）")
                session = cloudscraper.create_scraper()
                session.headers.update(get_headers())
            else:
                session = requests.Session()
                session.headers.update(get_headers())
        
        # 方法1: 直接尝试RSS feed（不访问首页）
        rss_urls = [
            'https://guardian.ng/feed/',
            'https://guardian.ng/rss/',
            'https://guardian.ng/news/feed/',
            'https://guardian.ng/feed/rss/',
            'https://guardian.ng/?feed=rss2',
        ]
        
        rss_success = False
        
        for rss_url in rss_urls:
            try:
                print(f"  🔄 尝试RSS feed: {rss_url}")
                rss_response = session.get(rss_url, timeout=10, allow_redirects=True)
                print(f"    状态码: {rss_response.status_code}")
                if rss_response.status_code == 200:
                    content_type = rss_response.headers.get('content-type', '').lower()
                    content = rss_response.text
                    
                    # 检查是否是有效的RSS/XML内容
                    if ('xml' in content_type or 'rss' in content_type or 'atom' in content_type or 
                        content.strip().startswith('<?xml') or '<rss' in content or '<feed' in content):
                        print(f"  ✓ 找到RSS feed: {rss_url}")
                        # 解析RSS
                        try:
                            from xml.etree import ElementTree as ET
                            root = ET.fromstring(rss_response.content)
                            
                            # 提取RSS中的文章链接
                            for item in root.findall('.//item'):
                                title_elem = item.find('title')
                                link_elem = item.find('link')
                                if title_elem is not None and link_elem is not None:
                                    title = title_elem.text or ''
                                    url = link_elem.text or ''
                                    if title and url:
                                        article_links.append({
                                            'title': title.strip(),
                                            'url': url.strip(),
                                            'source': GUARDIAN_HOMEPAGE
                                        })
                            
                            if article_links:
                                rss_success = True
                                total_links_found = len(article_links)
                                print(f"  ✓ 从RSS提取了 {len(article_links)} 个链接")
                                break
                        except Exception as e:
                            print(f"    ⚠️  RSS解析失败: {str(e)[:50]}")
                            continue
            except requests.exceptions.RequestException as e:
                print(f"    ⚠️  RSS请求失败: {str(e)[:50]}")
                continue
            except Exception as e:
                print(f"    ⚠️  其他错误: {str(e)[:50]}")
                continue
            
            # 如果RSS成功，跳过首页访问
            if not rss_success:
                # 方法2: 尝试访问首页
                print(f"  🔄 RSS方法失败，尝试访问首页...")
                response = session.get(GUARDIAN_HOMEPAGE, timeout=15, allow_redirects=True)
            
            # 检查状态码
            if response.status_code == 403:
                print(f"  ⚠️  收到403错误，尝试其他方法...")
                # 尝试访问分类页面
                news_sections = [
                    'https://guardian.ng/news/',
                    'https://guardian.ng/politics/',
                    'https://guardian.ng/business/',
                ]
                
                for section_url in news_sections:
                    try:
                        print(f"  🔄 尝试访问分类页面: {section_url}")
                        section_response = session.get(section_url, timeout=10)
                        print(f"    状态码: {section_response.status_code}")
                        if section_response.status_code == 200:
                            soup = BeautifulSoup(section_response.content, 'html.parser')
                            section_links = extract_guardian_article_links(section_url, soup)
                            if section_links:
                                article_links.extend(section_links)
                                print(f"  ✓ 从 {section_url} 提取了 {len(section_links)} 个链接")
                                if len(article_links) >= 20:
                                    break
                    except Exception as e:
                        continue
            else:
                response.raise_for_status()
                
                # 检查是否被Cloudflare拦截
                if 'Just a moment' in response.text or 'challenge-platform' in response.text or 'cf-browser-verification' in response.text:
                    print(f"  ⚠️  检测到Cloudflare保护")
                    # 如果首页被拦截，article_links应该已经在上面从分类页面获取了
                else:
                    # 正常解析HTML
                    soup = BeautifulSoup(response.content, 'html.parser')
                    homepage_links = extract_guardian_article_links(GUARDIAN_HOMEPAGE, soup)
                    if homepage_links:
                        article_links.extend(homepage_links)
                        print(f"  ✓ 从首页提取了 {len(homepage_links)} 个链接")
        
        # 去重
        if article_links:
            seen_urls = set()
            unique_links = []
            for link in article_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            article_links = unique_links
            total_links_found = len(article_links)
            print(f"  ✓ 去重后共 {total_links_found} 个新闻链接")
        
        if not article_links:
            print(f"  ❌ 所有方法都失败，无法获取文章链接")
            print(f"  💡 建议：")
            print(f"     1. 检查网络连接和防火墙设置")
            print(f"     2. 使用Selenium等工具处理JavaScript（需要安装selenium）")
            print(f"     3. 使用代理服务")
            print(f"     4. 手动访问guardian.ng获取文章链接")
            return []
        
        # 提取文章内容
        if not article_links:
            print(f"  ⚠️  未找到任何新闻链接")
            return []
        
        for i, link_info in enumerate(article_links, 1):
            article_url = link_info['url']
            homepage_title = link_info['title']
            
            print(f"  [{i}/{len(article_links)}] 提取: {homepage_title[:50]}...")
            
            try:
                # 使用 newsplease 提取文章内容（动态生成请求头）
                current_request_args = {'headers': get_headers()}
                article = NewsPlease.from_url(article_url, request_args=current_request_args)
                
                if article and article.title:
                    article_data = serialize_article(article)
                    
                    if article_data:
                        article_data['homepage_title'] = homepage_title
                        article_data['homepage_source'] = GUARDIAN_HOMEPAGE
                        article_data['extracted_at'] = datetime.now().isoformat()
                    
                    all_articles.append(article_data)
                    total_articles_extracted += 1
                    print(f"    ✓ 成功提取")
                else:
                    print(f"    ✗ 无法提取内容")
                
                time.sleep(1)  # 延迟避免请求过快
                
            except Exception as e:
                print(f"    ✗ 提取失败: {str(e)[:50]}")
                continue
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 网络请求失败: {str(e)}")
        return []
    except Exception as e:
        print(f"  ✗ 处理失败: {str(e)}")
        return []
    
    print(f"\n" + "=" * 60)
    print(f"Guardian.ng 抓取完成！")
    print(f"  找到链接: {total_links_found} 个")
    print(f"  成功提取: {total_articles_extracted} 篇文章")
    print("=" * 60)
    
    return all_articles

def main():
    """主函数"""
    articles = crawl_guardian()
    
    if articles:
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f'guardian_news_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Guardian.ng文章数据已保存到 {output_file}")
        print(f"   共 {len(articles)} 篇文章")
    else:
        print(f"\n⚠️  未抓取到任何文章")

if __name__ == '__main__':
    main()
