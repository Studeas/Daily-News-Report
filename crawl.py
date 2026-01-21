from newsplease import NewsPlease
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import time
import os
from zoneinfo import ZoneInfo

LIMIT_NUM = 25

# List of news platform homepages
homepage_urls = [
    'https://punchng.com/',
    'https://dailypost.ng/',
    'https://dailytrust.com/',
    'https://thesun.ng/',
    'https://www.premiumtimesng.com/',
    # 'https://guardian.ng/'
]

# Set request headers to simulate browser access and avoid 403 errors
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

request_args = {'headers': headers}

# Nigeria timezone (Africa/Lagos, UTC+1)
NIGERIA_TZ = ZoneInfo('Africa/Lagos')

def convert_to_nigeria_time(dt_str_or_dt):
    """
    Convert a datetime string or datetime object to Nigeria time (Africa/Lagos).
    If input is a string, parse it and convert to Nigeria timezone.
    If input is a datetime, convert it to Nigeria timezone.
    Returns ISO format string in Nigeria timezone.
    """
    if dt_str_or_dt is None:
        return None
    
    try:
        dt = None
        
        # If it's already a datetime object
        if isinstance(dt_str_or_dt, datetime):
            dt = dt_str_or_dt
        else:
            # If it's a string, parse it
            dt_str = str(dt_str_or_dt).strip()
            # Clean up the string (handle 'Z' suffix)
            dt_str_clean = dt_str.replace('Z', '+00:00')
            
            # Parse the datetime
            try:
                dt = datetime.fromisoformat(dt_str_clean)
            except ValueError:
                # Try parsing without timezone info
                dt = datetime.fromisoformat(dt_str)
        
        # If datetime is naive (no timezone), we need to determine its timezone
        if dt.tzinfo is None:
            # For date_download, it's likely in local timezone
            # Get the current local timezone
            try:
                # Try to get local timezone from system
                local_tz = datetime.now().astimezone().tzinfo
                if local_tz:
                    dt = dt.replace(tzinfo=local_tz)
                else:
                    # Fallback to UTC if can't determine
                    dt = dt.replace(tzinfo=ZoneInfo('UTC'))
            except Exception:
                # Fallback to UTC
                dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # Convert to Nigeria time
        dt_nigeria = dt.astimezone(NIGERIA_TZ)
        return dt_nigeria.isoformat()
        
    except Exception as e:
        # If conversion fails, return original value
        print(f"    ⚠ 时区转换失败: {str(e)[:50]}")
        return dt_str_or_dt if isinstance(dt_str_or_dt, str) else str(dt_str_or_dt)

def extract_article_links(homepage_url, soup):
    """
    Extract news article links and titles from homepage HTML
    This method needs to be adjusted based on each website's specific HTML structure
    """
    article_links = []
    base_domain = urlparse(homepage_url).netloc
    
    # Common news link selectors (needs adjustment based on actual website)
    # Try multiple possible selectors
    selectors = [
        'article a',           # Links within article tags
        '.post a',             # Links within post class
        '.article a',          # Links within article class
        'h2 a', 'h3 a',        # Links within headings
        '.entry-title a',      # Links within title class
        '.news-item a',        # Links within news item class
        'a[href*="/article/"]',  # Links containing /article/
        'a[href*="/news/"]',      # Links containing /news/
        'a[href*="/story/"]',     # Links containing /story/
    ]
    
    found_links = set()  # For deduplication
    
    for selector in selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            # Convert to absolute URL
            full_url = urljoin(homepage_url, href)
            parsed = urlparse(full_url)
            
            # Filter conditions: only keep same-domain links, exclude homepage, category pages, etc.
            if (parsed.netloc == base_domain and 
                full_url not in found_links and
                full_url != homepage_url and
                not any(x in full_url.lower() for x in ['/category/', '/tag/', '/author/', '/page/', '/archive/'])):
                
                title = link.get_text(strip=True)
                if title and len(title) > 10:  # Filter by title length
                    found_links.add(full_url)
                    article_links.append({
                        'title': title,
                        'url': full_url,
                        'source': homepage_url
                    })
    
    # If the above selectors didn't find anything, try a more generic method
    if not article_links:
        # Find all links and filter out those that might be articles
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            full_url = urljoin(homepage_url, href)
            parsed = urlparse(full_url)
            
            if (parsed.netloc == base_domain and 
                full_url not in found_links and
                full_url != homepage_url and
                len(full_url) > len(homepage_url) + 10 and  # Filter by URL length
                not any(x in full_url.lower() for x in ['/category/', '/tag/', '/author/', '/page/', '/archive/', '#'])):
                
                title = link.get_text(strip=True)
                if title and len(title) > 10:
                    found_links.add(full_url)
                    article_links.append({
                        'title': title,
                        'url': full_url,
                        'source': homepage_url
                    })
    
    # Deduplicate and limit quantity
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
    """Convert article object or dict to serializable dictionary"""
    if article is None:
        return None
    
    # If already a dict, use directly
    if isinstance(article, dict):
        data = article
    # If an object, convert to dict
    elif hasattr(article, '__dict__'):
        data = article.__dict__
    else:
        # Other types, return directly
        return article
    
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            # Convert datetime to string
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = serialize_article(value)
        elif hasattr(value, '__dict__'):
            # Recursively process nested objects
            result[key] = serialize_article(value)
        elif isinstance(value, (list, tuple)):
            # Process lists and tuples
            result[key] = [serialize_article(item) for item in value]
        else:
            # Other types, assign directly
            result[key] = value
    return result

