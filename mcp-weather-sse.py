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
        async def handle_current_weather(city: str) -> Dict[str, Any]:
            try:
                url = f"{OPENWEATHER_API_BASE_URL}/weather"
                response = requests.get(
                    url,
                    params={
                        "q": city,
                        "units": "metric",
                        "appid": self.api_key
                    }
                )
                response.raise_for_status()
                weather_data = response.json()

                result = self._format_current_weather(weather_data, "metric")

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result
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

        # @self.server.tool(name="get_weather_forecast", description="Get weather forecast for a city")
        # async def handle_weather_forecast(city: str) -> Dict[str, Any]:
        #     try:
        #         url = f"{OPENWEATHER_API_BASE_URL}/forecast"
        #         response = requests.get(
        #             url,
        #             params={
        #                 "q": city,
        #                 "units": "metric",
        #                 "appid": self.api_key
        #             }
        #         )
        #         response.raise_for_status()
        #         forecast_data = response.json()

        #         result = self._format_forecast(forecast_data, 3, "metric")

        #         return {
        #             "content": [
        #                 {
        #                     "type": "text",
        #                     "text": json.dumps(result, indent=2)
        #                 }
        #             ]
        #         }
        #     except requests.exceptions.RequestException as e:
        #         logger.error(f"Error fetching forecast data: {str(e)}")
        #         return {
        #             "content": [
        #                 {
        #                     "type": "text",
        #                     "text": f"Error fetching forecast data: {str(e)}"
        #                 }
        #             ]
        #         }

        @self.server.tool(name="get_weather_by_coordinates", description="Get weather for specific coordinates")
        async def handle_weather_by_coordinates(latitude: float, longitude: float) -> Dict[str, Any]:
            try: 
                url = f"{OPENWEATHER_API_BASE_URL}/weather"
                response = requests.get(
                    url,
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "units": "metric",
                        "appid": self.api_key
                    }
                )
                response.raise_for_status()
                weather_data = response.json()

                result = self._format_current_weather(weather_data, "metric")

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result
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

    def _format_current_weather(self, data: Dict[str, Any], units: str) -> str:
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        try:
            location_name = data.get("name", "Unknown")
            country = data.get("sys", {}).get("country", "Unknown")
            temp = data.get('main', {}).get('temp', 0)
            feels_like = data.get('main', {}).get('feels_like', 0)
            humidity = data.get('main', {}).get('humidity', 0)
            pressure = data.get('main', {}).get('pressure', 0)
            wind_speed = data.get('wind', {}).get('speed', 0)
            wind_deg = data.get('wind', {}).get('deg', 0)
            wind_direction = self._get_wind_direction(wind_deg)
            weather_main = data.get('weather', [{}])[0].get('main', "Unknown")
            weather_desc = data.get('weather', [{}])[0].get('description', "Unknown").capitalize()
            visibility = data.get('visibility', 0) / 1000
            cloudiness = data.get('clouds', {}).get('all', 0)

            # Build the main weather description
            weather_str = f"🌍 Weather Report for {location_name}, {country}\n\n"
            
            # Current conditions paragraph
            weather_str += f"Right now, it's {temp}{temp_unit} with {weather_desc.lower()}. "
            weather_str += f"The temperature feels like {feels_like}{temp_unit} due to the current conditions. "
            
            # Wind conditions
            if wind_speed > 0:
                weather_str += f"Winds are blowing from the {wind_direction} at {wind_speed} {speed_unit}. "
            else:
                weather_str += "The air is calm with minimal wind. "

            # Atmospheric conditions
            weather_str += f"\n\nThe atmosphere shows {humidity}% humidity"
            if cloudiness > 0:
                weather_str += f" with {cloudiness}% cloud cover"
            weather_str += f". Visibility extends to {visibility:.1f} kilometers"
            weather_str += f", and the barometric pressure reads {pressure} hPa."

            # Precipitation information if present
            precipitation_info = []
            if 'rain' in data:
                rain_1h = data['rain'].get('1h', 0)
                if rain_1h > 0:
                    precipitation_info.append(f"🌧️ {rain_1h}mm of rain has fallen in the last hour")

            if 'snow' in data:
                snow_1h = data['snow'].get('1h', 0)
                if snow_1h > 0:
                    precipitation_info.append(f"❄️ {snow_1h}mm of snow has accumulated in the last hour")

            if precipitation_info:
                weather_str += "\n\n" + ". ".join(precipitation_info) + "."

            # Add a summary recommendation based on conditions
            weather_str += "\n\n📝 Summary: "
            if weather_main.lower() in ["rain", "drizzle", "thunderstorm"]:
                weather_str += "Don't forget your umbrella!"
            elif weather_main.lower() == "snow":
                weather_str += "Bundle up and watch for snow conditions!"
            elif weather_main.lower() == "clear" and temp > 20:
                weather_str += "Great weather for outdoor activities!"
            elif weather_main.lower() == "clear" and temp < 10:
                weather_str += "Clear but chilly - dress warmly!"
            else:
                weather_str += f"Typical {weather_main.lower()} conditions for this area."

            return weather_str

        except (KeyError, IndexError) as e:
            logger.error(f"Error formatting current weather data: {str(e)}")
            return f"Error formatting weather data: {str(e)}"

    def _format_forecast(self, data: Dict[str, Any], days: int, units: str) -> str:
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        try:
            city_data = data.get("city", {})
            forecast_list = data.get("list", [])
            city_name = city_data.get("name", "Unknown")
            country = city_data.get("country", "Unknown")

            # Group forecasts by date
            daily_forecasts = {}
            for item in forecast_list:
                date = item.get("dt_txt", "").split(" ")[0]
                time = item.get("dt_txt", "").split(" ")[1]
                
                if date not in daily_forecasts:
                    daily_forecasts[date] = []
                
                daily_forecasts[date].append({
                    "time": time,
                    "temp": item.get('main', {}).get('temp', 0),
                    "feels_like": item.get('main', {}).get('feels_like', 0),
                    "min_temp": item.get('main', {}).get('temp_min', 0),
                    "max_temp": item.get('main', {}).get('temp_max', 0),
                    "humidity": item.get('main', {}).get('humidity', 0),
                    "weather_main": item.get('weather', [{}])[0].get('main', "Unknown"),
                    "weather_desc": item.get('weather', [{}])[0].get('description', "Unknown").capitalize(),
                    "wind_speed": item.get('wind', {}).get('speed', 0),
                    "wind_deg": item.get('wind', {}).get('deg', 0),
                    "cloudiness": item.get('clouds', {}).get('all', 0),
                    "rain": item.get('rain', {}).get('3h', 0) if 'rain' in item else 0,
                    "snow": item.get('snow', {}).get('3h', 0) if 'snow' in item else 0
                })

            # Get the dates we want to show
            forecast_dates = list(daily_forecasts.keys())[:days]
            
            # Start building the forecast string
            forecast_str = f"🗓️ {days}-Day Weather Forecast for {city_name}, {country}\n\n"

            for date in forecast_dates:
                forecasts = daily_forecasts[date]
                
                # Calculate daily statistics
                max_temp = max(f["temp"] for f in forecasts)
                min_temp = min(f["temp"] for f in forecasts)
                avg_humidity = sum(f["humidity"] for f in forecasts) / len(forecasts)
                total_rain = sum(f["rain"] for f in forecasts)
                total_snow = sum(f["snow"] for f in forecasts)
                
                # Get the most common weather condition
                weather_conditions = [f["weather_main"].lower() for f in forecasts]
                main_condition = max(set(weather_conditions), key=weather_conditions.count)
                
                # Format the date to be more readable
                formatted_date = date.split("-")
                formatted_date = f"{formatted_date[2]}/{formatted_date[1]}"  # DD/MM format
                
                # Build the daily forecast paragraph
                forecast_str += f"📅 {formatted_date}:\n"
                forecast_str += f"Expect {main_condition} conditions throughout the day. "
                forecast_str += f"Temperatures will range from {min_temp}{temp_unit} to {max_temp}{temp_unit}, "
                forecast_str += f"with humidity around {avg_humidity:.0f}%. "
                
                # Add precipitation information if present
                if total_rain > 0:
                    forecast_str += f"🌧️ Expected rainfall: {total_rain:.1f}mm. "
                if total_snow > 0:
                    forecast_str += f"❄️ Expected snowfall: {total_snow:.1f}mm. "
                
                # Add detailed timeline
                forecast_str += "\n\nHourly Timeline:\n"
                for forecast in forecasts:
                    time = forecast["time"].split(":")[0]  # Get just the hour
                    forecast_str += (f"  • {time}:00 - {forecast['temp']}{temp_unit}, "
                                   f"{forecast['weather_desc'].lower()}, "
                                   f"wind {forecast['wind_speed']} {speed_unit}\n")
                
                # Add recommendations based on conditions
                forecast_str += "\n💡 Day Summary: "
                if "rain" in main_condition or "drizzle" in main_condition:
                    forecast_str += "Pack an umbrella and waterproof clothing."
                elif "snow" in main_condition:
                    forecast_str += "Prepare for snowy conditions and dress warmly."
                elif "clear" in main_condition and max_temp > 20:
                    forecast_str += "Perfect weather for outdoor activities!"
                elif "clear" in main_condition and min_temp < 10:
                    forecast_str += "Clear but chilly - layer your clothing."
                else:
                    forecast_str += f"Typical {main_condition} conditions expected."
                
                forecast_str += "\n\n" + "-"*50 + "\n\n"
            
            return forecast_str

        except (KeyError, IndexError) as e:
            logger.error(f"Error formatting weather forecast data: {str(e)}")
            return f"Error formatting forecast data: {str(e)}"

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