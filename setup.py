import os
from discord import Intents
from dotenv import load_dotenv
from discord.ext import commands
from actions import Actions


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = Intents.default()
# need this for commands extension to function
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")
action = Actions(bot)
