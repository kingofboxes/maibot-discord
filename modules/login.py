import discord, json, pymongo, re
from datetime import datetime
from discord.ext import commands
from modules.client import *

# System cog.
class Login(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    # Returns a profile of the user.
    @commands.command(help='Maps the current user to a SEGA ID.')
    async def map(self, ctx):

        users = self.db["users"]
        account = users.find_one( { "_id" : ctx.message.author.id } )
        segaID = ctx.message.content.split(' ', 1)[1]

        if account is None:
            mapping = { "_id" : ctx.message.author.id, 
                        "segaID" : segaID,
                        "password" : None,
                    }
            users.insert_one(mapping)
            await ctx.message.channel.send(f"Mapping {ctx.message.author.mention} to SEGA ID '{segaID}'.")
            await ctx.message.author.send(f"Please enter your password using the !password command (i.e. !link <password>).")
        else:
            await ctx.message.channel.send(f"{ctx.message.author.mention} already mapped to SEGA ID '{segaID}'.")

    # Returns a profile of the user.
    @commands.command(help='Logs into the account.')
    async def link(self, ctx):

        account = self.db["users"].find_one( { "_id" : ctx.message.author.id } )

        if account is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        
        mdx_password = ctx.message.content.split(' ', 1)[1]
        query = { "_id" : ctx.message.author.id }
        newValues = { "$set" : {"password" : mdx_password}}

        self.db["users"].update_one(query, newValues)

        await ctx.message.channel.send("Your account has been linked! You now have access to all the features of the bot.")



            
