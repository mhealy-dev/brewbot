import os
import json
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'DISCORD: {TOKEN}\nWEATHER: {WEATHER_API_KEY}')
    print("Hello, I'm ready to tell you the weather!")


@bot.command()
async def weather(ctx, *args):
    # Join the arguments into a single string with spaces between them
    location = ' '.join(args)
    # Make a request to the OpenWeatherMap API to get the current weather data
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&units=imperial&appid={WEATHER_API_KEY}'
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Extract the relevant weather data
        temperature = data['main']['temp']
        high = data['main']['temp_max']
        low = data['main']['temp_min']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        icon = data['weather'][0]['icon']
        icon_url = f"http://openweathermap.org/img/w/{icon}.png"
        # Create an embed to display the weather data
        embed = discord.Embed(
            title=f"Current weather in {location.title()}", color=0x9370D0)
        embed.set_thumbnail(url=icon_url)
        embed.add_field(name="**Temperature**",
                        value=f"{temperature}°F", inline=False)
        embed.add_field(
            name="**High**", value=f"{high}°F", inline=True)
        embed.add_field(
            name="**Low**", value=f"{low}°F", inline=True)
        embed.add_field(name="**Description**",
                        value=description.title(), inline=False)
        embed.add_field(name="**Humidity**",
                        value=f"{humidity}%", inline=False)
        embed.add_field(name="**Wind Speed**",
                        value=f"{wind_speed} m/s", inline=False)
        # Send the embed back to the user
        await ctx.send(embed=embed)
    else:
        message = "Unable to retrieve weather data for the specified location."
        await ctx.send(message)


@bot.command()
async def forecast(ctx, *args):
    # Join the arguments into a single string with spaces between them
    location = ' '.join(args)
    # Make a request to the OpenWeatherMap API to get the current weather data
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={location}&units=imperial&appid={WEATHER_API_KEY}'
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        api_data_filepath = os.path.join(os.path.dirname(__file__), 'forecast.json')
        with open(api_data_filepath, 'w') as fp:
            json.dump(data, fp, indent=4)
        # Extract the relevant forecast data
        forecasts = []
        for forecast in data['list']:
            date_time = forecast['dt_txt']
            date = datetime.strptime(date_time.split(' ')[0], '%Y-%m-%d')
            if date > datetime.now() + timedelta(days=4):
                break
            date = date.strftime('%b %d, %Y')
            time = date_time.split(' ')[1]
            temperature = round(forecast['main']['temp'], 1)
            weather_description = forecast['weather'][0]['description']
            icon = forecast['weather'][0]['icon']
            forecasts.append({'date': date, 'time': time, 'temperature': temperature,
                             'weather_description': weather_description, 'icon': icon})

        # Group the forecasts by date and calculate the daily high and low temperatures
        daily_forecasts = {}
        for forecast in forecasts:
            date = forecast['date']
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    'high': None, 'low': None, 'forecasts': []}
            temperature = forecast['temperature']
            if daily_forecasts[date]['high'] is None or temperature > daily_forecasts[date]['high']:
                daily_forecasts[date]['high'] = temperature
            if daily_forecasts[date]['low'] is None or temperature < daily_forecasts[date]['low']:
                daily_forecasts[date]['low'] = temperature
            daily_forecasts[date]['forecasts'].append(forecast)

        # Create an embed for all 5 days' forecasts
        embed = discord.Embed(
            title=f"Weekly forecast for {location.title()}", color=0x9370D0)
        for date, forecast_data in daily_forecasts.items():
            high = forecast_data['high']
            low = forecast_data['low']
            weather_description = forecast_data['forecasts'][0]['weather_description']
            icon_url = f"http://openweathermap.org/img/w/{forecast_data['forecasts'][0]['icon']}.png"
            embed.add_field(
                name=date, value=f"**High:** {high}°F\n**Low:** {low}°F\n**Weather:** {weather_description.title()}", inline=True)
            embed.set_thumbnail(url=icon_url)

        # Send the embed back to the user
        debug_file = discord.File(api_data_filepath, 'forecast.json')
        await ctx.send(embed=embed, file=debug_file)
    else:
        message = "Unable to retrieve weather forecast data for the specified location."
        await ctx.send(message)
bot.run(TOKEN)
