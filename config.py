"""
AI API 配置文件
支持多种AI API：Gemini、OpenAI、Claude等
"""

import os
from typing import Dict, Optional, Any

class AIConfig:
    """AI API配置类"""
    
    # 可用的AI提供商
    PROVIDERS = {
        'gemini': 'Google Gemini',
        'openai': 'OpenAI GPT',
        'claude': 'Anthropic Claude',
        'ollama': 'Ollama (本地)',
        'tongyi': '阿里云通义千问',
        'deepseek': 'DeepSeek',
        'hunyuan': '腾讯混元',
        'zhipu': '智谱AI (GLM)',
    }
    
    def __init__(self):
        """初始化配置"""
        # 默认提供商（可以通过环境变量或配置文件修改）
        self.default_provider = os.getenv('AI_PROVIDER', 'gemini').lower()
        
        # 各API的配置
        self.configs = {
            'gemini': {
                'enabled': True,
                'api_key': os.getenv('GEMINI_API_KEY', ''),
                'models': [
                    'gemini-3-flash-preview'
                ],
                'default_model': 'gemini-1.5-pro',
                'temperature': 0.7,
                'max_tokens': 8192,
            },
            'openai': {
                'enabled': True,
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'models': [
                    'gpt-4-turbo-preview',
                    'gpt-4',
                    'gpt-3.5-turbo',
                ],
                'default_model': 'gpt-4-turbo-preview',
                'temperature': 0.7,
                'max_tokens': 4096,
            },
            'claude': {
                'enabled': True,
                'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
                'models': [
                    'claude-3-opus-20240229',
                    'claude-3-sonnet-20240229',
                    'claude-3-haiku-20240307',
                ],
                'default_model': 'claude-3-sonnet-20240229',
                'temperature': 0.7,
                'max_tokens': 4096,
            },
            'ollama': {
                'enabled': True,
                'api_key': '',  # Ollama不需要API密钥
                'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                'models': [
                    'llama2',
                    'mistral',
                    'codellama',
                    'llama2:13b',
                ],
                'default_model': 'llama2',
                'temperature': 0.7,
                'max_tokens': 4096,
            },
            'tongyi': {
                'enabled': True,
                'api_key': os.getenv('DASHSCOPE_API_KEY', ''),
                'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'models': [
                    'qwen-plus',
                    'qwen-turbo',
                    'qwen-plus-longcontext',
                    'qwen-vl-max',
                    'qwen-vl-plus',
                ],
                'default_model': 'qwen-max',
                'temperature': 0.7,
                'max_tokens': 2000,
            },
            'deepseek': {
                'enabled': True,
                'api_key': os.getenv('DEEPSEEK_API_KEY', 'sk-a1a2cdcabeb045478b1c1b2d4bf8530e'),
                'base_url': 'https://api.deepseek.com',  # 也可以使用 'https://api.deepseek.com/v1'
                'models': [
                    'deepseek-chat',
                    'deepseek-reasoner',
                ],
                'default_model': 'deepseek-chat',
                'temperature': 0.7,
                'max_tokens': 4096,
            },
            'hunyuan': {
                'enabled': True,
                'api_key': os.getenv('TENCENT_SECRET_ID', ''),
                'secret_key': os.getenv('TENCENT_SECRET_KEY', ''),
                'base_url': 'https://hunyuan.tencentcloudapi.com',
                'region': os.getenv('TENCENT_REGION', 'ap-beijing'),
                'models': [
                    'hunyuan-lite',
                    'hunyuan-standard',
                    'hunyuan-pro',
                ],
                'default_model': 'hunyuan-lite',
                'temperature': 0.7,
                'max_tokens': 4096,
            },
            'zhipu': {
                'enabled': True,
                'api_key': os.getenv('ZHIPU_API_KEY', ''),
                'models': [
                    'glm-4.7',
                    'glm-4',
                    'glm-4-flash',
                    'glm-3-turbo',
                ],
                'default_model': 'glm-4.7',
                'temperature': 1.0,
                'max_tokens': 65536,
                'thinking_enabled': False,  # 是否启用深度思考模式
            },
        }
    
    def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """获取指定提供商的配置"""
        provider = (provider or self.default_provider).lower()
        
        if provider not in self.configs:
            raise ValueError(f"不支持的AI提供商: {provider}. 可用选项: {list(self.PROVIDERS.keys())}")
        
        config = self.configs[provider].copy()
        config['provider'] = provider
        config['provider_name'] = self.PROVIDERS.get(provider, provider)
        
        return config
    
    def is_provider_available(self, provider: Optional[str] = None) -> bool:
        """检查提供商是否可用（有API密钥等）"""
        provider = (provider or self.default_provider).lower()
        config = self.get_provider_config(provider)
        
        # Ollama不需要API密钥
        if provider == 'ollama':
            return config['enabled']
        
        # 腾讯混元需要secret_id和secret_key
        if provider == 'hunyuan':
            return config['enabled'] and bool(config.get('api_key')) and bool(config.get('secret_key'))
        
        # 其他提供商需要API密钥
        return config['enabled'] and bool(config.get('api_key'))
    
    def get_available_providers(self) -> list:
        """获取所有可用的提供商列表"""
        available = []
        for provider in self.PROVIDERS.keys():
            if self.is_provider_available(provider):
                available.append(provider)
        return available
    
    def set_default_provider(self, provider: str):
        """设置默认提供商"""
        if provider.lower() not in self.PROVIDERS:
            raise ValueError(f"不支持的AI提供商: {provider}")
        self.default_provider = provider.lower()
    
    def update_config(self, provider: str, **kwargs):
        """更新指定提供商的配置"""
        provider = provider.lower()
        if provider not in self.configs:
            raise ValueError(f"不支持的AI提供商: {provider}")
        
        self.configs[provider].update(kwargs)
    
    def print_status(self):
        """打印所有提供商的配置状态"""
        print("=" * 60)
        print("AI API 配置状态")
        print("=" * 60)
        print(f"默认提供商: {self.default_provider} ({self.PROVIDERS.get(self.default_provider, '未知')})\n")
        
        for provider, name in self.PROVIDERS.items():
            config = self.get_provider_config(provider)
            status = "✓ 可用" if self.is_provider_available(provider) else "✗ 不可用"
            if provider == 'ollama':
                api_key_status = "不需要"
            elif provider == 'hunyuan':
                api_key_status = "已设置" if (config.get('api_key') and config.get('secret_key')) else "未设置"
            else:
                api_key_status = "已设置" if config.get('api_key') else "未设置"
            
            print(f"{name} ({provider}):")
            print(f"  状态: {status}")
            print(f"  API密钥: {api_key_status}")
            print(f"  默认模型: {config.get('default_model', 'N/A')}")
            print(f"  可用模型: {', '.join(config.get('models', []))}")
            print()


# 全局配置实例
config = AIConfig()

# 便捷函数
def get_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """获取配置（便捷函数）"""
    return config.get_provider_config(provider)

def is_available(provider: Optional[str] = None) -> bool:
    """检查是否可用（便捷函数）"""
    return config.is_provider_available(provider)

def set_provider(provider: str):
    """设置提供商（便捷函数）"""
    config.set_default_provider(provider)
