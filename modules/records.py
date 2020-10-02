import discord, re, json
from discord.ext import commands

# DXNet cog for maibot DX+, specifically for records.
class DXNetRecords(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    # Returns most recently played song.
    @commands.command(help='Searches the database for a result.')
    async def search(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            records = self.db[f"{user['segaID']}-records"]
        
        # Attempt to get arguments from input.
        message = ctx.message.content

        if re.search(' -\w ', message):
            input = message.split(' ', 2)
        else:
            input = message.split(' ', 1)
        
        # Default behaviour is searching for master songs.
        # Sort by score, descending value.
        if len(input) == 2:
            pattern = input[1]
            pattern = re.sub(r"\'", "", pattern)
            pattern = re.sub(r"\"", "", pattern)
            r = records.find({ "song" : {"$regex": pattern, "$options" : "i"}, "records.MASTER.value" : {"$ne": None}}).sort('records.MASTER.value', -1).limit(3)

            # Backup search in case song has not been played.
            if r.count() == 0:
                r = records.find({ "song" : {"$regex": pattern, "$options" : "i"}}).sort(f'records.MASTER.value', -1).limit(3)

            if r.count() > 1:
                await ctx.message.channel.send("Found more than 1 song that matches your search query. Returning up to 3 songs...")
            elif r.count() == 0:
                await ctx.message.channel.send("Could not find specified title.")
                return
            else:
                pass

            for record in r:

                image = self.db['images'].find_one( {"_id" : record['_id']} )['url']
                embed = discord.Embed(title=record['song'], color=0x2e86c1)
                embed.set_thumbnail(url=image)
                embed.add_field(name='Genre:', value=f"{record['genre']}", inline=False)
                embed.add_field(name='Version:', value=f"{record['version']}", inline=False)
                embed.add_field(name='Difficulty:', value=f"MASTER ({record['records']['MASTER']['level']})", inline=False)
                embed.add_field(name='Score:', value=f"{record['records']['MASTER']['score']} ({record['records']['MASTER']['rank']})", inline=False)
                await ctx.message.channel.send(embed=embed)
        
        # Flags can be given.
        # Sort by score, descending value.
        elif len(input) == 3:
            
            if re.search(' -m ', message):
                diff = "MASTER"
            elif re.search(' -e ', message):
                diff = "EXPERT"
            elif re.search(' -r ', message):
                diff = "REMASTER"
            else:
                await ctx.message.channel.send("```Usage: !search [-e|m|r] <title>```")
                return

            pattern = input[2]
            pattern = re.sub(r"\'", "", pattern)
            pattern = re.sub(r"\"", "", pattern)
            r = records.find({ "song" : {"$regex": pattern, "$options" : "i"}, "records.MASTER.value" : {"$ne": None}}).sort(f'records.{diff}.value', -1).limit(3)

            # Backup search in case song has not been played.
            if r.count() == 0:
                r = records.find({ "song" : {"$regex": pattern, "$options" : "i"}}).sort(f'records.{diff}.score', -1).limit(3)

            if r.count() > 1:
                await ctx.message.channel.send("Found more than 1 song that matches your search query. Returning up to 3 songs...")
            elif r.count() == 0:
                await ctx.message.channel.send("Could not find specified title.")
                return
            else:
                pass

            for record in r:
                image = self.db['images'].find_one( {"_id" : record['_id']} )['url']
                embed = discord.Embed(title=record['song'], color=0x2e86c1)
                embed.set_thumbnail(url=image)
                embed.add_field(name='Genre:', value=f"{record['genre']}", inline=False)
                embed.add_field(name='Version:', value=f"{record['version']}", inline=False)
                embed.add_field(name='Difficulty:', value=f"{diff} ({record['records'][diff]['level']})", inline=False)
                embed.add_field(name='Score:', value=f"{record['records'][diff]['score']} ({record['records'][diff]['rank']})", inline=False)
                await ctx.message.channel.send(embed=embed)

        else:
            await ctx.message.channel.send("```Usage: !search [-e|m|r] <title>```")
            return

    # Queries the database.
    @commands.command(help='Queries the database.')
    async def query(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            records = self.db[f"{user['segaID']}-records"]
        
        # Attempt to get arguments from input.
        message = ctx.message.content

        if re.search(' -m ', message):
            diff = "MASTER"
        elif re.search(' -e ', message):
            diff = "EXPERT"
        elif re.search(' -r ', message):
            diff = "REMASTER"
        else:
            await ctx.message.channel.send("```Usage: !query <-e|-m|-r> <query>```")
            return
        
        # Process query.
        input = message.split(' ', 2)
        if len(input) != 3:
            await ctx.message.channel.send("```Usage: !query <-e|-m|-r> <query>```")
            return
        query = input[2]

        # Get records based on query.
        query = json.loads(query)
        r = records.find(query).sort(f'records.{diff}.score', -1).limit(3)

        if r.count() > 1:
            await ctx.message.channel.send("Found more than 1 song that matches your query string. Returning up to 3 songs...")
        elif r.count() == 0:
            await ctx.message.channel.send("Could not find any songs with specified query.")
            return
        else:
            pass

        for record in r:
            image = self.db['images'].find_one( {"_id" : record['_id']} )['url']
            embed = discord.Embed(title=record['song'], color=0x2e86c1)
            embed.set_thumbnail(url=image)
            embed.add_field(name='Genre:', value=f"{record['genre']}", inline=False)
            embed.add_field(name='Version:', value=f"{record['version']}", inline=False)
            embed.add_field(name='Difficulty:', value=f"{diff} ({record['records'][diff]['level']})", inline=False)
            embed.add_field(name='Score:', value=f"{record['records'][diff]['score']} ({record['records'][diff]['rank']})", inline=False)
            await ctx.message.channel.send(embed=embed)
        