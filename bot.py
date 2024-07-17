import discord
from discord.ext import commands, tasks
import asyncio
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Load your Discord token
DISCORD_TOKEN = 'discord_bot_token'

# Load the JSON file with player data
with open('auction-sets.json', 'r') as file:
    auction_data = json.load(file)

# Dictionary to store user data (team name, balance, players, etc.)
user_data = {}

# Dictionary to track active auctions
active_auction = None
current_player_index = 0
current_player = None
bidding_in_progress = False
timer_task = None

# Set up the bot
intents = discord.Intents.all()
intents.typing = False  # Adjust based on your bot's needs
intents.presences = True  # Enable presence intent
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Function to load ownership data
def load_ownership_data():
    if os.path.exists('ownership.json'):
        with open('ownership.json', 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

# Function to save ownership data
def save_ownership_data(data):
    with open('ownership.json', 'w') as file:
        json.dump(data, file, indent=4)

# Load the ownership data at the start
ownership_data = load_ownership_data()

# Function to scrape player data from a given profile URL
def scrape_player_data(profile_url):
    response = requests.get(profile_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    stats = {}

    # Extract player info from the first table
    player_info_table = soup.find_all('table')[0]
    for row in player_info_table.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(strip=True).replace(':', '')
            value = td.get_text(strip=True)
            stats[key] = value

    # Extract additional player stats from the second table
    stats_table = soup.find_all('table')[1]
    for row in stats_table.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(strip=True).replace(':', '')
            value = td.get_text(strip=True)
            stats[key] = value

    # Extract player image from the div with class flip-box-back
    image_tag = soup.find('div', {'class': 'flip-box-back'}).find('img')
    if image_tag:
        stats['image'] = image_tag.get('src')

    # Extract playing styles and player skills from the third table
    playing_styles_table = soup.find_all('table', class_='playing_styles')[0]
    current_section = ''
    for row in playing_styles_table.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        if th:
            current_section = th.get_text(strip=True)
            stats[current_section] = []
        if td:
            value = td.get_text(strip=True)
            stats[current_section].append(value)

    return stats

@bot.command()
async def player(ctx, *, player_name):
    # Find the player's profile URL from your auction_data
    player_profile_url = None
    for player in auction_data['players']:
        if player['name'].lower() == player_name.lower():
            player_profile_url = player['profile_url']
            break

    if player_profile_url is None:
        await ctx.send("Player not found.")
        return

    # Scrape player data
    player_info = scrape_player_data(player_profile_url)
    filtered_player_info = filter_stats(player_info)

    # Create and send embed message with player details
    embed = discord.Embed(title=filtered_player_info.get('Player Name'))
    embed.set_thumbnail(url=filtered_player_info.get('image'))

    field_count = 0
    for key, value in filtered_player_info.items():
        if key != 'image' and key != 'Player Name':
            embed.add_field(name=key, value=value, inline=True)
            field_count += 1
            if field_count >= 25:
                break

    await ctx.send(embed=embed)

# Filter out unwanted details
def filter_stats(stats):
    unwanted_keys = [
        'Defensive Awareness', 'Tackling', 'Aggression', 'Defensive Engagement',
        'Speed', 'Acceleration', 'Kicking Power', 'Jumping', 'Physical Contact',
        'Balance', 'Stamina', 'Weak Foot Usage', 'Weak Foot Accuracy', 'Form',
        'Injury Resistance', 'Playing Style', 'Player Skills', 'AI Playing Styles'
    ]
    return {key: value for key, value in stats.items() if key not in unwanted_keys}

async def show_auction_player(ctx):
    global current_player

    if current_player is None:
        await ctx.send("No player available for auction.")
        return

    player_info = scrape_player_data(current_player['profile_url'])
    filtered_player_info = filter_stats(player_info)

    embed = discord.Embed(title=filtered_player_info.get('Player Name'))
    embed.set_thumbnail(url=filtered_player_info.get('image'))

    field_count = 0
    for key, value in filtered_player_info.items():
        if key != 'image' and key != 'Player Name':
            embed.add_field(name=key, value=value, inline=True)
            field_count += 1
            if field_count >= 25:
                break

    view = BidView()
    await ctx.send(embed=embed, view=view)

async def start_timer(ctx):
    global timer_task
    for i in range(10, 0, -1):
        await ctx.send(f"Time remaining: {i} seconds")
        await asyncio.sleep(1)

    await finalize_bid(ctx)

async def finalize_bid(ctx):
    global active_auction, current_player, bidding_in_progress

    if current_player['id'] in active_auction["players_bids"]:
        highest_bid = active_auction["players_bids"][current_player['id']]
        bidder_id = highest_bid["bidder_id"]
        bid_amount = highest_bid["bid_amount"]

        user_data[bidder_id]["balance"] -= bid_amount
        user_data[bidder_id]["players"].append(current_player['name'])

        await ctx.send(f"{current_player['name']} sold to {bot.get_user(bidder_id).name} for {bid_amount} kicks.")
    else:
        await ctx.send(f"No bids for {current_player['name']}.")

    bidding_in_progress = False

@bot.command()
async def nextbid(ctx):
    global current_player_index, current_player, bidding_in_progress, timer_task

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    if timer_task:
        timer_task.cancel()

    current_player_index += 1
    if current_player_index < len(auction_data['players']):
        current_player = auction_data['players'][current_player_index]
        await show_auction_player(ctx)
        bidding_in_progress = True
        timer_task = bot.loop.create_task(start_timer(ctx))
    else:
        await ctx.send("No more players in the auction.")

@bot.command()
async def startauction(ctx, auction_name: str):
    global active_auction, current_player_index, current_player, bidding_in_progress, timer_task

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    if active_auction is not None:
        await ctx.send("An auction is already in progress.")
        return

    active_auction = {
        "players_bids": {},
        "name": auction_name,
        "date": datetime.now().isoformat()
    }

    ownership_data[auction_name] = {
        "date": active_auction["date"],
        "teams": {}
    }
    save_ownership_data(ownership_data)

    await ctx.send(f"Auction '{auction_name}' has been started. Use !join <team-name> to join.")

@bot.command()
async def join(ctx, team_name: str):
    user_id = ctx.author.id
    user_data[user_id] = {"team_name": team_name, "balance": 100000, "players": []}
    await ctx.send(f"{ctx.author.name} has joined the auction with team name {team_name}.")

@bot.command()
async def starting(ctx):
    global current_player_index, current_player, bidding_in_progress, timer_task

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    if active_auction is None:
        await ctx.send("No auction is currently active.")
        return

    current_player_index = 0
    current_player = auction_data['players'][current_player_index]
    await show_auction_player(ctx)
    bidding_in_progress = True
    timer_task = bot.loop.create_task(start_timer(ctx))

@bot.command()
async def closeauction(ctx):
    global active_auction, bidding_in_progress, timer_task

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    if active_auction is None:
        await ctx.send("No auction is currently active.")
        return

    if timer_task:
        timer_task.cancel()

    auction_name = active_auction["name"]
    ownership_data[auction_name]["teams"] = {user_data[user_id]["team_name"]: {"players": user_data[user_id]["players"]} for user_id in user_data}
    save_ownership_data(ownership_data)

    active_auction = None
    bidding_in_progress = False
    await ctx.send("Auction has been closed and ownership details saved.")

@bot.command()
async def commands(ctx):
    help_message = """
    **Available Commands:**
    `!startauction <auction-name>` - Start a new auction.
    `!join <team-name>` - Join the auction with a team name.
    `!starting` - Start the auction.
    `!nextbid` - Move to the next player for bidding.
    `!closeauction` - Close the current auction.
    `!ping` - Check bot latency.
    `!player <player-name>` - Get information about a specific player.
    `!myteam` - Show your current players and remaining balance.
    """
    await ctx.send(help_message)

@bot.command()
async def myteam(ctx):
    user_id = ctx.author.id
    if user_id not in user_data:
        await ctx.send("You are not registered in the auction. Use `!join <team-name>` to join.")
        return

    team_info = user_data[user_id]
    team_name = team_info["team_name"]
    balance = team_info["balance"]
    players = team_info["players"]

    embed = discord.Embed(title=f"{ctx.author.name}'s Team: {team_name}")
    embed.add_field(name="Balance", value=f"{balance} kicks", inline=False)
    embed.add_field(name="Players", value="\n".join(players) if players else "No players", inline=False)

    await ctx.send(embed=embed)

class BidView(discord.ui.View):
    @discord.ui.button(label="Bid", style=discord.ButtonStyle.primary)
    async def bid_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        global active_auction, current_player, bidding_in_progress, timer_task

        user_id = interaction.user.id
        if user_id not in user_data:
            await interaction.response.send_message("You are not registered in the auction. Use `!join <team-name>` to join.", ephemeral=True)
            return

        if not bidding_in_progress:
            await interaction.response.send_message("No auction in progress.", ephemeral=True)
            return

        user_balance = user_data[user_id]["balance"]
        current_bid = active_auction["players_bids"].get(current_player['id'], {}).get("bid_amount", 0)

        if user_balance < current_bid + 1000:
            await interaction.response.send_message("Insufficient balance for the bid.", ephemeral=True)
            return

        active_auction["players_bids"][current_player['id']] = {"bidder_id": user_id, "bid_amount": current_bid + 1000}
        await interaction.response.send_message(f"Bid placed: {current_bid + 1000} kicks by {interaction.user.name}", ephemeral=True)

        # Send a message to the channel as well
        await interaction.channel.send(f"{interaction.user.name} placed a bid of {current_bid + 1000} kicks for {current_player['name']}.")


@bot.command()
async def walletreset(ctx):
    user_id = ctx.author.id
    if user_id in user_data:
        user_data[user_id]["balance"] = 100000
        await ctx.send(f"{ctx.author.name}, your wallet has been reset to 100,000 kicks.")
    else:
        await ctx.send("You are not registered in the auction. Use `!join <team-name>` to join.")

# Run the bot
bot.run(DISCORD_TOKEN)
