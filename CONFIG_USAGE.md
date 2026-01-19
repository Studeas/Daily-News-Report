# AI API 配置使用指南

## 快速开始

### 1. 设置环境变量

选择你想使用的AI提供商，设置对应的API密钥：

```bash
# Google Gemini (推荐)
export GEMINI_API_KEY='your-gemini-api-key'
export AI_PROVIDER='gemini'

# OpenAI GPT
export OPENAI_API_KEY='your-openai-api-key'
export AI_PROVIDER='openai'

# Anthropic Claude
export ANTHROPIC_API_KEY='your-anthropic-api-key'
export AI_PROVIDER='claude'

# 阿里云通义千问 🇨🇳
export DASHSCOPE_API_KEY='sk-4be054a836d4434faa959aa32aef882a'
export AI_PROVIDER='tongyi'

# DeepSeek 🇨🇳
export DEEPSEEK_API_KEY='your-deepseek-api-key'
export AI_PROVIDER='deepseek'

# 腾讯混元 🇨🇳
export TENCENT_SECRET_ID='your-secret-id'
export TENCENT_SECRET_KEY='your-secret-key'
export TENCENT_REGION='ap-beijing'
export AI_PROVIDER='hunyuan'

# 智谱AI 🇨🇳
export ZHIPU_API_KEY='7820eca7bc284516865f2eba4c5c0aeb.F58w18MC91xKoWsg'
export AI_PROVIDER='zhipu'

# Ollama (本地)
export OLLAMA_BASE_URL='http://localhost:11434'
export AI_PROVIDER='ollama'
```

### 2. 运行脚本

```bash
python process_with_ai.py
```

脚本会自动：
- 检测可用的AI提供商
- 使用配置的提供商（或自动选择第一个可用的）
- 显示配置状态

## 支持的AI提供商

### 国际AI提供商

#### 1. Google Gemini (推荐)
- **优势**: 免费额度高，性能好，支持长文本
- **模型**: gemini-1.5-pro, gemini-1.5-flash
- **设置**: `export GEMINI_API_KEY='your-key'`

#### 2. OpenAI GPT
- **优势**: 质量高，稳定
- **模型**: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
- **设置**: `export OPENAI_API_KEY='your-key'`

#### 3. Anthropic Claude
- **优势**: 安全性好，长文本处理能力强
- **模型**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **设置**: `export ANTHROPIC_API_KEY='your-key'`

#### 4. Ollama (本地)
- **优势**: 完全免费，本地运行，隐私保护
- **模型**: llama2, mistral, codellama
- **设置**: 需要先安装并运行 Ollama
- **安装**: https://ollama.ai

### 中国AI提供商

#### 5. 阿里云通义千问 (Tongyi/Qwen) 🇨🇳
- **优势**: 中文理解能力强，价格相对较低，支持多模态
- **模型**: qwen-max, qwen-plus, qwen-turbo, qwen-vl-max
- **设置**: 
  ```bash
  export DASHSCOPE_API_KEY='your-key'
  export AI_PROVIDER='tongyi'
  ```
- **获取API密钥**: 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
- **注意**: 使用OpenAI兼容接口，需要安装 `openai` 包

#### 6. DeepSeek 🇨🇳
- **优势**: 性价比高，支持推理模式，OpenAI兼容接口
- **模型**: deepseek-chat (对话), deepseek-reasoner (推理)
- **设置**: 
  ```bash
  export DEEPSEEK_API_KEY='your-key'
  export AI_PROVIDER='deepseek'
  ```
