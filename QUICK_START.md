# 快速开始 - GitHub Actions 部署

## 🚀 5分钟快速部署

### 步骤 1: 创建 GitHub 仓库

```bash
# 在 GitHub 网页上创建新仓库，然后执行：
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/news_nigeria.git
git branch -M main
git push -u origin main
```

### 步骤 2: 配置 Secrets

在 GitHub 仓库 → Settings → Secrets and variables → Actions 中添加：

**必需配置**:
- `AI_PROVIDER`: `gemini`
- `GEMINI_API_KEY`: 你的 API 密钥
- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: `your-email@gmail.com`
- `SMTP_PASSWORD`: Gmail 应用专用密码
- `EMAIL_TO`: `recipient@example.com`

### 步骤 3: 测试

1. 在 GitHub 仓库页面点击 **Actions**
2. 选择 **Daily News Crawl and Process**
3. 点击 **Run workflow** → **Run workflow**

### 步骤 4: 等待执行完成

- 查看 Actions 页面了解执行进度
- 完成后检查邮箱

---

## 📧 Gmail 应用专用密码获取

1. 访问: https://myaccount.google.com/security
2. 开启"两步验证"
3. 创建"应用专用密码"
4. 选择"邮件"和"其他设备"
5. 复制16位密码作为 `SMTP_PASSWORD`

---

## ⏰ 修改执行时间

编辑 `.github/workflows/daily-news.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # UTC 02:00 = 北京时间 10:00
```

时区对照:
- 北京时间 08:00 → `0 0 * * *`
- 北京时间 10:00 → `0 2 * * *`
- 北京时间 14:00 → `0 6 * * *`

---

详细说明请查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
