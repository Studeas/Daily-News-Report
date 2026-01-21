#!/usr/bin/env python3
"""
Greeting generator
Generate humorous and positive greetings based on time of day using AI

API Key Configuration:
- Local debugging: Set environment variable ZHIPU_API_KEY
  Example: export ZHIPU_API_KEY='your-api-key'
- GitHub Actions: API key is automatically provided via secrets (ZHIPU_API_KEY)
  The secrets are set as environment variables in the workflow
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from ai_client import AIClient
from config import is_available, get_config
from typing import Dict, Optional, Any

# Nigeria timezone (Africa/Lagos, UTC+1)
NIGERIA_TZ = ZoneInfo('Africa/Lagos')

# Default greeting as fallback
DEFAULT_GREETING = "你好！"

def get_current_time_info():
    """Get current time information in Nigeria timezone"""
    now_nigeria = datetime.now(NIGERIA_TZ)
    return {
        'hour': now_nigeria.hour,
        'minute': now_nigeria.minute,
        'date': now_nigeria.strftime('%Y-%m-%d'),
        'time': now_nigeria.strftime('%H:%M:%S'),
        'weekday': now_nigeria.strftime('%A')
    }

def get_weather_info() -> Optional[Dict[str, Any]]:
    """
    Fetch weather information for Nigeria (Abuja)
    
    Returns:
        Dictionary with weather data or None if unavailable
    """
    try:
        from weather import fetch_weather, format_weather_summary
        weather = fetch_weather()
        weather_summary = format_weather_summary(weather)
        return {
            'data': weather,
            'summary': weather_summary
        }
    except ImportError:
        print("  ⚠️  天气模块未找到，跳过天气信息")
        return None
    except Exception as e:
        print(f"  ⚠️  获取天气信息失败: {str(e)[:50]}，跳过天气信息")
        return None

def generate_greeting(use_ai=True, include_weather=True):
    """
    Generate greeting based on current time in Nigeria timezone, with weather information
    
    Args:
        use_ai: Whether to use AI to generate greeting (default: True)
        include_weather: Whether to include weather information (default: True)
    
    Returns:
        Dictionary containing:
        {
            'greeting': str,           # The greeting message
            'weather_summary': str,    # Formatted weather summary (original text)
            'weather_advice': str      # AI-generated weather-related advice
        }
        Or if use_ai=False: just returns the greeting string
    """
    time_info = get_current_time_info()
    
    # Get weather information
    weather_info = None
    if include_weather:
        print("  🌤️  正在获取天气信息...")
        weather_info = get_weather_info()
    
    # If AI is not requested, return default greeting
    if not use_ai:
        if weather_info:
            return {
                'greeting': DEFAULT_GREETING,
                'weather_summary': weather_info['summary'],
                'weather_advice': ''
            }
        return DEFAULT_GREETING
    
    # Try to generate greeting using AI
    try:
        # Use zhipu as the default AI provider (hardcoded)
        ai_provider = 'zhipu'
        
        # Check if zhipu is available
        if not is_available(ai_provider):
            # Check why zhipu is not available
            try:
                from config import config
                zhipu_config = config.configs.get('zhipu', {})
                if not zhipu_config.get('enabled', False):
                    print(f"  ⚠️  zhipu未启用")
                elif not zhipu_config.get('api_key'):
                    print(f"  ⚠️  zhipu API key未配置")
                    print(f"     本地调试：请设置环境变量 ZHIPU_API_KEY")
                    print(f"     示例：export ZHIPU_API_KEY='your-api-key'")
                    print(f"     GitHub Actions：会在 secrets 中自动配置")
                else:
                    print(f"  ⚠️  zhipu配置存在问题（API key已设置但可能无效）")
            except Exception as e:
                print(f"  ⚠️  检查zhipu配置时出错: {str(e)[:50]}")
            
            # Fallback: try to find any available provider
            try:
                from config import config
                available = config.get_available_providers()
                if available:
                    ai_provider = available[0]
                    print(f"  ⚠️  zhipu不可用，回退到可用的AI提供商: {ai_provider}")
                else:
                    print("  ⚠️  没有可用的AI提供商，使用默认问候语")
                    if weather_info:
                        return {
                            'greeting': DEFAULT_GREETING,
                            'weather_summary': weather_info['summary'],
                            'weather_advice': ''
                        }
                    return DEFAULT_GREETING
            except Exception as e:
                print(f"  ⚠️  无法检查AI提供商: {str(e)[:50]}，使用默认问候语")
                if weather_info:
                    return {
                        'greeting': DEFAULT_GREETING,
                        'weather_summary': weather_info['summary'],
                        'weather_advice': ''
                    }
                return DEFAULT_GREETING
        
        # Initialize AI client
        ai_client = AIClient(ai_provider)
        
        # Build weather context for prompt
        weather_context = ""
        if weather_info:
            weather_data = weather_info['data']
            temp_c = weather_data.get('temperature_c') or '未知'
            feels_like = weather_data.get('feels_like_c')
            feels_like_str = f" (体感 {feels_like}°C)" if feels_like else ""
            weather_desc = weather_data.get('weather_description', '未知') or '未知'
            humidity = weather_data.get('humidity') or '未知'
            wind_speed = weather_data.get('wind_speed_kmh') or '未知'
            wind_dir = weather_data.get('wind_direction', '') or ''
            wind_dir_str = f" {wind_dir}" if wind_dir else ""
            aq = weather_data.get('air_quality', {})
            aqi_level = aq.get('aqi_level', '未知') if aq else '未知'
            pm25 = aq.get('pm2_5', 'N/A') if aq else 'N/A'
            
            weather_context = f"""
                            当前天气信息（阿布贾）：
                            - 温度：{temp_c}°C{feels_like_str}
                            - 天气：{weather_desc}
                            - 湿度：{humidity}%
                            - 风速：{wind_speed} km/h{wind_dir_str}
                            - 空气质量：{aqi_level} (PM2.5: {pm25} μg/m³)
                            """
        
        # Create prompt with time and weather information
        prompt = f"""请根据当前时间和天气信息生成一句简短、幽默、阳光的问候语，用于每日新闻报告的邮件开头。

                当前时间信息：
                - 日期：{time_info['date']}
                - 时间：{time_info['time']} (尼日利亚时间)
                - 星期：{time_info['weekday']}
                - 小时：{time_info['hour']}点
                {weather_context}
                要求：
                1. 简短精炼，不超过35个字
                2. 幽默有趣，让人心情愉悦
                3. 阳光积极，充满正能量
                4. 根据当前时间（{time_info['hour']}点）自然判断是上午、下午还是晚上，并生成相应的问候语
                5. 可以适当结合天气情况，但不要过于详细
                6. 不要包含emoji或特殊符号
                7. 直接输出问候语，不要其他解释或引号
                8. 注意添加适当的标点符号，例如逗号、句号、感叹号。
                9. 偶尔可以引用书籍中的金句或者名人名言。

                请生成一句新的问候语（每次都要不同，要有创意）："""
        
        # Generate greeting
        print(f"  🤖 使用AI生成问候语（当前时间：{time_info['time']}，提供商：{ai_provider}）...")
        # Increase max_tokens to avoid truncation (100 was too small)
        result = ai_client.generate_content(prompt, temperature=0.6, max_tokens=1000)
        
        # Debug: print result structure for troubleshooting
        if result:
            # Try different possible field names for the response text
            greeting_text = result.get('text') or result.get('content') or result.get('message')
            
            if greeting_text:
                greeting = str(greeting_text).strip()
                # Clean up the greeting (remove quotes, extra spaces, etc.)
                greeting = greeting.strip('"').strip("'").strip()
                # Remove any leading/trailing punctuation that might be from AI response
                # Remove common AI response prefixes
                prefixes_to_remove = ['问候语：', '问候语:', '生成：', '生成:', '以下是', '建议：', '建议:', '根据当前时间']
                for prefix in prefixes_to_remove:
                    if greeting.startswith(prefix):
                        greeting = greeting[len(prefix):].strip()
                
                if greeting and len(greeting) > 0:
                    print(f"  ✓ AI生成问候语成功: {greeting[:30]}...")
                    
                    # Generate weather-related advice if weather info is available
                    weather_advice = ""
                    if weather_info:
                        weather_advice = generate_weather_advice(ai_client, weather_info['data'], time_info)
                    
                    # Return structured result
                    result_dict = {
                        'greeting': greeting,
                        'weather_summary': weather_info['summary'] if weather_info else '',
                        'weather_advice': weather_advice
                    }
                    return result_dict
            
            # If no text found, show debug information
            print(f"  🔍 调试信息 - 返回结果键: {list(result.keys())}")
            print(f"  🔍 调试信息 - 完整返回结果: {result}")
            
            # Check for error in result
            error_msg = result.get('error') or result.get('message') or ''
            if error_msg:
                print(f"  ⚠️  AI返回结果中没有文本内容")
                print(f"     错误信息: {error_msg[:200]}")
            else:
                print(f"  ⚠️  AI返回结果中没有文本内容")
        else:
            print(f"  ⚠️  AI返回结果为空（result is None）")
        
        # If AI generation failed, use default
        print(f"  ⚠️  AI生成问候语失败，使用默认问候语")
        if weather_info:
            return {
                'greeting': DEFAULT_GREETING,
                'weather_summary': weather_info['summary'],
                'weather_advice': ''
            }
        return DEFAULT_GREETING
        
    except ImportError as e:
        print(f"  ⚠️  AI客户端导入失败: {str(e)}，使用默认问候语")
        if weather_info:
            return {
                'greeting': DEFAULT_GREETING,
                'weather_summary': weather_info['summary'],
                'weather_advice': ''
            }
        return DEFAULT_GREETING
    except Exception as e:
        import traceback
        print(f"  ⚠️  生成AI问候语时出错: {str(e)}")
        print(f"  错误详情: {traceback.format_exc()[:200]}")
        print(f"  使用默认问候语")
        if weather_info:
            return {
                'greeting': DEFAULT_GREETING,
                'weather_summary': weather_info['summary'],
                'weather_advice': ''
            }
        return DEFAULT_GREETING

def generate_weather_advice(ai_client: AIClient, weather_data: Dict[str, Any], time_info: Dict[str, Any]) -> str:
    """
    Generate weather-related advice using AI
    
    Args:
        ai_client: AI client instance
        weather_data: Weather data dictionary
        time_info: Time information dictionary
    
    Returns:
        String with weather-related advice
    """
    try:
        temp = weather_data.get('temperature_c') or '未知'
        weather_desc = weather_data.get('weather_description', '') or '未知'
        humidity = weather_data.get('humidity') or '未知'
        wind_speed = weather_data.get('wind_speed_kmh') or '未知'
        aq = weather_data.get('air_quality', {})
        aqi_level = aq.get('aqi_level', '未知') if aq else '未知'
        
        prompt = f"""根据以下天气信息，生成一份简短、实用、积极的天气建议，包括：
                1. 穿衣建议（根据温度）
                2. 注意事项（如防晒、防雨、防风等）
                3. 保持心情愉快的建议
                4. 今天适合做的事情

                当前天气信息（尼日利亚阿布贾）：
                - 温度：{temp}°C
                - 天气：{weather_desc}
                - 湿度：{humidity}%
                - 风速：{wind_speed} km/h
                - 空气质量：{aqi_level}
                - 当前时间：{time_info['hour']}点

                要求：
                1. 简短精炼，总共不超过100个字
                2. 积极正面，让人心情愉悦
                3. 实用具体，给出可操作的建议
                4. 可以适当幽默，但不要过度
                5. 直接输出建议，不要其他解释或引号
                6. 使用自然的中文表达，可以分段但不要用列表符号

                请生成天气建议："""
        
        print(f"  🤖 使用AI生成天气建议...")
        result = ai_client.generate_content(prompt, temperature=0.7, max_tokens=300)
        
        if result:
            advice_text = result.get('text') or result.get('content') or result.get('message')
            if advice_text:
                advice = str(advice_text).strip()
                # Clean up
                advice = advice.strip('"').strip("'").strip()
                prefixes_to_remove = ['建议：', '建议:', '天气建议：', '天气建议:', '以下是', '根据天气']
                for prefix in prefixes_to_remove:
                    if advice.startswith(prefix):
                        advice = advice[len(prefix):].strip()
                
                if advice and len(advice) > 0:
                    print(f"  ✓ AI生成天气建议成功")
                    return advice
        
        print(f"  ⚠️  AI生成天气建议失败")
        return ""
        
    except Exception as e:
        print(f"  ⚠️  生成天气建议时出错: {str(e)[:50]}")
        return ""

def main():
    """Main function for command-line usage"""
    import sys
    import json
    
    # Check if --no-ai flag is provided
    use_ai = '--no-ai' not in sys.argv
    include_weather = '--no-weather' not in sys.argv
    
    result = generate_greeting(use_ai=use_ai, include_weather=include_weather)
    
    # Handle both string and dict return types
    if isinstance(result, dict):
        print("\n" + "=" * 60)
        print("问候语和天气信息")
        print("=" * 60)
        print(f"\n问候语：\n{result['greeting']}")
        if result.get('weather_summary'):
            print(f"\n天气摘要：\n{result['weather_summary']}")
        if result.get('weather_advice'):
            print(f"\n天气建议：\n{result['weather_advice']}")
        print("\n" + "=" * 60)
        print("\n完整JSON数据：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
    
    return result

if __name__ == '__main__':
    main()
