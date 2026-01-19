# Git 推送指南 - 哪些文件需要推送？

## 📦 需要推送到 GitHub 的文件

以下文件**必须**推送到 GitHub，因为 GitHub Actions 需要它们：

### ✅ 核心代码文件
- `crawl.py` - 爬虫脚本
- `crawl_guardian.py` - Guardian 专用爬虫
- `process_with_ai.py` - AI 处理脚本
- `run.py` - 主工作流脚本
- `send_email.py` - 邮件发送脚本
- `ai_client.py` - AI 客户端
- `config.py` - 配置文件
- `prompt_template.txt` - AI 提示词模板

### ✅ 配置文件
- `requirements.txt` - Python 依赖
- `.github/workflows/daily-news.yml` - GitHub Actions 工作流
- `.gitignore` - Git 忽略规则
- `README.md` - 项目说明
- `DEPLOYMENT_GUIDE.md` - 部署指南
- `QUICK_START.md` - 快速开始
- `CONFIG_USAGE.md` - 配置使用说明

### ✅ 目录结构（空目录占位文件）
- `data/.gitkeep` - 保持 data 目录存在
- `log/.gitkeep` - 保持 log 目录存在

---

## ❌ 不需要推送到 GitHub 的文件

以下文件**不应该**推送到 GitHub（已在 `.gitignore` 中配置）：

### 🚫 数据文件
- `data/*.json` - 爬取的文章数据（文件很大，且会每天更新）
- `data/news_*.json` - 所有新闻数据文件

### 🚫 日志文件
- `log/*.log` - 所有日志文件
- `log/run_*.log` - 运行日志

### 🚫 报告文件（可选）
- `report/` - 报告文件夹（可选，因为 GitHub Actions 会生成新的）
  - 如果你想保留历史报告，可以推送
  - 如果不想，可以在 `.gitignore` 中添加 `report/`

### 🚫 临时文件
- `__pycache__/` - Python 缓存
- `*.pyc` - 编译的 Python 文件
- `.env` - 环境变量文件（包含敏感信息）

---

## 🔍 检查当前状态

执行以下命令查看哪些文件会被推送：

```bash
# 查看 Git 状态
git status

# 查看哪些文件会被提交（排除 .gitignore 中的文件）
git status --short

# 查看 .gitignore 是否生效
git check-ignore -v data/*.json log/*.log
```

---

## 📝 推送步骤

### 1. 检查要推送的文件

```bash
# 查看将要提交的文件
git add -n .  # 预览模式，不会真正添加

# 或者
git status
```

### 2. 添加文件

```bash
# 添加所有应该推送的文件（.gitignore 会自动排除不需要的文件）
git add .

# 或者手动添加特定文件
git add *.py
git add *.txt
git add *.md
git add .github/
git add .gitignore
```

### 3. 提交

```bash
git commit -m "Add GitHub Actions workflow and email support"
```

### 4. 推送到 GitHub

```bash
git push origin main
```

---

## ⚠️ 重要提示

### 1. 数据文件不要推送
- `data/` 文件夹中的 JSON 文件可能很大（几 MB 到几十 MB）
- 这些文件会每天更新，推送会占用大量存储空间
- GitHub Actions 会在每次运行时生成新的数据文件

### 2. 日志文件不要推送
- `log/` 文件夹中的日志文件会不断增长
- 这些文件对代码运行不是必需的
- GitHub Actions 会生成自己的日志

### 3. 报告文件（可选）
- 如果你想在 GitHub 上保留历史报告，可以推送 `report/` 文件夹
- 如果不想，报告会作为 GitHub Actions 的 Artifacts 保存 30 天

### 4. 确保 .gitignore 正确

检查 `.gitignore` 文件是否包含：

```
data/*.json
!data/.gitkeep
log/*.log
!log/.gitkeep
```

---

## 🎯 推荐做法

### 方案 A：最小推送（推荐）
只推送代码和配置文件，不推送数据和日志：

```bash
# .gitignore 已经配置好了，直接执行：
git add .
git commit -m "Initial commit with GitHub Actions"
git push origin main
```

### 方案 B：包含报告
如果想在 GitHub 上查看历史报告：

```bash
# 修改 .gitignore，注释掉 report/ 的忽略规则
# 然后推送
git add .
git commit -m "Include reports"
git push origin main
```

---

## ✅ 验证推送结果

推送后，在 GitHub 网页上检查：

1. 进入仓库页面
2. 查看文件列表
3. 确认：
   - ✅ 有所有 `.py` 文件
   - ✅ 有 `.github/workflows/` 文件夹
   - ✅ 有 `requirements.txt`
   - ❌ **没有** `data/*.json` 文件
   - ❌ **没有** `log/*.log` 文件

---

## 📊 文件大小参考

- 代码文件：通常 < 1 MB
- 单个 JSON 数据文件：可能 1-50 MB
- 日志文件：可能 1-10 MB
- 报告文件：通常 < 5 MB

**结论**：只推送代码文件，总大小通常 < 5 MB，非常合理。
