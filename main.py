import os
import requests
from datetime import date

import interactions
from interactions import SlashContext, slash_command, OptionType, slash_option, SlashCommandChoice, Embed

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# Seasons
WINTER = 'winter'
SPRING = 'spring'
SUMMER = 'summer'
FALL = 'fall'

# Emoji
SEASON_EMOJI = {
    WINTER: "🏂",
    SPRING: "🌷",
    SUMMER: "🌞",
    FALL: "🍂"
}

# Regions
NORTH_EAST = "Northeast"
MIDWEST = "Midwest"
SOUTH = "South"
WEST = "West"
PACIFIC_NORTHWEST = "Pacific Northwest"
SOUTH_WEST = "Southwest"
    
# Temperature Ranges
TEMP_RANGES = {
    WINTER: {
        NORTH_EAST: (10, 40),
        MIDWEST: (-10, 40),
        SOUTH: (40, 70),
        WEST: (20, 40),
        PACIFIC_NORTHWEST: (40, 50),
        SOUTH_WEST: (50, 70)
    },
    SPRING: {
        NORTH_EAST: (40, 70),
        MIDWEST: (40, 70),
        SOUTH: (60, 80),
        WEST: (50, 75),
        PACIFIC_NORTHWEST: (50, 70),
        SOUTH_WEST: (60, 80)
    },
    SUMMER: {
        NORTH_EAST: (70, 100),
        MIDWEST: (70, 100),
        SOUTH: (80, 100),
        WEST: (75, 95),
        PACIFIC_NORTHWEST: (60, 85),
        SOUTH_WEST: (90, 120)
    },
    FALL: {
        NORTH_EAST: (50, 70),
        MIDWEST: (50, 70),
        SOUTH: (60, 80),
        WEST: (50, 80),
        PACIFIC_NORTHWEST: (50, 70),
        SOUTH_WEST: (70, 95)
    }
}

# Define cities with latitude and longitude representing different regions in the U.S.
REGIONS = {
    NORTH_EAST: [
        {"city": "New York", "lat": 40.7128, "lon": -74.0060},
        {"city": "Boston", "lat": 42.3601, "lon": -71.0589},
        {"city": "Philadelphia", "lat": 39.9526, "lon": -75.1652}
    ],
    MIDWEST: [
        {"city": "Chicago", "lat": 41.8781, "lon": -87.6298},
        {"city": "Detroit", "lat": 42.3314, "lon": -83.0458},
        {"city": "Minneapolis", "lat": 44.9778, "lon": -93.2650}
    ],
    SOUTH: [
        {"city": "Miami", "lat": 25.7617, "lon": -80.1918},
        {"city": "Atlanta", "lat": 33.7490, "lon": -84.3880},
        {"city": "Dallas", "lat": 32.7767, "lon": -96.7970}
    ],
    WEST: [
        {"city": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
        {"city": "Denver", "lat": 39.7392, "lon": -104.9903},
        {"city": "Salt Lake City", "lat": 40.7609, "lon": -111.8910}
    ],
    PACIFIC_NORTHWEST: [
        {"city": "Portland", "lat": 45.5051, "lon": -122.6750},
        {"city": "Seattle", "lat": 47.6062, "lon": -122.3321}
    ],
    SOUTH_WEST: [
        {"city": "Phoenix", "lat": 33.4484, "lon": -112.0740},
        {"city": "Las Vegas", "lat": 36.1699, "lon": -115.1398}
    ]
}

def get_meteorological_season(month):
    if month in [12, 1, 2]:
        return WINTER
    elif month in [3, 4, 5]:
        return SPRING
    elif month in [6, 7, 8]:
        return SUMMER
    elif month in [9, 10, 11]:
        return FALL
    else:
        return "Unknown"

def is_temperature_within_range(season, region, temperature):
    if season in TEMP_RANGES:
        min_temp, max_temp = TEMP_RANGES[season][region]
        return min_temp <= temperature <= max_temp
    return False

def get_current_temperature(lat, lon):
    """Fetch the current temperature from NWS API."""
    # NWS API endpoint for the weather station based on lat/lon
    url = f"https://api.weather.gov/points/{lat},{lon}"
    
    try:
        response = requests.get(url)
        initial_data = response.json()

        forecast_url = initial_data['properties']['forecast']
        forecast_response = requests.get(forecast_url)
        data = forecast_response.json()
        
        for period in data['properties']['periods']:
            if period['isDaytime']:  # Assuming we're interested in daytime temperature
                return period['temperature']
        print("No daytime temperature found.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data for lat: {lat}, lon: {lon}.")
        print(e)
        return None

def check_weather_for_all_regions(season):
    region_status = {}

    # Check temperatures for each city in each region
    for region, cities in REGIONS.items():
        region_temp_status = []
        
        for city_data in cities:
            city, lat, lon = city_data['city'], city_data['lat'], city_data['lon']
            temp = get_current_temperature(lat, lon)
            if temp is not None:
                region_temp_status.append((city, temp, is_temperature_within_range(season, region, temp)))
        
        # Record the region's status
        region_status[region] = region_temp_status
    
    return region_status


def build_embed(cur_season, region_weather_status):
    match = 0
    total = 0
    
    embed = Embed(
      title="Weather Results",
      description=f"Weather comparison for the {cur_season} season across the U.S.",
      color=0x0000FF,
      )
    
    for region, statuses in region_weather_status.items():
        embed.add_field(name=region, value=" ")
        
        for city, temp, status in statuses:
            total += 1
            match += status
            embed.add_field(name=" ", value=f"{city}: {temp}°F - {'✅' if status else '❌'}")
    match_rate = match / total * 100
    embed.add_field(name="Result", value=f"{match_rate}%")
    
    return embed, match / total


@slash_command(name="season-wtf",
               description="Update channel name to current season")
@slash_option(
    name="season",
    description="the season for which you want to set the channel name",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name=SPRING, value=SPRING),
        SlashCommandChoice(name=SUMMER, value=SUMMER),
        SlashCommandChoice(name=FALL, value=FALL),
        SlashCommandChoice(name=WINTER, value=WINTER)
    ]
)
async def season_wtf(ctx: SlashContext, season: str):
  await ctx.defer()
  user_mention = ctx.user.mention

  current_season = get_meteorological_season(date.today().month)
  
  if season != current_season:
      await ctx.send("Sorry, but that's obviously wrong. Maybe try a different season?")
      return

  region_weather_status = check_weather_for_all_regions(current_season)
  
  embed, match_rate = build_embed(current_season, region_weather_status)
  await ctx.send(embeds=[embed])
  
  if (match_rate > 0.5):
    new_name = f"{SEASON_EMOJI[current_season]}{current_season}-{date.today().year}-wtf"
    await ctx.channel.edit(name=new_name)
    await ctx.send('Thanks {}! The new channel name is \"{}\"'.format(user_mention, new_name))
  else:
    failure_message = f"I'm sorry, but more than half of the sampled US cities are not experiencing {current_season}-like temperatures right now. Perhaps the season will shift tomorrow?"
    await ctx.send(failure_message)    

bot = interactions.Client(token=DISCORD_BOT_TOKEN,
                          intents=interactions.Intents.MESSAGES)
bot.start()
