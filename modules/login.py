import json
from modules.client import *
from discord.ext import commands

# Login module for maibot DX+.
class Login(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    # Maps the user of the command to their provided SEGA ID.
    @commands.command(help='Maps the current user to a SEGA ID.')
    async def map(self, ctx):

        # Gather required variables.
        users = self.db["users"]
        account = users.find_one( { "_id" : ctx.message.author.id } )

        # Attempt to get arguments from input.
        message = ctx.message.content
        input = message.split(' ')

        # Do error checking on arguments.
        if len(input) != 2:
            await ctx.message.channel.send("```Usage: !map <username>```")
            return

        # Add mapping to MongoDB.
        if account is None:
            mapping = { "_id" : ctx.message.author.id, 
                        "segaID" : input[1],
                        "cookie" : None,
                    }
            users.insert_one(mapping)
            await ctx.message.channel.send(f"Mapping {ctx.message.author.mention} to SEGA ID '{input[1]}'.")
            await ctx.message.author.send(f"Please enter your password using the !password command (i.e. !password <password>, without the <>).")
        else:
            query = { "_id" : ctx.message.author.id }
            newValues = { "$set" : { "segaID" : input[1] } }
            users.update_one(query, newValues)
            await ctx.message.channel.send(f"{ctx.message.author.mention} is now mapped to SEGA ID '{input[1]}'.")
            

    # Logs user into account.
    @commands.command(help='Logs into the account.')
    async def password(self, ctx):

        # Verify there is a mapping.
        account = self.db["users"].find_one( { "_id" : ctx.message.author.id } )
        if account is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return

        # Attempt to get arguments from input.
        message = ctx.message.content
        input = message.split(' ')

        # Do error checking on arguments.
        if len(input) != 2:
            await ctx.message.channel.send("```Usage: !password <password>```")
            return

        # Log in to the client (this is the only place where password is used, but never stored)
        mdx = MaiDXClient()
        mdx.login(account['segaID'], input[1])
        
        # Dump session cookies in MongoDB.
        c = mdx.getSessionCookies()
        cookie_attrs = ["version", "name", "value", "port", "domain", "path", "secure", "expires", "discard", "comment", "comment_url", "rfc2109"]
        cookiedata = json.dumps([{attr: getattr(cookie, attr) for attr in cookie_attrs} for cookie in c])
        query = { "_id" : ctx.message.author.id }
        newValues = { "$set" : { "cookie" : cookiedata } }
    
        if account['cookie'] is None:
            await ctx.message.channel.send("Your account has been linked! You now have access to all the features of the bot.")
        else:
            await ctx.message.channel.send("Your password has been updated.")
        
        self.db["users"].update_one(query, newValues)

        


        

        



            
