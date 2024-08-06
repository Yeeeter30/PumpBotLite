import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import datetime

load_dotenv()

bot_token = os.getenv("token")

API_KEY = os.getenv("apikey")

# Initialize bot with dynamic prefix
bot = commands.Bot(command_prefix='?', intents=discord.Intents.all())

start_time = datetime.datetime.now()

@bot.event
async def on_ready():
    # Set the bot's status to "Playing" with a custom message
    await bot.change_presence(activity=discord.Game(name="PumpBot Lite Coded By Async.Flux"))
    print(f'Bot is ready. Logged in as {bot.user}')
        
@bot.slash_command(name="getcosmetic", description="Get details of a Fortnite item by searching from a list.")
async def getcosmetic(ctx: discord.ApplicationContext, search: str):
    list_url = "https://fortniteapi.io/v2/items/list?lang=en"
    headers = {
        "Authorization": API_KEY
    }

    try:
        await ctx.defer()  # Acknowledge the interaction

        # Get the list of items
        list_response = requests.get(list_url, headers=headers)
        list_response.raise_for_status()
        list_data = list_response.json()
        items = list_data.get('items', [])

        # Search for the item in the list
        item_data = next((item for item in items if item['id'].lower() == search.lower() or item['name'].lower() == search.lower()), None)

        if item_data:
            # Get details for the matched item
            item_id = item_data['id']
            detail_url = f"https://fortniteapi.io/v2/items/get?id={item_id}&lang=en"
            detail_response = requests.get(detail_url, headers=headers)
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            item_details = detail_data.get('item', {})

            name = item_details.get('name', 'Unknown')
            description = item_details.get('description', 'No description')

            # Create and send the embed
            embed = discord.Embed(title=name, description=description, color=discord.Color.green())
            await ctx.followup.send(embed=embed)  # Send the follow-up message
        else:
            # Send an embed if no item is found
            embed = discord.Embed(title="Item Not Found", description=f"No item found matching: {search}", color=discord.Color.red())
            await ctx.followup.send(embed=embed)
    except requests.exceptions.HTTPError as http_err:
        await ctx.followup.send(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        await ctx.followup.send(f"Error occurred: {req_err}")
    except Exception as err:
        await ctx.followup.send(f"An unexpected error occurred: {err}")

@getcosmetic.error
async def getcosmetic_error(ctx: discord.ApplicationContext, error: Exception):
    if isinstance(error, discord.errors.NotFound):
        await ctx.respond("Error: Command not found. Please try again.")
    elif isinstance(error, discord.errors.ApplicationCommandInvokeError):
        await ctx.respond("Error: There was a problem invoking the command.")
    else:
        await ctx.respond(f"An unexpected error occurred: {error}")
    
@bot.slash_command(name="map", description="Get the current Fortnite map with and without POIs")
async def map(ctx):
    # URLs for the maps
    blank_image_url = "https://media.fortniteapi.io/images/map.png"
    pois_image_url = "https://media.fortniteapi.io/images/map.png?showPOI=true"

    # Create an embed with two images
    embed = discord.Embed(title="Fortnite Map", description="Here are the latest maps:", color=discord.Color.blue())

    # Add map without POIs
    embed.add_field(name="MAP NO POIS", value="Map without Points of Interest", inline=False)
    embed.set_image(url=blank_image_url)

    # Add map with POIs
    embed.add_field(name="MAP POIS", value="Map with Points of Interest", inline=False)
    embed.add_field(name="\u200b", value=f"[View POI Map]({pois_image_url})", inline=False)

    await ctx.respond(embed=embed)

@bot.slash_command(name="shop", description="Shows shop items with pagination.")
async def shop(
    ctx: discord.ApplicationContext,
    page: discord.Option(int, "Select a page", default=1)
):
    url = 'https://fortniteapi.io/v2/shop?lang=en'
    headers = {'Authorization': API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        await ctx.respond(f"Failed to fetch data. Status code: {response.status_code}")
        return

    data = response.json()
    shop_items = data.get('shop', [])

    items_per_page = 10  # Number of items per page
    total_pages = (len(shop_items) + items_per_page - 1) // items_per_page

    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page number. Please enter a number between 1 and {total_pages}.")
        return

    start_index = (page - 1) * items_per_page
    end_index = min(start_index + items_per_page, len(shop_items))
    items_to_display = shop_items[start_index:end_index]

    embed = discord.Embed(title="Fortnite Shop Items", description=f"Page {page} of {total_pages}")
    for item in items_to_display:
        embed.add_field(
            name=item.get('displayName', 'No name'),
            value=f"**Description:** {item.get('displayDescription', 'No description')}\n"
                  f"**Price:** {item.get('price', {}).get('finalPrice', 'N/A')}\n"
                  f"**Rarity:** {item.get('rarity', {}).get('name', 'N/A')}",
            inline=False
        )

    await ctx.respond(embed=embed)
        
@bot.slash_command(name="code", description="Searches for a code")
async def code(ctx: discord.ApplicationContext, code: str):
    url = f'https://fortniteapi.io/v1/creator?code={code}'
    headers = {'Authorization': API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an error for HTTP codes 4xx/5xx
        data = response.json()

        if data.get('response') and data.get('code'):
            code_data = data['code']
            embed = discord.Embed(title="Code Information", color=discord.Color.blue())
            embed.add_field(name="ID", value=code_data.get('id', 'N/A'))
            embed.add_field(name="Slug", value=code_data.get('slug', 'N/A'))
            embed.add_field(name="Display Name", value=code_data.get('displayName', 'N/A'))
            embed.add_field(name="Status", value=code_data.get('status', 'N/A'))
            embed.add_field(name="Verified", value="Yes" if code_data.get('verified', False) else "No")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("No data found for the given code.")
    except requests.exceptions.HTTPError as http_err:
        await ctx.respond(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        await ctx.respond(f"Error occurred: {req_err}")
    except Exception as err:
        await ctx.respond(f"An unexpected error occurred: {err}")


@bot.slash_command(name='uptime', description='Displays the bot\'s uptime.')
async def uptime(ctx: discord.ApplicationContext):
    current_time = datetime.datetime.now()
    uptime_duration = current_time - start_time
    
    days = uptime_duration.days
    hours, remainder = divmod(uptime_duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    embed = discord.Embed(
        title="Bot Uptime",
        description=(f"**Uptime:**\n"
                     f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"),
        color=discord.Color.green()
    )
    
    await ctx.respond(embed=embed)       
 
@bot.slash_command(name="creative", description="Get details of a specific Fortnite Creative island by code.")
async def creative(ctx: discord.ApplicationContext, code: str):
    url = f"https://fortniteapi.io/v1/creative/island?code={code}"
    headers = {
        'Authorization': API_KEY
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("result"):
        island = data.get("island", {})
        embed = discord.Embed(title="Fortnite Creative Island Information", color=discord.Color.blue())
        embed.add_field(name="Title", value=island.get("title", "No Title"), inline=False)
        embed.add_field(name="Description", value=island.get("description", "No Description"), inline=False)
        embed.add_field(name="Introduction", value=island.get("introduction", "No Introduction"), inline=False)
        embed.add_field(name="Creator", value=island.get("creator", "Unknown Creator"), inline=False)
        embed.add_field(name="Published Date", value=island.get("publishedDate", "No Date"), inline=False)
        embed.add_field(name="Code", value=island.get("code", "No Code"), inline=False)
        embed.set_thumbnail(url=island.get("image", "https://via.placeholder.com/150"))

        await ctx.respond(embed=embed)
    else:
        await ctx.respond("Failed to retrieve data. Please check the code and try again.") 
 
@bot.slash_command(name="getitem", description="Fetch and display weapon details by ID or Name.")
async def getitem(ctx: discord.ApplicationContext, search: str):
    url = "https://fortniteapi.io/v1/loot/list?lang=en"
    headers = {
        'Authorization': API_KEY
    }
    
    try:
        await ctx.defer()  # Acknowledge the interaction

        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Try to find the weapon matching the provided search term as ID or Name
        weapon = next((item for item in data.get('weapons', []) 
                       if item['id'] == search or item['name'].lower() == search.lower()), None)

        if weapon:
            # Create an embed with weapon details
            embed = discord.Embed(
                title=weapon['name'],
                description=weapon['description'],
                color=discord.Color.blue()
            )
            embed.add_field(name="Rarity", value=weapon['rarity'].capitalize(), inline=True)
            embed.add_field(name="Type", value=weapon['type'].capitalize(), inline=True)
            embed.add_field(name="Damage per Bullet", value=weapon['mainStats']['DmgPB'], inline=True)
            embed.add_field(name="Firing Rate", value=weapon['mainStats']['FiringRate'], inline=True)
            embed.add_field(name="Clip Size", value=weapon['mainStats']['ClipSize'], inline=True)
            embed.add_field(name="Reload Time", value=weapon['mainStats']['ReloadTime'], inline=True)
            
            await ctx.followup.send(embed=embed)  # Send the follow-up message
        else:
            embed = discord.Embed(title="Weapon Not Found", description=f"No weapon found with ID or Name: {search}", color=discord.Color.red())
            await ctx.followup.send(embed=embed)
    except requests.exceptions.HTTPError as http_err:
        await ctx.followup.send(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        await ctx.followup.send(f"Error occurred: {req_err}")
    except Exception as err:
        await ctx.followup.send(f"An unexpected error occurred: {err}")

@getitem.error
async def getitem_error(ctx: discord.ApplicationContext, error: Exception):
    if isinstance(error, discord.errors.NotFound):
        await ctx.respond("Error: Command not found. Please try again.")
    elif isinstance(error, discord.errors.ApplicationCommandInvokeError):
        await ctx.respond("Error: There was a problem invoking the command.")
    else:
        await ctx.respond(f"An unexpected error occurred: {error}")
        
@bot.slash_command(name="upcoming", description="Get upcoming Fortnite items.")
async def upcoming(ctx: discord.ApplicationContext, page: int = 1):
    url = "https://fortniteapi.io/v2/items/upcoming?lang=en"
    headers = {
        'Authorization': API_KEY
    }
    
    # Make the request
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        
        # Pagination logic
        items_per_page = 10
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_items = items[start_index:end_index]
        
        if not page_items:
            await ctx.respond(f"No items found for page {page}.")
            return
        
        # Create an embed for each item
        embed = discord.Embed(title=f"Upcoming Fortnite Items - Page {page}", color=discord.Color.blue())
        
        for item in page_items:
            item_name = item['name']
            item_id = item['id']
            item_description = item.get('description', 'No description available')
            
            embed.add_field(
                name=item_name,
                value=(
                    f"**ID:** {item_id}\n"
                    f"**Description:** {item_description}"
                ),
                inline=False
            )
        
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("Failed to fetch data from the API.")
        
bot.run(bot_token)