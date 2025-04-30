# MCP Weather SSE Server

A Model Context Protocol (MCP) server that connects to the OpenWeatherMap API through Server-Sent Events (SSE). This server provides real-time weather data to AI clients like Claude, CursorAI, or MCP-Inspector.

## Features

- Implements the Model Context Protocol for seamless integration with AI tools
- Uses Server-Sent Events (SSE) transport for real-time communication
- Connects to the OpenWeatherMap API to fetch live weather data
- Provides three tools:
  - `get_current_weather`: Get current weather conditions for a city
  - `get_weather_forecast`: Get a multi-day weather forecast for a city
  - `get_weather_by_coordinates`: Get weather for specific geographic coordinates

## Prerequisites

- Python 3.8+
- An OpenWeatherMap API key (sign up at [openweathermap.org](https://openweathermap.org/))

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/mcp-weather-sse.git
   cd mcp-weather-sse
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install mcp requests
   ```

## Usage

### Starting the Server

You can start the server with your OpenWeatherMap API key:

```bash
# Using command line argument
python mcp_weather_sse.py --api-key YOUR_API_KEY

# Customize host and port (default: 127.0.0.1:3001)
python mcp-weather-sse.py --host 0.0.0.0 --port 8080 --api-key YOUR_API_KEY
```

### Connecting with MCP Clients

#### Cursor AI

1. Open Cursor AI
2. Go to File → Preferences → Cursor Settings → MCP → Add New Server
3. Enter the following details:
   - Name: Weather SSE
   - Type: sse
   - URL: http://127.0.0.1:3001/sse

#### Claude Desktop

1. Open Claude Desktop
2. Go to Settings → MCP Servers
3. Add a new server with the following configuration:
   ```json
   {
     "mcpServers": {
       "weather": {
         "type": "sse",
         "url": "http://127.0.0.1:3001/sse"
       }
     }
   }
   ```

#### MCP-Inspector

You can use the MCP-Inspector tool to test your server:

```bash
npm install -g @anthropic-ai/mcp-inspector
mcp-inspector http://127.0.0.1:3001/sse
```

## Example Queries

Once connected, you can use the following queries to interact with the server:

1. "What's the current weather in New York?"
2. "Can you give me a 3-day forecast for Tokyo?"
3. "What's the weather at coordinates 40.7128, -74.0060?"

## API Reference

### `get_current_weather`

Get current weather conditions for a city.

Parameters:
- `city` (string): City name (e.g., 'London', 'New York')
- `units` (string, optional): Units of measurement ('metric' or 'imperial', default: 'metric')

### `get_weather_forecast`

Get a multi-day weather forecast for a city.

Parameters:
- `city` (string): City name (e.g., 'London', 'New York')
- `days` (integer, optional): Number of days to forecast (1-5, default: 3)
- `units` (string, optional): Units of measurement ('metric' or 'imperial', default: 'metric')

### `get_weather_by_coordinates`

Get weather for specific geographic coordinates.

Parameters:
- `latitude` (number): Latitude coordinate
- `longitude` (number): Longitude coordinate
- `units` (string, optional): Units of measurement ('metric' or 'imperial', default: 'metric')

## Security Considerations

- The server binds to 127.0.0.1 by default, making it only accessible from your local machine
- For production use, implement proper authentication and HTTPS
- Consider rate limiting to avoid exceeding OpenWeatherMap API quotas

## License

MIT

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses data from the [OpenWeatherMap API](https://openweathermap.org/api)
