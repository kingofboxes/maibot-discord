#!/usr/bin/env python3

# External modules.
import os, discord, pymongo, json, atexit
from dotenv import load_dotenv
from discord.ext import commands, tasks

# Import the cogs.
from modules.system import System
from modules.client import *

# Instantiate a client and run it.
bot = commands.Bot(command_prefix='!')

# Clean up function:
def shutdown():
    print("Bot has been shut down.")

# Load the required variables from .env file.
load_dotenv()
env_token = os.getenv('DISCORD_TOKEN')
username = os.getenv("DXNET_USR")
password = os.getenv("DXNET_PWD")

# Initialise a MaiDX client.
mdx = MaiDXClient()
mdx.login(username, password)

# Connect to DB.
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Create DB if it doesn't exist.
if f"{username}-maimaiDX" not in client.list_database_names():
    print("Initiating first run sequence...")

    # Create the schema and tables.
    db = client[f"{username}-maimaiDX"]
    profile = db["profile"]
    history = db["history"]
    records = db["records"]

    # Get player data.
    p = mdx.getPlayerData()
    r = mdx.getPlayerRecord()
    h = mdx.getPlayerHistory()

    # Insert data.
    profile.insert_one(p)
    history.insert_many(h)
    records.insert_many(r)

else:
    db = client[f"{username}-maimaiDX"]

# Add cogs to the bot.
bot.add_cog(System(bot, db, mdx))

# Run the bot.
atexit.register(shutdown)
bot.run(env_token)