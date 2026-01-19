# 新闻抓取与AI分析系统

自动抓取新闻文章，使用AI进行过滤、分类、翻译和摘要生成。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置AI API

设置环境变量（选择一个AI提供商）：

```bash
# 智谱AI（推荐）
export ZHIPU_API_KEY='your-api-key'
export AI_PROVIDER='zhipu'

# 或使用其他提供商
export GEMINI_API_KEY='your-api-key'      # Google Gemini
export DASHSCOPE_API_KEY='your-api-key'  # 阿里云通义千问
export DEEPSEEK_API_KEY='your-api-key'   # DeepSeek
```

### 运行

```bash
python run.py
```

自动完成新闻抓取、AI处理和报告生成。

## 输出文件

- **数据文件**: `data/news_YYYY-MM-DD.json` - 原始抓取的新闻
- **报告文件**: `report/YYYYMMDD/report.json` 和 `report.html` - AI处理后的报告
- **日志文件**: `log/run_YYYYMMDD_HHMMSS.log` - 执行日志

## 支持的AI提供商

- 智谱AI (ZhipuAI)
- Google Gemini
- 阿里云通义千问
- DeepSeek
- 腾讯混元
- OpenAI GPT
- Anthropic Claude

详细配置见 `config.py` 和 `CONFIG_USAGE.md`。

## 自动化部署

支持 GitHub Actions 自动执行，每天定时抓取并发送邮件报告。

配置步骤：
1. 在 GitHub 仓库设置 Secrets（API密钥、邮件配置等）
2. 工作流文件：`.github/workflows/daily-news.yml`
3. 默认执行时间：UTC 12:00

## 主要功能

- 自动抓取多个新闻平台
- AI智能过滤（排除娱乐、体育等非严肃新闻）
- 自动分类（疾病与灾害、安全形势、涉我舆情等）
- 中英文翻译
- 关键信息提取
- 断点续传（支持中断后继续处理）
- 邮件自动通知

## 自定义配置

- **修改新闻源**: 编辑 `crawl.py` 中的 `homepage_urls`
- **调整AI提示词**: 编辑 `prompt_template.txt`
- **切换AI提供商**: 设置 `AI_PROVIDER` 环境变量
