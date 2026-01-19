# 尼日利亚新闻抓取与AI处理系统

## 功能说明

本系统包含两个主要脚本：

1. **crawl.py** - 新闻抓取脚本
   - 从5个尼日利亚新闻平台首页提取新闻链接
   - 抓取每篇文章的完整内容
   - 保存为 `articles.json`

2. **process_with_ai.py** - AI处理与报告生成脚本
   - 使用Google Gemini API对文章进行过滤和翻译
   - 生成结构化报告（JSON + Markdown格式）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

### 1. 获取Google Gemini API密钥

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建API密钥
3. 设置环境变量：

```bash
export GEMINI_API_KEY='your-api-key-here'
```

或者在脚本中直接设置（不推荐，安全性较低）

## 使用方法

### 第一步：抓取新闻

```bash
python crawl.py
```

这将：
- 访问5个新闻平台首页
- 提取新闻链接
- 抓取文章内容
- 保存到 `articles.json`

### 第二步：AI处理与生成报告

```bash
python process_with_ai.py
```

这将：
- 读取 `articles.json`
- 使用Gemini API进行：
  - 文章质量过滤
  - 分类
  - 关键信息提取
  - 中英文翻译
- 生成两个报告文件：
  - `news_report.json` - 结构化JSON数据
  - `news_report.md` - 可读的Markdown报告

## 输出文件说明

### articles.json
原始抓取的新闻数据，包含：
- 标题、正文、作者、发布日期
- 来源信息、URL等

### news_report.json
AI处理后的结构化数据，包含：
- 原文数据（original）
- AI处理结果（processed）：
  - 中文翻译
  - 分类
  - 关键要点
  - 摘要
- 元数据（metadata）

### news_report.md
可读的Markdown格式报告，包含：
- 数据摘要统计
- 分类统计
- 来源统计
- 每篇文章的详细内容（中英文对照）

## 注意事项

1. **API限流**：Gemini API有请求频率限制，脚本已添加延迟处理
2. **费用**：使用Gemini API可能产生费用，请查看Google的定价
3. **网络**：需要稳定的网络连接访问新闻网站和API
4. **数据量**：如果文章数量很大，处理时间会较长

## 故障排除

### Gemini API未初始化
- 检查是否安装了 `google-generativeai`
- 检查是否设置了 `GEMINI_API_KEY` 环境变量
- 检查API密钥是否有效

### 文章提取失败
- 某些网站可能有反爬虫机制
- 检查网络连接
- 可能需要调整 `crawl.py` 中的选择器

### 翻译质量不佳
- 可以调整 `process_with_ai.py` 中的提示词
- 尝试使用不同的Gemini模型（如 `gemini-pro-vision`）

## 自定义配置

### 修改新闻源
编辑 `crawl.py` 中的 `homepage_urls` 列表

### 调整AI处理逻辑
编辑 `process_with_ai.py` 中的 `process_article_with_ai()` 函数中的提示词

### 修改报告格式
编辑 `process_with_ai.py` 中的 `generate_markdown_report()` 函数
