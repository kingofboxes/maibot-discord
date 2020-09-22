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
mdx_username = os.getenv("DXNET_USR")
mdx_password = os.getenv("DXNET_PWD")
db_username = os.getenv("MONGO_USR")
db_password = os.getenv("MONGO_PWD")
db_hostname = os.getenv("MONGO_HOSTNAME")
db_port = os.getenv("MONGO_PORT")

# Initialise a MaiDX client.
mdx = MaiDXClient()
mdx.login(mdx_username, mdx_password)

# Connect to DB.
client = pymongo.MongoClient(f"mongodb://{db_username}:{db_password}@{db_hostname}:{db_port}")

# Create DB if it doesn't exist.
if "maimaiDX" not in client.list_database_names():
    print("Initiating first run sequence...")

    # Create the schema and tables.
    db = client["maimaiDX"]
    profile = db[f"{mdx_username}-profile"]
    history = db[f"{mdx_username}-history"]
    records = db[f"{mdx_username}-records"]

    # Get player data.
    p = mdx.getPlayerData()
    r = mdx.getPlayerRecord()
    h = mdx.getPlayerHistory()

    # Insert data.
    profile.insert_one(p)
    history.insert_many(h)
    records.insert_many(r)

else:
    db = client["maimaiDX"]

# Add cogs to the bot.
bot.add_cog(System(bot, db, mdx, mdx_username))

# Run the bot.
atexit.register(shutdown)
bot.run(env_token)