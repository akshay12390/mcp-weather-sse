import argparse
import os
from dotenv import load_dotenv
import sys
import json
import logging
import asyncio
import requests
from typing import Optional, Dict, Any, List

from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp-weather-sse")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
OPENWEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5"

class WeatherSSEServer:
    """MCP Server that connects to OpenWeatherMap API through SSE."""

    def __init__(self, api_key: str, port: int = DEFAULT_PORT, host: str = DEFAULT_HOST):
        self.api_key = api_key
        self.port = port
        self.host = host
        self.server = FastMCP("Weather SSE Server", version="1.0.0")
        self._register_tools()

    def _register_tools(self):
        @self.server.tool(name="get_current_weather", description="Get current weather for a city")
        async def handle_current_weather(city: str, units: str = "metric") -> Dict[str, Any]:
            try:
                url = f"{OPENWEATHER_API_BASE_URL}/weather"
                response = requests.get(
                    url,
                    params={
                        "q": city,
                        "units": units,
                        "appid": self.api_key
                    }
                )
                response.raise_for_status()
                weather_data = response.json()

                result = self._format_current_weather(weather_data, units)

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching weather data: {str(e)}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error fetching weather data: {str(e)}"
                        }
                    ]
                }

        @self.server.tool(name="get_weather_forecast", description="Get weather forecast for a city")
        async def handle_weather_forecast(city: str, days: int = 3, units: str = "metric") -> Dict[str, Any]:
            try:
                url = f"{OPENWEATHER_API_BASE_URL}/forecast"
                response = requests.get(
                    url,
                    params={
                        "q": city,
                        "units": units,
                        "appid": self.api_key
                    }
                )
                response.raise_for_status()
                forecast_data = response.json()

                result = self._format_forecast(forecast_data, days, units)

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching forecast data: {str(e)}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error fetching forecast data: {str(e)}"
                        }
                    ]
                }

        @self.server.tool(name="get_weather_by_coordinates", description="Get weather for specific coordinates")
        async def handle_weather_by_coordinates(latitude: float, longitude: float, units: str = "metric") -> Dict[str, Any]:
            try: 
                url = f"{OPENWEATHER_API_BASE_URL}/weather"
                response = requests.get(
                    url,
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "units": units,
                        "appid": self.api_key
                    }
                )
                response.raise_for_status()
                weather_data = response.json()

                result = self._format_current_weather(weather_data, units)

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching weather data by coordinates: {str(e)}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error fetching weather data by coordinates: {str(e)}"
                        }   
                    ]
                }

    def _format_current_weather(self, data: Dict[str, Any], units: str) -> Dict[str, Any]:
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        try:
            weather = {
                "location": {
                    "name": data.get("name", "Unknown"),
                    "country": data.get("sys", {}).get("country", "Unknown"),
                    "coordinates": {
                        "latitude": data.get("coord", {}).get("lat", 0),
                        "longitude": data.get("coord", {}).get("lon", 0)
                    }
                },
                "current": {
                    "temperature": f"{data.get('main', {}).get('temp', 0)}{temp_unit}",
                    "feels_like": f"{data.get('main', {}).get('feels_like', 0)}{temp_unit}",
                    "humidity": f"{data.get('main', {}).get('humidity', 0)}%",
                    "pressure": f"{data.get('main', {}).get('pressure', 0)} hPa",
                    "wind": {
                        "speed": f"{data.get('wind', {}).get('speed', 0)} {speed_unit}",
                        "direction": data.get('wind', {}).get('deg', 0)
                    },
                    "weather": {
                        "main": data.get('weather', [{}])[0].get('main', "Unknown"),
                        "description": data.get('weather', [{}])[0].get('description', "Unknown"),
                        "icon": data.get('weather', [{}])[0].get('icon', "Unknown")
                    },
                    "visibility": f"{data.get('visibility', 0) / 1000} km",
                    "cloudiness": f"{data.get('clouds', {}).get('all', 0)}%",
                    "sunrise": data.get('sys', {}).get('sunrise', 0),
                    "sunset": data.get('sys', {}).get('sunset', 0)
                }
            }

            if 'rain' in data:
                weather['current']['rain'] = {
                    "1h": f"{data['rain'].get('1h', 0)} mm",
                }

            if 'snow' in data:
                weather['current']['snow'] = {
                    "1h": f"{data['snow'].get('1h', 0)} mm",
                }

            return weather

        except (KeyError, IndexError) as e:
            logger.error(f"Error formatting current weather data: {str(e)}")
            return {
                "error": "Error formatting current weather data",
                "details": str(e)
            }

    def _format_forecast(self, data: Dict[str, Any], days: int, units: str) -> Dict[str, Any]:
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        try:
            city_data = data.get("city", {})
            forecast_list = data.get("list", [])

            daily_forecasts = {}

            for item in forecast_list:
            
                date = item.get("dt_txt", "").split(" ")[0]

                if date not in daily_forecasts:
                    daily_forecasts[date] = []

                daily_forecasts[date].append({
                    "time": item.get("dt_txt", "").split(" ")[1],
                    "temperature": f"{item.get('main', {}).get('temp', 0)}{temp_unit}",
                    "feels_like": f"{item.get('main', {}).get('feels_like', 0)}{temp_unit}",
                    "min_temp": f"{item.get('main', {}).get('temp_min', 0)}{temp_unit}",
                    "max_temp": f"{item.get('main', {}).get('temp_max', 0)}{temp_unit}",
                    "humidity": f"{item.get('main', {}).get('humidity', 0)}%",
                    "pressure": f"{item.get('main', {}).get('pressure', 0)} hPa",
                    "weater": {
                        "main": item.get('weather', [{}])[0].get('main', "Unknown"),
                        "description": item.get('weather', [{}])[0].get('description', "Unknown"),
                        "icon": item.get('weather', [{}])[0].get('icon', "Unknown")
                    },
                    "wind": {
                        "speed": f"{item.get('wind', {}).get('speed', 0)} {speed_unit}",
                        "direction": item.get('wind', {}).get('deg', 0)
                    },
                    "cloudiness": f"{item.get('clouds', {}).get('all', 0)}%"
                })

            forecast_dates = list(daily_forecasts.keys())[:days]
            limited_forecasts = {date: daily_forecasts[date] for date in forecast_dates if date in daily_forecasts}

            return {
                "location": {
                    "name": city_data.get("name", "Unknown"),
                    "country": city_data.get("country", "Unknown"),
                    "coordinates": {
                        "latitude": city_data.get("coord", {}).get("lat", 0),
                        "longitude": city_data.get("coord", {}).get("lon", 0)
                    }
                },
                "forecast": limited_forecasts
            }

        except (KeyError, IndexError) as e:
            logger.error(f"Error formatting weather forecast data: {str(e)}")
            return {
                "error": "Error formatting weather forecast data",
                "details": str(e)
            }
    def _get_wind_direction(self, degrees: float) -> str:
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        index = round(degrees / (360 / len(directions))) % len(directions)
        return directions[index]

    async def start(self):
        logger.info(f"Starting MCP Weather SSE Server on {self.host}:{self.port}")
        await self.server.run_sse_async()

def parse_args():
    parser = argparse.ArgumentParser(description="MCP Weather SSE Server")
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Host address (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port number (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="OpenWeatherMap API key"
    )
    return parser.parse_args()

async def main():
    args = parse_args()
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("API key is required. Please provide it using --api-key or set the OPENWEATHER_API_KEY environment variable.")
        sys.exit(1)

    server = WeatherSSEServer(api_key=api_key, port=args.port, host=args.host)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())