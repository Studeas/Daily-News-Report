"""
AI API client wrapper
Provides unified interface to call different AI APIs
"""

from typing import Dict, Optional, Any
import json
import re
from config import get_config, is_available

class AIClient:
    """Unified AI client interface"""
    
    def __init__(self, provider: Optional[str] = None):
        """Initialize AI client"""
        self.config = get_config(provider)
        self.provider = self.config['provider']
        self.model_name = self.config.get('default_model')
        
        # Initialize corresponding client
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize specific AI client"""
        if self.provider == 'gemini':
            return self._init_gemini()
        elif self.provider == 'openai':
            return self._init_openai()
        elif self.provider == 'claude':
            return self._init_claude()
        elif self.provider == 'ollama':
            return self._init_ollama()
        elif self.provider == 'tongyi':
            return self._init_tongyi()
        elif self.provider == 'deepseek':
            return self._init_deepseek()
        elif self.provider == 'hunyuan':
            return self._init_hunyuan()
        elif self.provider == 'zhipu':
            return self._init_zhipu()
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config['api_key'])
            
            # Try different models
            for model_name in self.config['models']:
                try:
                    model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                    print(f"✓ 使用 Gemini 模型: {model_name}")
                    return model
                except Exception as e:
                    continue
            
            raise Exception("无法找到可用的Gemini模型")
        except ImportError:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.config['api_key'])
            self.model_name = self.config.get('default_model', 'gpt-4-turbo-preview')
            print(f"✓ 使用 OpenAI 模型: {self.model_name}")
            return client
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    def _init_claude(self):
        """初始化Claude客户端"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.config['api_key'])
            self.model_name = self.config.get('default_model', 'claude-3-sonnet-20240229')
            print(f"✓ 使用 Claude 模型: {self.model_name}")
            return client
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")
    
    def _init_ollama(self):
        """初始化Ollama客户端"""
        try:
            import requests
            base_url = self.config.get('base_url', 'http://localhost:11434')
            self.model_name = self.config.get('default_model', 'llama2')
            print(f"✓ 使用 Ollama 模型: {self.model_name} (base_url: {base_url})")
            return {'base_url': base_url}
        except ImportError:
            raise ImportError("请安装 requests: pip install requests")
    
    def _init_tongyi(self):
        """Initialize Tongyi client (prefer DashScope SDK, fallback to OpenAI compatible interface)"""
        try:
            # Priority: try using DashScope SDK
            try:
                import dashscope
                dashscope.api_key = self.config['api_key']
                self.model_name = self.config.get('default_model', 'qwen-max')
                print(f"✓ 使用 通义千问 模型: {self.model_name} (DashScope SDK)")
                return {'type': 'dashscope', 'api_key': self.config['api_key']}
            except ImportError:
                # If DashScope SDK is not available, use OpenAI compatible interface
                import openai
                client = openai.OpenAI(
                    api_key=self.config['api_key'],
                    base_url=self.config.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
                )
                self.model_name = self.config.get('default_model', 'qwen-max')
                print(f"✓ 使用 通义千问 模型: {self.model_name} (OpenAI兼容接口)")
                return {'type': 'openai_compat', 'client': client}
        except ImportError:
            raise ImportError("请安装 dashscope 或 openai: pip install dashscope 或 pip install openai")
    
    def _init_deepseek(self):
        """Initialize DeepSeek client (using OpenAI compatible interface)"""
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.config['api_key'],
                base_url=self.config.get('base_url', 'https://api.deepseek.com')
            )
            self.model_name = self.config.get('default_model', 'deepseek-chat')
            print(f"✓ 使用 DeepSeek 模型: {self.model_name}")
            return client
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    def _init_hunyuan(self):
        """初始化腾讯混元客户端"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
            
            cred = credential.Credential(
                self.config['api_key'],
                self.config.get('secret_key', '')
            )
            
            httpProfile = HttpProfile()
            httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
            
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            clientProfile.language = "zh-CN"
            
            client = hunyuan_client.HunyuanClient(cred, self.config.get('region', 'ap-beijing'), clientProfile)
            self.model_name = self.config.get('default_model', 'hunyuan-lite')
            print(f"✓ 使用 腾讯混元 模型: {self.model_name}")
            return client
        except ImportError:
            raise ImportError("请安装 tencentcloud-sdk-python: pip install tencentcloud-sdk-python")
    
    def _init_zhipu(self):
        """初始化智谱AI客户端"""
        try:
            from zai import ZhipuAiClient
            client = ZhipuAiClient(api_key=self.config['api_key'])
            self.model_name = self.config.get('default_model', 'glm-4.7')
            print(f"✓ 使用 智谱AI 模型: {self.model_name}")
            return client
        except ImportError:
            raise ImportError("请安装 zai: pip install zai")
    
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content (unified interface)"""
        if self.provider == 'gemini':
            return self._generate_gemini(prompt, **kwargs)
        elif self.provider == 'openai':
            return self._generate_openai(prompt, **kwargs)
        elif self.provider == 'claude':
            return self._generate_claude(prompt, **kwargs)
        elif self.provider == 'ollama':
            return self._generate_ollama(prompt, **kwargs)
        elif self.provider == 'tongyi':
            return self._generate_tongyi(prompt, **kwargs)
        elif self.provider == 'deepseek':
            return self._generate_deepseek(prompt, **kwargs)
        elif self.provider == 'hunyuan':
            return self._generate_hunyuan(prompt, **kwargs)
        elif self.provider == 'zhipu':
            return self._generate_zhipu(prompt, **kwargs)
    
    def _generate_gemini(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content with Gemini"""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': kwargs.get('temperature', self.config.get('temperature', 0.7)),
                    'max_output_tokens': kwargs.get('max_tokens', self.config.get('max_tokens', 8192)),
                }
            )
            
            # Check response
            if not response.candidates:
                return {'error': '响应中没有候选项', 'text': None}
            
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # Handle safety filter
            if finish_reason == 1 or str(finish_reason).upper() == "SAFETY":
                return {
                    'error': '内容被安全过滤器阻止',
                    'finish_reason': 'SAFETY',
                    'text': None,
                    'safety_ratings': getattr(candidate, 'safety_ratings', [])
                }
            
            # Extract text
            try:
                text = response.text.strip()
            except:
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text.strip()
                else:
                    return {'error': '无法提取响应文本', 'text': None}
            
            return {'text': text, 'finish_reason': finish_reason}
            
        except Exception as e:
            return {'error': str(e), 'text': None}
    
    def _generate_openai(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """OpenAI生成内容"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻分析助手，擅长分析、翻译和总结新闻文章。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', self.config.get('temperature', 0.7)),
                max_tokens=kwargs.get('max_tokens', self.config.get('max_tokens', 4096)),
            )
            
            text = response.choices[0].message.content.strip()
            finish_reason = response.choices[0].finish_reason
            
            return {'text': text, 'finish_reason': finish_reason}
            
        except Exception as e:
            return {'error': str(e), 'text': None}
    
    def _generate_claude(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Claude生成内容"""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=kwargs.get('max_tokens', self.config.get('max_tokens', 4096)),
                temperature=kwargs.get('temperature', self.config.get('temperature', 0.7)),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            text = response.content[0].text.strip()
            stop_reason = response.stop_reason
            
            return {'text': text, 'finish_reason': stop_reason}
            
        except Exception as e:
            return {'error': str(e), 'text': None}
    
    def _generate_ollama(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Ollama生成内容"""
        try:
            import requests
            
            url = f"{self.client['base_url']}/api/generate"
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.get('temperature', 0.7)),
                    "num_predict": kwargs.get('max_tokens', self.config.get('max_tokens', 4096)),
                }
            }
            
            response = requests.post(url, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            text = result.get('response', '').strip()
            
            return {'text': text, 'finish_reason': 'stop'}
            
        except Exception as e:
            return {'error': str(e), 'text': None}
    
    def _generate_tongyi(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content with Tongyi"""
        try:
            # Check client type
            if isinstance(self.client, dict) and self.client.get('type') == 'dashscope':
                # Use DashScope SDK
                import dashscope
                from dashscope import Generation
                
                messages = [
                    {"role": "system", "content": "你是一个专业的新闻分析助手，擅长分析、翻译和总结新闻文章。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=kwargs.get('temperature', self.config.get('temperature', 0.7)),
                    max_tokens=kwargs.get('max_tokens', self.config.get('max_tokens', 2000)),
                )
                
                if response.status_code == 200:
                    text = response.output.choices[0].message.content.strip()
                    return {'text': text, 'finish_reason': 'stop'}
                else:
                    error_msg = f"DashScope API错误: {response.status_code} - {response.message}"
                    if response.status_code == 401:
                        error_msg += "\n提示: API密钥可能无效。请检查："
                        error_msg += "\n1. API密钥是否正确（通义千问的密钥通常不以'sk-'开头）"
                        error_msg += "\n2. 是否在阿里云百炼平台开通了服务"
                        error_msg += "\n3. 访问 https://bailian.console.aliyun.com/ 获取正确的API密钥"
                    return {'error': error_msg, 'text': None}
            else:
                # Use OpenAI compatible interface
                client = self.client.get('client') if isinstance(self.client, dict) else self.client
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的新闻分析助手，擅长分析、翻译和总结新闻文章。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=kwargs.get('temperature', self.config.get('temperature', 0.7)),
                    max_tokens=kwargs.get('max_tokens', self.config.get('max_tokens', 2000)),
                )
                
                text = response.choices[0].message.content.strip()
                finish_reason = response.choices[0].finish_reason
                
                return {'text': text, 'finish_reason': finish_reason}
            
        except Exception as e:
            error_msg = str(e)
            # Improve 401 error message
            if '401' in error_msg or 'invalid_api_key' in error_msg.lower() or 'Incorrect API key' in error_msg:
                error_msg += "\n\n💡 通义千问API密钥获取指南："
                error_msg += "\n1. 访问 https://bailian.console.aliyun.com/"
                error_msg += "\n2. 登录阿里云账号并开通百炼服务"
                error_msg += "\n3. 在控制台创建API密钥（注意：密钥格式通常不以'sk-'开头）"
                error_msg += "\n4. 设置环境变量: export DASHSCOPE_API_KEY='your-actual-key'"
            return {'error': error_msg, 'text': None}
    
    def _generate_deepseek(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """DeepSeek生成内容（使用OpenAI兼容接口）"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻分析助手，擅长分析、翻译和总结新闻文章。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', self.config.get('temperature', 0.7)),
                max_tokens=kwargs.get('max_tokens', self.config.get('max_tokens', 4096)),
            )
            
            text = response.choices[0].message.content.strip()
            finish_reason = response.choices[0].finish_reason
            
            return {'text': text, 'finish_reason': finish_reason}
            
        except Exception as e:
            error_msg = str(e)
            # Improve error message
            if '402' in error_msg or 'Insufficient Balance' in error_msg or '余额不足' in error_msg:
                error_msg = f"DeepSeek账户余额不足 (402)\n\n💡 解决方案："
                error_msg += "\n1. 访问 https://platform.deepseek.com/ 登录账户"
                error_msg += "\n2. 检查账户余额并充值"
                error_msg += "\n3. 或者切换到其他AI提供商（如Gemini、通义千问等）"
                error_msg += f"\n   设置环境变量: export AI_PROVIDER='gemini' 或其他可用提供商"
            elif '401' in error_msg or 'invalid_api_key' in error_msg.lower() or 'Incorrect API key' in error_msg:
                error_msg += "\n\n💡 DeepSeek API密钥获取指南："
                error_msg += "\n1. 访问 https://platform.deepseek.com/"
                error_msg += "\n2. 注册/登录账户"
                error_msg += "\n3. 在控制台创建API密钥"
                error_msg += "\n4. 设置环境变量: export DEEPSEEK_API_KEY='your-api-key'"
            return {'error': error_msg, 'text': None}
    
    def _generate_hunyuan(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """腾讯混元生成内容"""
        try:
            from tencentcloud.hunyuan.v20230901 import models
            
            req = models.ChatCompletionsRequest()
            req.Model = self.model_name
            req.Messages = [
                {
                    "Role": "system",
                    "Content": "你是一个专业的新闻分析助手，擅长分析、翻译和总结新闻文章。"
                },
                {
                    "Role": "user",
                    "Content": prompt
                }
            ]
            req.Temperature = kwargs.get('temperature', self.config.get('temperature', 0.7))
            req.MaxTokens = kwargs.get('max_tokens', self.config.get('max_tokens', 4096))
            
            resp = self.client.ChatCompletions(req)
            
            if resp.Choices and len(resp.Choices) > 0:
                text = resp.Choices[0].Message.Content.strip()
                finish_reason = getattr(resp.Choices[0], 'FinishReason', 'stop')
                return {'text': text, 'finish_reason': finish_reason}
            else:
                return {'error': '响应中没有内容', 'text': None}
            
        except Exception as e:
            return {'error': str(e), 'text': None}
    
    def _generate_zhipu(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content with ZhipuAI"""
        try:
            # Build request parameters
            request_params = {
                'model': self.model_name,
                'messages': [
                    {"role": "system", "content": "你是一个专业的新闻分析助手，擅长分析、翻译和总结新闻文章。"},
                    {"role": "user", "content": prompt}
                ],
                'max_tokens': kwargs.get('max_tokens', self.config.get('max_tokens', 65536)),
                'temperature': kwargs.get('temperature', self.config.get('temperature', 1.0)),
            }
            
            # Control thinking mode explicitly
            # For greeting generation, we don't need thinking mode (it's too verbose)
            thinking_enabled = kwargs.get('thinking_enabled', self.config.get('thinking_enabled', False))
            if thinking_enabled:
                request_params['thinking'] = {
                    "type": "enabled"
                }
            else:
                # Explicitly disable thinking mode for glm-4.7 (which may enable it by default)
                request_params['thinking'] = {
                    "type": "disabled"
                }
            
            response = self.client.chat.completions.create(**request_params)
            
            # Debug: Print full response structure for troubleshooting
            print(f"  🔍 [DEBUG] Response type: {type(response)}")
            print(f"  🔍 [DEBUG] Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            # Get reply content
            if not hasattr(response, 'choices') or len(response.choices) == 0:
                raise Exception("响应中没有 choices")
            
            choice = response.choices[0]
            print(f"  🔍 [DEBUG] Choice type: {type(choice)}")
            print(f"  🔍 [DEBUG] Choice dir: {[attr for attr in dir(choice) if not attr.startswith('_')]}")
            
            message = choice.message
            print(f"  🔍 [DEBUG] Message type: {type(message)}")
            print(f"  🔍 [DEBUG] Message dir: {[attr for attr in dir(message) if not attr.startswith('_')]}")
            
            # ZhipuAI response format may differ, need to adapt
            text = ''
            
            # Try multiple ways to extract content
            # Note: zhipu may put content in 'content' or 'reasoning_content' depending on model
            if hasattr(message, 'content'):
                text = message.content if message.content is not None else ''
                print(f"  🔍 [DEBUG] message.content: {repr(text[:100] if text else '')}")
            
            # If content is empty, try reasoning_content (for thinking models)
            # But we need to extract the final answer from reasoning_content, not return the whole thinking process
            if not text and hasattr(message, 'reasoning_content'):
                reasoning = message.reasoning_content if message.reasoning_content is not None else ''
                print(f"  🔍 [DEBUG] message.reasoning_content exists (length: {len(reasoning) if reasoning else 0})")
                
                # Try to extract final greeting from reasoning_content
                # Look for patterns like "**选择：**" or "最终：" or quotes
                # Pattern 1: Look for "**选择：**" or "**最终：**" followed by quoted text
                patterns = [
                    r'\*\*选择[：:]\*\*\s*\*\*([^*]+)\*\*',  # **选择：** **问候语**
                    r'\*\*最终[：:]\*\*\s*\*\*([^*]+)\*\*',  # **最终：** **问候语**
                    r'选择[：:]\s*[“"]([^"”]+)[“"]',  # 选择："问候语"
                    r'最终[：:]\s*[“"]([^"”]+)[“"]',  # 最终："问候语"
                    r'[“"]([^"”]{5,25})[“"]',  # Any quoted text between 5-25 chars (likely the greeting)
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, reasoning)
                    if matches:
                        # Take the last match (usually the final choice)
                        text = matches[-1].strip()
                        print(f"  🔍 [DEBUG] Extracted from reasoning_content: {repr(text)}")
                        break
                
                # If no pattern matched, use reasoning_content as fallback (but it's too verbose)
                if not text and reasoning:
                    # This shouldn't happen, but if it does, we'll use reasoning_content
                    text = reasoning
                    print(f"  ⚠️  [DEBUG] Could not extract final answer from reasoning_content, using full content")
            
            # Try other possible fields
            if not text and hasattr(message, 'text'):
                text = message.text if message.text is not None else ''
                print(f"  🔍 [DEBUG] message.text: {repr(text)}")
            
            # Try to_dict() method (Pydantic model)
            if not text and hasattr(message, 'to_dict'):
                try:
                    msg_dict = message.to_dict()
                    text = msg_dict.get('content', '') or msg_dict.get('reasoning_content', '') or msg_dict.get('text', '')
                    print(f"  🔍 [DEBUG] message.to_dict(): {msg_dict}")
                    print(f"  🔍 [DEBUG] Extracted from dict: {repr(text)}")
                except Exception as e:
                    print(f"  🔍 [DEBUG] to_dict() failed: {e}")
            
            # Try model_dump() method (Pydantic v2)
            if not text and hasattr(message, 'model_dump'):
                try:
                    msg_dict = message.model_dump()
                    text = msg_dict.get('content', '') or msg_dict.get('reasoning_content', '') or msg_dict.get('text', '')
                    print(f"  🔍 [DEBUG] message.model_dump(): {msg_dict}")
                    print(f"  🔍 [DEBUG] Extracted from model_dump: {repr(text)}")
                except Exception as e:
                    print(f"  🔍 [DEBUG] model_dump() failed: {e}")
            
            # Fallback to dict access
            if not text and isinstance(message, dict):
                text = message.get('content', '') or message.get('reasoning_content', '') or message.get('text', '')
                print(f"  🔍 [DEBUG] message (dict): {message}")
            
            # Strip whitespace
            text = text.strip() if text else ''
            
            finish_reason = getattr(choice, 'finish_reason', None) or getattr(response.choices[0], 'finish_reason', 'stop')
            print(f"  🔍 [DEBUG] finish_reason: {finish_reason}")
            print(f"  🔍 [DEBUG] Final text: {repr(text)}")
            
            # If text is still empty, try to access raw response using to_dict or model_dump
            if not text:
                print(f"  🔍 [DEBUG] 尝试从原始响应中提取...")
                try:
                    # Try to_dict() method
                    if hasattr(response, 'to_dict'):
                        resp_dict = response.to_dict()
                        print(f"  🔍 [DEBUG] response.to_dict() keys: {list(resp_dict.keys())}")
                        if 'choices' in resp_dict and resp_dict['choices']:
                            first_choice = resp_dict['choices'][0]
                            if isinstance(first_choice, dict):
                                msg_data = first_choice.get('message', {})
                                text = msg_data.get('content', '') or msg_data.get('reasoning_content', '') or msg_data.get('text', '')
                                print(f"  🔍 [DEBUG] 从 to_dict() 提取的 text: {repr(text)}")
                                print(f"  🔍 [DEBUG] 完整的 message 数据: {msg_data}")
                    
                    # Try model_dump() method (Pydantic v2)
                    if not text and hasattr(response, 'model_dump'):
                        resp_dict = response.model_dump()
                        print(f"  🔍 [DEBUG] response.model_dump() keys: {list(resp_dict.keys())}")
                        if 'choices' in resp_dict and resp_dict['choices']:
                            first_choice = resp_dict['choices'][0]
                            if isinstance(first_choice, dict):
                                msg_data = first_choice.get('message', {})
                                text = msg_data.get('content', '') or msg_data.get('reasoning_content', '') or msg_data.get('text', '')
                                print(f"  🔍 [DEBUG] 从 model_dump() 提取的 text: {repr(text)}")
                                print(f"  🔍 [DEBUG] 完整的 message 数据: {msg_data}")
                    
                    # Try __dict__ as last resort
                    if not text and hasattr(response, '__dict__'):
                        resp_dict = response.__dict__
                        print(f"  🔍 [DEBUG] response.__dict__ keys: {list(resp_dict.keys())}")
                        if 'choices' in resp_dict:
                            choices_data = resp_dict['choices']
                            if choices_data and len(choices_data) > 0:
                                first_choice = choices_data[0]
                                if hasattr(first_choice, 'to_dict'):
                                    choice_dict = first_choice.to_dict()
                                    msg_data = choice_dict.get('message', {})
                                    if isinstance(msg_data, dict):
                                        text = msg_data.get('content', '') or msg_data.get('reasoning_content', '')
                                    elif hasattr(msg_data, 'to_dict'):
                                        text = msg_data.to_dict().get('content', '') or msg_data.to_dict().get('reasoning_content', '')
                                    print(f"  🔍 [DEBUG] 从 __dict__ 提取的 text: {repr(text)}")
                except Exception as e:
                    print(f"  🔍 [DEBUG] 提取失败: {e}")
                    import traceback
                    print(f"  🔍 [DEBUG] 错误详情: {traceback.format_exc()[:300]}")
            
            # Final check
            if not text and finish_reason == 'length':
                print(f"  ⚠️  警告: finish_reason='length' 但 text 为空")
                print(f"  ⚠️  这可能表示响应被截断，但内容提取失败")
                print(f"  ⚠️  请检查 zhipu SDK 的响应格式")
            
            return {'text': text, 'finish_reason': finish_reason}
            
        except Exception as e:
            error_msg = str(e)
            # Improve error message
            if '401' in error_msg or 'invalid_api_key' in error_msg.lower() or 'Incorrect API key' in error_msg:
                error_msg += "\n\n💡 智谱AI API密钥获取指南："
                error_msg += "\n1. 访问 https://open.bigmodel.cn/"
                error_msg += "\n2. 注册/登录账户"
                error_msg += "\n3. 在控制台创建API密钥"
                error_msg += "\n4. 设置环境变量: export ZHIPU_API_KEY='your-api-key'"
            elif '402' in error_msg or 'Insufficient Balance' in error_msg or '余额不足' in error_msg:
                error_msg = f"智谱AI账户余额不足 (402)\n\n💡 解决方案："
                error_msg += "\n1. 访问 https://open.bigmodel.cn/ 登录账户"
                error_msg += "\n2. 检查账户余额并充值"
                error_msg += "\n3. 或者切换到其他AI提供商"
            return {'error': error_msg, 'text': None}