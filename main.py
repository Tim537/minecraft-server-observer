from script_secrets import get_mcalj_discord_message_id
from script_secrets import get_mcalj_discord_channel_id
from script_secrets import get_mcalj_discord_token
from script_secrets import get_mc_server_list
from mcstatus import JavaServer as MinecraftServer
from discord.ext import commands
from discord.ext import tasks
from lxml import etree
import requests
import discord
import time

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Cookie': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
}

discord_token = get_mcalj_discord_token()
discord_message = get_mcalj_discord_message_id()
discord_channel = get_mcalj_discord_channel_id()
minecraft_servers = get_mc_server_list()

discord_client = commands.Bot(command_prefix="MCALJ!", intents=discord.Intents.all(), help_command=None)

def get_html(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        headers['Cookie'] = response.headers['Set-Cookie'].split(";")[0]
        return response.text
    except requests.exceptions.HTTPError as e:
        print(e)
        return None
    
def is_available(url):
    html_raw = get_html(url)
    if html_raw is None:
        print("Error: No html for " + url)

    if "nicht verfügbar" in html_raw:
        return False
    
    return True

@discord_client.event
async def on_ready():
    check_offer.start()
    update_status.start()  

@tasks.loop(seconds=5)
async def check_offer():
    url = "https://taschengelddieb.de/823473224876-Try-It-Bot-IF-YOU-CAN"

    if is_available(url):
        notifications = [
            309746842894204929,
            277124058179567616
        ]

        for user in notifications:
            discord_user = discord_client.get_user(user)
            await discord_user.send("Das [Angebot](https://taschengelddieb.de/lego-avatar-75576-skimwing-abenteuer) ist verfügbar!")

@tasks.loop(seconds=5*60)
async def update_status():
    statuses = []
    for server in minecraft_servers:
        status = check_server(server["ip"], server["nickname"])
        statuses.append(status)

        if status["online"] and not server["cache_online"]:
            channel = discord_client.get_channel(discord_channel)                
            message = await channel.send(f"<@309746842894204929>\n {server['nickname']} ist jetzt online!")
            # time.sleep(3)
            # await message.delete()

        if not status["online"] and server["cache_online"]:
            channel = discord_client.get_channel(discord_channel)                
            message = await channel.send(f"<@309746842894204929>\n {server['nickname']} ist jetzt offline!")
            # time.sleep(3)
            # await message.delete()

        if status["online"]:
            server["cache_online"] = True
        else:
            server["cache_online"] = False

    formatted_status = "**__List of Minecraft Servers:__**\n\n"
    for status in statuses:            
        formatted_status += format_discord_status(status)

    message = await discord_client.get_channel(discord_channel).fetch_message(discord_message)
    await message.edit(content=formatted_status)

def check_server(ip, server_name):
    try:
        server = MinecraftServer.lookup(ip)
        status_raw = server.status()
        status = {
            "online": True,
            "nickname": server_name,
            "players_online": status_raw.players.online,
        }
        return status
    except:
        return {
            "online": False,
            "nickname": server_name,
        }
    
def format_discord_status(status):
    if status["online"]:
        return f"- {status['nickname']} ist online mit {status['players_online']} Spieler{'n' if status['players_online'] > 1 else ''}\n"
    else:
        return f"- {status['nickname']} ist offline\n"

discord_client.run(discord_token)