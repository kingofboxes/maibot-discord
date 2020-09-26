import discord
from discord.ext import commands

# System cog.
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
            await ctx.message.channel.send("```Usage: !map <username> (without the <>)```")
            return

        # Add mapping to MongoDB.
        if account is None:
            mapping = { "_id" : ctx.message.author.id, 
                        "segaID" : input[1],
                        "password" : None,
                    }
            users.insert_one(mapping)
            await ctx.message.channel.send(f"Mapping {ctx.message.author.mention} to SEGA ID '{input[1]}'.")
            await ctx.message.author.send(f"Please enter your password using the !password command (i.e. !password <password>, without the <>).")
        else:
            await ctx.message.channel.send(f"Error: {ctx.message.author.mention} already mapped to SEGA ID '{input[1]}'.")

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
            await ctx.message.channel.send("```Usage: !password <password> (without the <>)```")
            return

        # Update MongoDB.
        query = { "_id" : ctx.message.author.id }
        newValues = { "$set" : {"password" : input[1]} }
    
        if account['password'] is None:
            await ctx.message.channel.send("Your account has been linked! You now have access to all the features of the bot.")
        else:
            await ctx.message.channel.send("Your password has been updated.")
        
        self.db["users"].update_one(query, newValues)

        


        

        



            
