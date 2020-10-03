import discord, re, time
from discord.ext import commands

# DXNet cog for maibot DX+, specifically for user history.
class DXNetPlaylist(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    # Add to a list.
    @commands.command(help='Add to a playlist.')
    async def add(self, ctx):

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
            profile = self.db[f"{user['segaID']}-profile"]

        # Attempt to get arguments from input.
        message = ctx.message.content
        
        if re.search(' -ms ', message):
            diff = "MASTER"
            version = "STANDARD"
        elif re.search(' -es ', message):
            diff = "EXPERT"
            version = "STANDARD"
        elif re.search(' -rs ', message):
            diff = "REMASTER"
            version = "STANDARD"
        elif re.search(' -ed ', message):
            diff = "EXPERT"
            version = "DELUXE"
        elif re.search(' -md ', message):
            diff = "MASTER"
            version = "DELUXE"
        elif re.search(' -rd ', message):
            diff = "REMASTER"
            version = "DELUXE"
        else:
            await ctx.message.channel.send("```Usage: !add <-ed|-md|-rd|-es|-ms|-rs> <song>```")
            return

        input = message.split(' ', 2)
        if len(input) != 3:
            await ctx.message.channel.send("```Usage: !add <-ed|-md|-rd|-es|-ms|-rs> <song>```")
            return
        
        r = records.find_one({ "song" : input[2], "version": version})
        if not r:
            await ctx.message.channel.send("Could not find specified title.")
            return
        
        level = r['records'][diff]['level']
        value = re.sub("\+", ".5", level)
        
        entry = { 
            "song" : r['song'],
            "version" : r['version'],
            "level" : r['records'][diff]['level'],
            "value" : float(value)
        }

        player = profile.find_one()
        playlist = player['playlist']
        playlist.append(entry)
        playlist.sort(key = lambda x: x['value'])
        profile.update_one( {'_id' : player['_id'] }, {'$set': {'playlist' : playlist}} )

        await ctx.message.channel.send("Song successfully added to playlist.")

    # Add to a list.
    @commands.command(help='Output list.')
    async def playlist(self, ctx):

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
            profile = self.db[f"{user['segaID']}-profile"]

        player = profile.find_one()
        playlist = player['playlist']

        if len(playlist) == 0:
            await ctx.message.channel.send("There are no songs in your playlist.")
            return

        songs = "```"
        id = 1
        for entry in playlist:
            songs += f"[{id}] {entry['song']} ({entry['level']})\n"
            id += 1
        songs += "```"

        await ctx.message.channel.send(songs)

    # Remove from list.
    @commands.command(help='Remove stuff from list.')
    async def remove(self, ctx):

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
            profile = self.db[f"{user['segaID']}-profile"]

        message = ctx.message.content
        input = message.split(' ', 1)

        player = profile.find_one()
        playlist = player['playlist']

        if len(input) != 2 or not re.match('^\d+$', input[1]):
            await ctx.message.channel.send("```Usage: !remove <number>```")
            return
        elif int(input[1]) > len(playlist) or int(input[1]) < 1:
            await ctx.message.channel.send("Please provide a valid number.")
            return
        
        playlist.pop(int(input[1])-1)
        profile.update_one( {'_id' : player['_id'] }, {'$set': {'playlist' : playlist}} )
        await ctx.message.channel.send("Song successfully removed from playlist.")