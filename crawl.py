from newsplease import NewsPlease
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import os

LIMIT_NUM = 25

# List of news platform homepages
homepage_urls = [
    'https://punchng.com/',
    'https://dailypost.ng/',
    'https://dailytrust.com/',
    'https://thesun.ng/',
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
                        article_data['extracted_at'] = datetime.now().isoformat()
                    
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
