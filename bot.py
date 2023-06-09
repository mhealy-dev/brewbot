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
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


def debug_api_data(data):
    if DEBUG_MODE != 'True':
        return None
    api_data_filepath = os.path.join(os.path.dirname(
        __file__), 'sample-data', 'forecast.json')
    with open(api_data_filepath, 'w') as fp:
        json.dump(data, fp, indent=4)
    return discord.File(api_data_filepath, 'forecast.json')


@bot.event
async def on_ready():
    print("Hello, I'm ready to tell you the weather!")

# Current day weather command


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
        temperature = int(data['main']['temp'])
        high = int(data['main']['temp_max'])
        low = int(data['main']['temp_min'])
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = int(data['wind']['speed'])
        icon = data['weather'][0]['icon']
        icon_url = f"http://openweathermap.org/img/w/{icon}.png"
        # Create an embed to display the weather data
        embed = discord.Embed(
            title=f"Current weather in {location.title()}", color=0x9370D0)
        embed.set_thumbnail(url=icon_url)
        embed.add_field(name="**Current Temperature**",
                        value=f"{temperature}°F", inline=False)
        embed.add_field(
            name="**High**", value=f"{high}°F", inline=True)
        embed.add_field(
            name="**Low**", value=f"{low}°F", inline=True)
        embed.add_field(name="**Description**",
                        value=description.title(), inline=True)
        embed.add_field(name="**Humidity**",
                        value=f"{humidity}%", inline=True)
        embed.add_field(name="**Wind Speed**",
                        value=f"{wind_speed} m/s", inline=True)
        # Send the embed back to the user
        await ctx.send(embed=embed)
    else:
        message = "Unable to retrieve weather data for the specified location."
        await ctx.send(message)


# 5 day forecast command
@bot.command(name='fc')
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
            date = datetime.strptime(date_time.split(' ')[0], '%Y-%m-%d')
            if date.day == datetime.now().day:
                continue
            date = date.strftime('%b %d, %Y')
            time = date_time.split(' ')[1]
            temperature = int(forecast['main']['temp'])
            humidity = forecast['main']['humidity']
            weather_description = forecast['weather'][0]['description']
            icon = forecast['weather'][0]['icon']
            # Check if this forecast is for a new day
            if len(forecasts) == 0 or date != forecasts[-1]['date']:
                daily_forecast = {
                    'date': date,
                    'high': temperature,
                    'low': temperature,
                    'humidity': humidity,
                    'weather_description': weather_description,
                    'icon': icon
                }
                forecasts.append(daily_forecast)
            else:
                daily_forecast = forecasts[-1]
                if temperature > daily_forecast['high']:
                    daily_forecast['high'] = temperature
                if temperature < daily_forecast['low']:
                    daily_forecast['low'] = temperature
        if not forecasts:
            await ctx.send(f"Unable to retrieve weather forecast data for this {location.title()} the next 5 days.")
            return
        # Create an embed for each day's forecast
        embeds = []
        for forecast_data in forecasts:
            high = int(forecast_data['high'])
            low = int(forecast_data['low'])
            weather_description = forecast_data['weather_description']
            humidity = forecast_data['humidity']
            icon_url = f"http://openweathermap.org/img/w/{forecast_data['icon']}.png"
            # Create an embed for the day's forecast
            embed = discord.Embed(
                title=f"Forecast for {location.title()} on {forecast_data['date']}", color=0x9370D0)
            embed.add_field(
                name="**High**", value=f"{high}°F", inline=True)
            embed.add_field(
                name="**Low**", value=f"{low}°F", inline=True)
            embed.add_field(
                name="**Humidity**", value=f"{humidity}%", inline=True)
            embed.add_field(
                name="**Description**", value=weather_description.title(), inline=False)
            embed.set_thumbnail(url=icon_url)
            # Add the embed to the list of embeds
            embeds.append(embed)
        # Send the embed(s) back to the user
        if len(embeds) > 1:
            await send_forecasts(ctx, embeds)
        else:
            await ctx.send(embed=embeds[0])
    else:
        message = "Unable to retrieve weather forecast data for the specified location."
        await ctx.send(message)


async def send_forecasts(ctx, forecasts):
    pages = [embed for embed in forecasts]

    # Define the message components
    class ForecastPaginator(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.index = 0
            self.pages = pages
            self.message = None
            self.prev_button = discord.ui.Button(
                label='Previous', custom_id='prev', style=discord.ButtonStyle.primary)
            self.prev_button.callback = self.prev_page
            self.next_button = discord.ui.Button(
                label='Next', custom_id='next', style=discord.ButtonStyle.primary)
            self.next_button.callback = self.next_page
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
            

        def check_buttons(self):
            self.prev_button.disabled = self.index == 0
            self.next_button.disabled = self.index == len(self.pages) - 1

        async def prev_page(self, interaction: discord.Interaction):
            if self.index > 0:
                self.index -= 1
            self.check_buttons()
            await interaction.response.edit_message(view=self, embed=pages[self.index])

        async def next_page(self, interaction: discord.Interaction):
            # Go to the next page, if possible
            if self.index < len(self.pages) - 1:
                self.index += 1
            self.check_buttons()
            await interaction.response.edit_message(view=self, embed=pages[self.index])

        @ discord.ui.button(label='Stop', style=discord.ButtonStyle.danger)
        async def stop_pagination(self, interaction: discord.Interaction, button: discord.ui.button):
            # Stop the pagination
            await interaction.response.edit_message(view=None)
            self.stop()

    # Send the first page of the message with the paginator
    view = ForecastPaginator()
    view.check_buttons()
    view.message = await ctx.send(embed=pages[0], view=view)

    # Wait for the paginator to stop
    await view.wait()


bot.run(TOKEN)