- **获取API密钥**: 访问 [DeepSeek API](https://platform.deepseek.com/)
- **注意**: 使用OpenAI兼容接口，需要安装 `openai` 包

#### 7. 腾讯混元 (Hunyuan) 🇨🇳
- **优势**: 腾讯官方AI，中文优化，企业级稳定性
- **模型**: hunyuan-lite, hunyuan-standard, hunyuan-pro
- **设置**: 
  ```bash
  export TENCENT_SECRET_ID='your-secret-id'
  export TENCENT_SECRET_KEY='your-secret-key'
  export TENCENT_REGION='ap-beijing'  # 可选，默认北京
  export AI_PROVIDER='hunyuan'
  ```
- **获取密钥**: 访问 [腾讯云控制台](https://console.cloud.tencent.com/)
- **注意**: 需要安装 `tencentcloud-sdk-python` 包
- **说明**: Hunyuan-MT-7B 是开源的翻译模型，主要用于多语言翻译任务。如需使用，可能需要本地部署或通过第三方服务。

#### 8. 智谱AI (ZhipuAI/GLM) 🇨🇳
- **优势**: 支持深度思考模式，长文本处理能力强（最大65536 tokens），中文优化
- **模型**: glm-4.7, glm-4, glm-4-flash, glm-3-turbo
- **设置**: 
  ```bash
  export ZHIPU_API_KEY='your-api-key'
  export AI_PROVIDER='zhipu'
  ```
- **获取API密钥**: 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
- **注意**: 需要安装 `zai` 包
- **特色功能**: 支持深度思考模式（thinking mode），适合复杂推理任务

## 自定义配置

### 修改默认提供商

在 `config.py` 中修改：

```python
self.default_provider = 'openai'  # 改为你想要的提供商
```

或使用环境变量：

```bash
export AI_PROVIDER='openai'
```

### 修改模型

在 `config.py` 中修改对应提供商的 `default_model`：

```python
'openai': {
    'default_model': 'gpt-4',  # 改为你想要的模型
    ...
}
```

### 修改参数

可以调整 temperature、max_tokens 等参数：

```python
config.update_config('gemini', temperature=0.5, max_tokens=4096)
```

## 查看配置状态

运行脚本时会自动显示所有提供商的配置状态，或手动查看：

```python
from config import config
config.print_status()
```

## 切换提供商

### 方法1: 环境变量（推荐）

```bash
export AI_PROVIDER='openai'
python process_with_ai.py
```

### 方法2: 代码中修改

在 `process_with_ai.py` 中：

```python
AI_PROVIDER = 'openai'  # 改为你想要的提供商
```

### 方法3: 运行时指定

修改代码支持命令行参数（可以添加）：

```python
import sys
if len(sys.argv) > 1:
    AI_PROVIDER = sys.argv[1].lower()
```

## 故障排除

### 1. 所有提供商都不可用

检查：
- API密钥是否正确设置
- 网络连接是否正常
- 是否安装了对应的Python包

### 2. 特定提供商失败

- **Gemini**: 检查API密钥，确认模型名称正确
- **OpenAI**: 检查账户余额，确认API密钥有效
- **Claude**: 检查API密钥，确认模型名称正确
- **通义千问**: 检查DASHSCOPE_API_KEY，确认在阿里云百炼平台已开通服务
- **DeepSeek**: 检查API密钥，确认账户有余额
- **腾讯混元**: 检查SECRET_ID和SECRET_KEY，确认在腾讯云已开通混元服务
- **Ollama**: 确认Ollama服务正在运行

### 3. 安全过滤器阻止

某些内容（如暴力、敏感话题）可能被安全过滤器阻止，这是正常的安全机制。

## 性能对比

| 提供商 | 速度 | 质量 | 成本 | 中文能力 | 推荐场景 |
|--------|------|------|------|----------|----------|
| Gemini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 免费额度高 | ⭐⭐⭐ | 日常使用 |
| GPT-4 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 较高 | ⭐⭐⭐⭐ | 高质量需求 |
| Claude | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中等 | ⭐⭐⭐ | 长文本处理 |
| 通义千问 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 较低 | ⭐⭐⭐⭐⭐ | 中文内容处理 |
| DeepSeek | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐⭐ | 性价比首选 |
| 腾讯混元 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中等 | ⭐⭐⭐⭐⭐ | 企业级应用 |
| 智谱AI | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中等 | ⭐⭐⭐⭐⭐ | 深度思考/长文本 |
| Ollama | ⭐⭐ | ⭐⭐⭐ | 免费 | ⭐⭐⭐ | 本地/隐私需求 |

## 示例

### 使用Gemini
```bash
export GEMINI_API_KEY='your-key'
export AI_PROVIDER='gemini'
python process_with_ai.py
```

### 使用OpenAI
```bash
export OPENAI_API_KEY='your-key'
export AI_PROVIDER='openai'
python process_with_ai.py
```

### 使用Claude
```bash
export ANTHROPIC_API_KEY='your-key'
export AI_PROVIDER='claude'
python process_with_ai.py
```

### 使用通义千问 🇨🇳
```bash
export DASHSCOPE_API_KEY='your-key'
export AI_PROVIDER='tongyi'
python process_with_ai.py
```

### 使用DeepSeek 🇨🇳
```bash
export DEEPSEEK_API_KEY='your-key'
export AI_PROVIDER='deepseek'
python process_with_ai.py
```

### 使用腾讯混元 🇨🇳
```bash
export TENCENT_SECRET_ID='your-secret-id'
export TENCENT_SECRET_KEY='your-secret-key'
export TENCENT_REGION='ap-beijing'
export AI_PROVIDER='hunyuan'
python process_with_ai.py
```

### 使用智谱AI 🇨🇳
```bash
export ZHIPU_API_KEY='your-api-key'
export AI_PROVIDER='zhipu'
python process_with_ai.py
```

### 使用Ollama（本地）
```bash
# 先启动Ollama服务
ollama serve

# 在另一个终端
export AI_PROVIDER='ollama'
python process_with_ai.py
```
