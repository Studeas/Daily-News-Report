"""
AI API configuration file
Supports multiple AI APIs: Gemini, OpenAI, Claude, etc.
"""

import os
from typing import Dict, Optional, Any

class AIConfig:
    """AI API configuration class"""
    
    # Available AI providers
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
        """Initialize configuration"""
        # Default provider (can be modified via environment variable or config file)
        self.default_provider = os.getenv('AI_PROVIDER', 'gemini').lower()
        
        # Configuration for each API
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
                'api_key': '',  # Ollama doesn't require API key
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
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
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
                'thinking_enabled': False,  # Whether to enable deep thinking mode
            },
        }
    
    def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for specified provider"""
        provider = (provider or self.default_provider).lower()
        
        if provider not in self.configs:
            raise ValueError(f"不支持的AI提供商: {provider}. 可用选项: {list(self.PROVIDERS.keys())}")
        
        config = self.configs[provider].copy()
        config['provider'] = provider
        config['provider_name'] = self.PROVIDERS.get(provider, provider)
        
        return config
    
    def is_provider_available(self, provider: Optional[str] = None) -> bool:
        """Check if provider is available (has API key, etc.)"""
        provider = (provider or self.default_provider).lower()
        config = self.get_provider_config(provider)
        
        # Ollama doesn't require API key
        if provider == 'ollama':
            return config['enabled']
        
        # Tencent Hunyuan requires secret_id and secret_key
        if provider == 'hunyuan':
            return config['enabled'] and bool(config.get('api_key')) and bool(config.get('secret_key'))
        
        # Other providers require API key
        return config['enabled'] and bool(config.get('api_key'))
    
    def get_available_providers(self) -> list:
        """Get list of all available providers"""
        available = []
        for provider in self.PROVIDERS.keys():
            if self.is_provider_available(provider):
                available.append(provider)
        return available
    
    def set_default_provider(self, provider: str):
        """Set default provider"""
        if provider.lower() not in self.PROVIDERS:
            raise ValueError(f"不支持的AI提供商: {provider}")
        self.default_provider = provider.lower()
    
    def update_config(self, provider: str, **kwargs):
        """Update configuration for specified provider"""
        provider = provider.lower()
        if provider not in self.configs:
            raise ValueError(f"不支持的AI提供商: {provider}")
        
        self.configs[provider].update(kwargs)
    
    def print_status(self):
        """Print configuration status for all providers"""
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


# Global configuration instance
config = AIConfig()

# Convenience functions
def get_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """Get configuration (convenience function)"""
    return config.get_provider_config(provider)

def is_available(provider: Optional[str] = None) -> bool:
    """Check if available (convenience function)"""
    return config.is_provider_available(provider)

def set_provider(provider: str):
    """Set provider (convenience function)"""
    config.set_default_provider(provider)
