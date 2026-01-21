#!/usr/bin/env python3
"""
Weather information fetcher
Fetch current weather data for Nigeria (Abuja) from OpenWeatherMap API

API Key Configuration:
- Local debugging: Set environment variable OPENWEATHER_API_KEY
  Example: export OPENWEATHER_API_KEY='your-api-key'
- GitHub Actions: API key is automatically provided via secrets (OPENWEATHER_API_KEY)
  The secrets are set as environment variables in the workflow

Get API key: https://openweathermap.org/api
Free tier: 1,000 calls/day, 60 calls/minute
"""

import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional, Any

# Nigeria timezone (Africa/Lagos, UTC+1)
NIGERIA_TZ = ZoneInfo('Africa/Lagos')

# Default location: Abuja, Nigeria
DEFAULT_CITY = "Abuja,NG"
DEFAULT_LAT = 9.0765  # Abuja latitude
DEFAULT_LON = 7.3986  # Abuja longitude

def fetch_weather(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch current weather data from OpenWeatherMap API
    
    Args:
        city: City name (e.g., "Abuja,NG") - optional if lat/lon provided
        lat: Latitude (optional, used with lon)
        lon: Longitude (optional, used with lat)
        api_key: OpenWeatherMap API key (optional, will use env var if not provided)
    
    Returns:
        Dictionary containing structured weather data:
        {
            'location': str,
            'temperature_c': float,
            'temperature_f': float,
            'feels_like_c': float,
            'humidity': int,
            'pressure_hPa': float,
            'wind_speed_m_s': float,
            'wind_direction_deg': int,
            'weather_main': str,
            'weather_description': str,
            'cloudiness': int,
            'visibility_m': int,
            'uv_index': float (if available),
            'air_quality': dict (if available),
            'datetime_local': str,
            'sunrise': str,
            'sunset': str
        }
    
    Raises:
        ValueError: If API key is missing
        requests.RequestException: If API request fails
    """
    # Get API key
    if not api_key:
        api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        raise ValueError(
            "OpenWeatherMap API key is required. "
            "Set OPENWEATHER_API_KEY environment variable or pass api_key parameter. "
            "Get your API key at: https://openweathermap.org/api"
        )
    
    # Use provided coordinates or city name
    if lat is not None and lon is not None:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "lang": "en"
        }
        location_desc = f"({lat}, {lon})"
    elif city:
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "en"
        }
        location_desc = city
    else:
        # Use default Abuja coordinates
        params = {
            "lat": DEFAULT_LAT,
            "lon": DEFAULT_LON,
            "appid": api_key,
            "units": "metric",
            "lang": "en"
        }
        location_desc = DEFAULT_CITY
    
    # Fetch current weather
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch weather data: {str(e)}")
    except ValueError as e:
        raise Exception(f"Invalid JSON response: {str(e)}")
    
    # Extract weather data
    main = data.get('main', {})
    wind = data.get('wind', {})
    weather_list = data.get('weather', [])
    clouds = data.get('clouds', {})
    sys_data = data.get('sys', {})
    
    # Get weather description
    weather_main = None
    weather_description = None
    if weather_list:
        weather_main = weather_list[0].get('main')
        weather_description = weather_list[0].get('description')
    
    # Convert timestamps to Nigeria time
    dt_utc = datetime.fromtimestamp(data.get('dt', 0), tz=ZoneInfo('UTC'))
    dt_local = dt_utc.astimezone(NIGERIA_TZ)
    
    sunrise_utc = datetime.fromtimestamp(sys_data.get('sunrise', 0), tz=ZoneInfo('UTC'))
    sunrise_local = sunrise_utc.astimezone(NIGERIA_TZ)
    
    sunset_utc = datetime.fromtimestamp(sys_data.get('sunset', 0), tz=ZoneInfo('UTC'))
    sunset_local = sunset_utc.astimezone(NIGERIA_TZ)
    
    # Build result dictionary
    result = {
        'location': f"{data.get('name', 'Unknown')}, {sys_data.get('country', 'NG')}",
        'coordinates': {
            'lat': data.get('coord', {}).get('lat'),
            'lon': data.get('coord', {}).get('lon')
        },
        'temperature_c': round(main.get('temp'), 1) if main.get('temp') else None,
        'temperature_f': round(main.get('temp') * 9/5 + 32, 1) if main.get('temp') else None,
        'feels_like_c': round(main.get('feels_like'), 1) if main.get('feels_like') else None,
        'humidity': main.get('humidity'),
        'pressure_hPa': main.get('pressure'),
        'wind_speed_m_s': round(wind.get('speed', 0), 2),
        'wind_speed_kmh': round(wind.get('speed', 0) * 3.6, 2) if wind.get('speed') else None,
        'wind_direction_deg': wind.get('deg'),
        'wind_direction': _deg_to_direction(wind.get('deg')) if wind.get('deg') else None,
        'weather_main': weather_main,
        'weather_description': weather_description,
        'cloudiness': clouds.get('all'),
        'visibility_m': data.get('visibility'),
        'visibility_km': round(data.get('visibility', 0) / 1000, 2) if data.get('visibility') else None,
        'datetime_local': dt_local.isoformat(),
        'datetime_utc': dt_utc.isoformat(),
        'sunrise': sunrise_local.strftime('%H:%M:%S'),
        'sunset': sunset_local.strftime('%H:%M:%S'),
        'timezone': 'Africa/Lagos',
    }
    
    # Try to fetch air quality data (requires separate API call)
    try:
        if lat is not None and lon is not None:
            coords = (lat, lon)
        else:
            coords = (data.get('coord', {}).get('lat'), data.get('coord', {}).get('lon'))
        
        if coords[0] and coords[1]:
            air_quality = fetch_air_quality(coords[0], coords[1], api_key)
            if air_quality:
                result['air_quality'] = air_quality
    except Exception as e:
        # Air quality is optional, don't fail if it's not available
        print(f"  ⚠️  无法获取空气质量数据: {str(e)[:50]}")
    
    return result

def fetch_air_quality(lat: float, lon: float, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch air quality data from OpenWeatherMap Air Pollution API
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: OpenWeatherMap API key
    
    Returns:
        Dictionary with air quality data or None if unavailable
    """
    try:
        url = "https://api.openweathermap.org/data/2.5/air_pollution"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'list' in data and len(data['list']) > 0:
            aq_data = data['list'][0]
            components = aq_data.get('components', {})
            aqi = aq_data.get('main', {}).get('aqi')  # 1-5 scale
            
            # AQI descriptions
            aqi_levels = {
                1: "Good",
                2: "Fair",
                3: "Moderate",
                4: "Poor",
                5: "Very Poor"
            }
            
            return {
                'aqi': aqi,
                'aqi_level': aqi_levels.get(aqi, "Unknown"),
                'co': round(components.get('co', 0), 2),
                'no2': round(components.get('no2', 0), 2),
                'o3': round(components.get('o3', 0), 2),
                'pm2_5': round(components.get('pm2_5', 0), 2),
                'pm10': round(components.get('pm10', 0), 2),
                'so2': round(components.get('so2', 0), 2),
            }
    except Exception:
        # Air quality API might not be available in free tier or might fail
        return None
    
    return None

def _deg_to_direction(degrees: int) -> str:
    """Convert wind direction in degrees to cardinal direction"""
    if degrees is None:
        return None
    
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

def format_weather_summary(weather: Dict[str, Any]) -> str:
    """
    Format weather data as a human-readable summary string
    
    Args:
        weather: Weather data dictionary from fetch_weather()
    
    Returns:
        Formatted string summary
    """
    lines = []
    
    # Location and time
    lines.append(f"📍 {weather.get('location', 'Unknown location')}")
    datetime_local = weather.get('datetime_local', '')
    if datetime_local:
        try:
            dt = datetime.fromisoformat(datetime_local)
            lines.append(f"🕐 {dt.strftime('%Y-%m-%d %H:%M:%S')} (尼日利亚时间)")
        except (ValueError, TypeError):
            # If datetime parsing fails, skip time line
            pass
    
    # Temperature
    temp_c = weather.get('temperature_c')
    feels_like = weather.get('feels_like_c')
    if temp_c is not None:
        temp_str = f"🌡️  {temp_c}°C"
        if feels_like is not None and abs(feels_like - temp_c) > 2:
            temp_str += f" (体感 {feels_like}°C)"
        lines.append(temp_str)
    
    # Weather description
    desc = weather.get('weather_description', '')
    if desc:
        lines.append(f"☁️  {desc.capitalize()}")
    
    # Wind
    wind_speed = weather.get('wind_speed_kmh')
    wind_dir = weather.get('wind_direction')
    if wind_speed is not None:
        wind_str = f"💨 风速: {wind_speed} km/h"
        if wind_dir:
            wind_str += f" ({wind_dir})"
        lines.append(wind_str)
    
    # Humidity
    humidity = weather.get('humidity')
    if humidity is not None:
        lines.append(f"💧 湿度: {humidity}%")
    
    # Air quality
    aq = weather.get('air_quality')
    if aq:
        aqi_level = aq.get('aqi_level', 'Unknown')
        pm25 = aq.get('pm2_5')
        lines.append(f"🌬️  空气质量: {aqi_level}")
        if pm25 is not None:
            lines.append(f"   PM2.5: {pm25} μg/m³")
    
    return "\n".join(lines)

def main():
    """Main function for command-line usage"""
    import sys
    
    # Get city from command line or environment variable
    city = None
    if len(sys.argv) > 1:
        city = sys.argv[1]
    else:
        city = os.getenv('WEATHER_CITY', DEFAULT_CITY)
    
    try:
        print(f"🌤️  正在获取天气信息: {city}")
        weather = fetch_weather(city=city)
        
        print("\n" + "=" * 60)
        print("天气信息 (结构化数据)")
        print("=" * 60)
        import json
        print(json.dumps(weather, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
        print("天气摘要")
        print("=" * 60)
        print(format_weather_summary(weather))
        
        return weather
        
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n请设置环境变量:")
        print("  export OPENWEATHER_API_KEY='your-api-key'")
        print("\n获取 API key: https://openweathermap.org/api")
        return None
    except Exception as e:
        print(f"❌ 获取天气失败: {e}")
        return None

if __name__ == '__main__':
    main()
