import os
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
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
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        # Create an embed to display the weather data
        embed = discord.Embed(
            title=f"Current weather in {location}", color=0x00f2)
        embed.add_field(name="Temperature",
                        value=f"{temperature} degrees Fahrenheit", inline=False)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Humidity", value=f"{humidity}%", inline=False)
        embed.add_field(name="Wind Speed",
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
        # Extract the relevant forecast data
        forecasts = []
        for forecast in data['list']:
            date_time = forecast['dt_txt']
            date = datetime.strptime(date_time.split(
                ' ')[0], '%Y-%m-%d').strftime('%m-%d-%Y')
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

        # Create an embed for each day's forecast
        for date, forecast_data in daily_forecasts.items():
            high = forecast_data['high']
            low = forecast_data['low']
            forecasts = forecast_data['forecasts']
            embed = discord.Embed(title=f"Forecast for {date}", color=0x00f2)
            # for forecast in forecasts:
            #     time = forecast['time']
            #     temperature = forecast['temperature']
            #     weather_description = forecast['weather_description']
            #     icon_url = f"http://openweathermap.org/img/w/{forecast['icon']}.png"
            #     embed.add_field(
            #         name=f"{time}", value=f"{temperature}°F {weather_description}", inline=True)
            #     embed.set_thumbnail(url=icon_url)
            weather_description = forecast['weather_description']
            icon_url = f"http://openweathermap.org/img/w/{forecast['icon']}.png"
            embed.add_field(name="High", value=f"{high}°F", inline=True)
            embed.add_field(name="Low", value=f"{low}°F", inline=True)
            embed.set_thumbnail(url=icon_url)
            await ctx.send(embed=embed)
    else:
        message = "Unable to retrieve weather forecast data for the specified location."
        await ctx.send(message)

bot.run(TOKEN)
