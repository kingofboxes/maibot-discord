#!/usr/bin/env python3

# External modules.
import os, discord, pymongo, json, atexit
from dotenv import load_dotenv
from discord.ext import commands, tasks

# Import the cogs.
from modules.system import System
from modules.login import Login
from modules.dxnet import DXNet
from modules.history import DXNetHistory
from modules.records import DXNetRecords
from modules.playlist import DXNetPlaylist

# Intents update for Discord.py 1.5.1.
intents = discord.Intents.default()
intents.members = True

# Instantiate a client and run it.
bot = commands.Bot(command_prefix='!', intents=intents)

# Clean up function:
def shutdown():
    print("Bot has been shut down.")

# Load the required variables from .env file.
load_dotenv()
env_token = os.getenv('DISCORD_TOKEN')
db_username = os.getenv("MONGO_USR")
db_password = os.getenv("MONGO_PWD")
db_hostname = os.getenv("MONGO_HOSTNAME")
db_port = os.getenv("MONGO_PORT")

# Connect to DB.
if db_username:
    client = pymongo.MongoClient(f"mongodb://{db_username}:{db_password}@{db_hostname}:{db_port}")
else:
    client = pymongo.MongoClient(f"mongodb://127.0.0.1:27017")

# Create maimaiDX database.
db = client["maimaiDX"]

# Add cogs to the bot.
bot.add_cog(System(bot, db))
bot.add_cog(Login(bot, db))
bot.add_cog(DXNet(bot, db))
bot.add_cog(DXNetHistory(bot, db))
bot.add_cog(DXNetRecords(bot, db))
bot.add_cog(DXNetPlaylist(bot, db))

# Run the bot.
atexit.register(shutdown)
bot.run(env_token)
