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
        # Extract the relevant forecast data
        forecasts = []
        for forecast in data['list']:
            date_time = forecast['dt_txt']
            date = datetime.strptime(date_time.split(' ')[0], '%Y-%m-%d')
            if date.day == datetime.now().day:
                continue
            date = date.strftime('%b %d, %Y')
            time = date_time.split(' ')[1]
            temperature = round(forecast['main']['temp'], 1)
            weather_description = forecast['weather'][0]['description']
            icon = forecast['weather'][0]['icon']
            forecasts.append({'date': date, 'time': time, 'temperature': temperature,
                             'weather_description': weather_description, 'icon': icon})
        if not forecasts:
            await ctx.send(f"Unable to retrieve weather forecast data for this {location.title()} the next 5 days.")
            return
        # Group the forecasts by date and calculate the daily high and low temperatures
        daily_forecasts = []
        dates_in_forecast = []
        for forecast in forecasts:
            new_day = {}
            date = forecast.get('date', None)
            previous_index = None
            if date not in daily_forecasts:
                new_day = {
                    'high': None, 'low': None, 'forecasts': []}
            else:
                for i, x in enumerate(daily_forecasts):
                    if x['date'] == date:
                        new_day = x
                        previous_index = i
                        break
            temperature = forecast['temperature']
            if new_day['high'] is None or temperature > new_day['high']:
                new_day['high'] = temperature
            if new_day['low'] is None or temperature < new_day['low']:
                new_day['low'] = temperature
            new_day['date'] = date
            new_day['forecasts'].append(forecast)
            if not previous_index:
                daily_forecasts.append(new_day)
                dates_in_forecast.append(date)
            else:
                daily_forecasts[previous_index] = new_day

        # Create an embed for all 5 days' forecasts
        # embed = discord.Embed(
        #     title=f"5 day forecast for {location.title()}", color=0x9370D0)
        # for date, forecast_data in daily_forecasts.items():
        #     high = forecast_data['high']
        #     low = forecast_data['low']
        #     weather_description = forecast_data['forecasts'][0]['weather_description']
        #     icon_url = f"http://openweathermap.org/img/w/{forecast_data['forecasts'][0]['icon']}.png"
        #     embed.add_field(
        #         name=date, value=f"**High:** {high}°F\n**Low:** {low}°F\n**Weather:** {weather_description.title()}", inline=True)
        #     embed.set_thumbnail(url=icon_url)

        # Create the embeds for each day's forecasts
        embeds = []
        for forecast_data in daily_forecasts:
            high = forecast_data['high']
            low = forecast_data['low']
            weather_description = forecast_data['forecasts'][0]['weather_description']
            icon_url = f"http://openweathermap.org/img/w/{forecast_data['forecasts'][0]['icon']}.png"

            # Create an embed for the day's forecast
            embed = discord.Embed(
                title=f"Forecast for {location.title()} on {forecast_data['date']}", color=0x9370D0)
            embed.add_field(
                name="High Temperature", value=f"{high}°F", inline=True)
            embed.add_field(
                name="Low Temperature", value=f"{low}°F", inline=True)
            embed.add_field(
                name="Weather Description", value=weather_description.title(), inline=False)
            embed.set_thumbnail(url=icon_url)

            # Add the embed to the list of embeds
            embeds.append(embed)

        # Include API data in JSON file if env.DEBUG_MODE == 'True'
        debug_file = debug_api_data(data)

        # Send the embed back to the user
        if len(embeds) > 1:
            await send_forecasts(ctx, daily_forecasts)
        else:
            await ctx.send(embed=embed, file=debug_file)
    else:
        message = "Unable to retrieve weather forecast data for the specified location."
        await ctx.send(message)


async def send_forecasts(ctx, forecasts):
    pages = []
    page = []
    for forecast in forecasts:
        # Create a string representation of the forecast
        forecast_str = f"**High:** {forecast['high']}°F\n**Low:** {forecast['low']}°F\n**Weather:** {forecast.get('weather_description', '')}"
        page.append(f"**{forecast['date']}**\n{forecast_str}")

        # If we've accumulated 10 lines, start a new page
        if len(page) == 10:
            pages.append(page)
            page = []

    # If we have any leftover lines, add them to the last page
    if page:
        pages.append(page)

    # Define the message components
    class ForecastPaginator(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.index = 0
            self.message = None

        async def edit_message(self):
            # Edit the message with the current page's content
            if self.message:
                await self.message.edit(content='\n'.join(pages[self.index]))

        @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
        async def prev_page(self, button: discord.ui.Button, interaction: discord.Interaction):
            # Go to the previous page, if possible
            if self.index > 0:
                self.index -= 1
                await self.edit_message()

        @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
        async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
            # Go to the next page, if possible
            if self.index < len(pages) - 1:
                self.index += 1
                await self.edit_message()

        @discord.ui.button(label='Stop', style=discord.ButtonStyle.danger)
        async def stop_pagination(self, button: discord.ui.Button, interaction: discord.Interaction):
            # Stop the pagination
            self.stop()

    # Send the first page of the message with the paginator
    view = ForecastPaginator()
    await view.edit_message()
    view.message = await ctx.send('\n'.join(pages[0]), view=view)

    # Wait for the paginator to stop
    await view.wait()


bot.run(TOKEN)