# Main program
print("=" * 60)
print("开始抓取新闻...")
print("=" * 60)

all_articles = []
total_links_found = 0
total_articles_extracted = 0

# Step 1: Extract news links from each homepage
for homepage_url in homepage_urls:
    print(f"\n📰 处理首页: {homepage_url}")
    try:
        # Get homepage HTML
        response = requests.get(homepage_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract news links
        article_links = extract_article_links(homepage_url, soup)
        total_links_found += len(article_links)
        
        print(f"  ✓ 找到 {len(article_links)} 个新闻链接")
        
        # Step 2: Extract article content for each link
        for i, link_info in enumerate(article_links, 1):
            article_url = link_info['url']
            homepage_title = link_info['title']
            
            print(f"  [{i}/{len(article_links)}] 提取: {homepage_title[:50]}...")
            
            try:
                # Use newsplease to extract article content
                article = NewsPlease.from_url(article_url, request_args=request_args)
                
                if article and article.title:
                    # Serialize article data
                    article_data = serialize_article(article)
                    
                    # Add homepage information
                    if article_data:
                        article_data['homepage_title'] = homepage_title
                        article_data['homepage_source'] = homepage_url
                        # Convert extracted_at to Nigeria time
                        article_data['extracted_at'] = convert_to_nigeria_time(datetime.now())
                    
                    # Convert date_download to Nigeria timezone for consistency
                    if article_data and 'date_download' in article_data:
                        article_data['date_download'] = convert_to_nigeria_time(article_data['date_download'])
                    
                    # Convert date_publish to Nigeria timezone (assuming it's already in Nigeria time, but ensure consistency)
                    if article_data and 'date_publish' in article_data and article_data['date_publish']:
                        article_data['date_publish'] = convert_to_nigeria_time(article_data['date_publish'])
                    
                    # Time filter: skip articles published more than 48 hours before download
                    if article_data and 'date_publish' in article_data and 'date_download' in article_data:
                        try:
                            date_publish_str = article_data.get('date_publish')
                            date_download_str = article_data.get('date_download')
                            
                            # Only filter if both dates are available and not None
                            if date_publish_str and date_download_str:
                                # Parse datetime strings (both should now be in Nigeria timezone)
                                date_publish_str_clean = str(date_publish_str).replace('Z', '+00:00')
                                date_download_str_clean = str(date_download_str).replace('Z', '+00:00')
                                
                                date_publish = datetime.fromisoformat(date_publish_str_clean)
                                date_download = datetime.fromisoformat(date_download_str_clean)
                                
                                # Ensure both are timezone-aware (should be after conversion)
                                if date_publish.tzinfo is None:
                                    date_publish = date_publish.replace(tzinfo=NIGERIA_TZ)
                                if date_download.tzinfo is None:
                                    date_download = date_download.replace(tzinfo=NIGERIA_TZ)
                                
                                # Calculate time difference
                                time_diff = date_download - date_publish
                                
                                # Skip if published more than 48 hours before download
                                if time_diff > timedelta(hours=48):
                                    print(f"    ⏭ 跳过（发布时间早于下载时间超过48小时: {time_diff.days}天{time_diff.seconds//3600}小时）")
                                    continue
                        except (ValueError, TypeError, AttributeError) as e:
                            # If date parsing fails, continue with the article
                            print(f"    ⚠ 时间解析失败，继续处理: {str(e)[:30]}")
                    
                    all_articles.append(article_data)
                    total_articles_extracted += 1
                    print(f"    ✓ 成功提取")
                else:
                    print(f"    ✗ 无法提取内容")
                
                # Add delay to avoid requests being too fast
                time.sleep(1)
                
            except Exception as e:
                print(f"    ✗ 提取失败: {str(e)[:50]}")
                continue
        
    except Exception as e:
        print(f"  ✗ 处理首页失败: {str(e)}")
        continue

# Step 3: Save to JSON file
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
