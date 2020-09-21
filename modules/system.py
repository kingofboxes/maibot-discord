import discord, json, pymongo, re
from datetime import datetime
from discord.ext import commands
from time import gmtime, strftime

# System cog.
class System(commands.Cog):

    def __init__(self, bot, db, mdx):
        self.bot = bot
        self.db = db
        self.mdx = mdx

    @commands.Cog.listener()
    async def on_ready(self):

        # Activate background checks.
        print(f'[{datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}] Logged in as {self.bot.user}!')

        # Fluff.
        custom_activity = discord.Game(name="Discord")
        await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=custom_activity)

    @commands.Cog.listener()
    async def on_message(self, message):

        # Stops bot from trigger responses to its own messages.
        if message.author == self.bot.user:
            return

        # Log the message in console, change output to log file later.
        print(f'[{datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}] Message from {message.author}: {message.content}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send('You do not have permission to use this command.')

    # Checks if player state has changed.
    def stateChanged(self, p):
        cache = self.db["profile"].find_one({ "_id" : p['_id']})
        for key in p:
            if (p[key] != cache[key]):
                 return True
        return False

    # Returns a profile of the user.
    @commands.command(help='Updates the current client instance of maibot.')
    async def refresh(self, ctx):
        await ctx.message.channel.send("Refreshing data from maimai DX NET, this could take up to a minute...")

        p = self.mdx.getPlayerData()
        if not self.stateChanged(p):
            await ctx.message.channel.send("Game history and records are already up to date.")
        else:
       
            # Update profile.
            profile = self.db['profile']
            _q = { "_id" : p['_id']}
            _v = { "$set": p }
            profile.update_one(_q, _v)

            # Update player records.
            records = self.db['records']
            r = self.mdx.getPlayerRecord()

            for _r in r:
                _q = { "_id": _r['_id']}
                _v = { "$set": _r}
                records.update_one(_q, _v)

            # Update player history.
            history = self.db['history']
            h = self.mdx.getPlayerHistory()

            for _h in h:
                _q = { "_id": _h['_id']}
                _v = { "$set": _h}
                history.update_one(_q, _v)

            await ctx.message.channel.send(f"Your game history and records have been updated, {ctx.message.author.mention}!")
            

    # Returns a profile of the user.
    @commands.command(help='Returns the current user who is logged in.')
    async def user(self, ctx):
        data = self.db["profile"].find_one()
        embed = discord.Embed(title=data['name'], color=0x2e86c1)
        embed.set_thumbnail(url=data['player_logo'])
        embed.add_field(name='Rating:', value=f"{data['rating']}", inline=False)
        embed.add_field(name='Play Count:', value=f"{data['play_count']}", inline=False)
        embed.add_field(name='Last Played:', value=f"{data['last_played']}", inline=False)
        await ctx.message.channel.send(embed=embed)
    
    # Returns most recently played.
    @commands.command(help='Returns the most recently played song by user.')
    async def recent(self, ctx):
        
        message = ctx.message.content
        input = message.split()

        if len(input) == 1:
            history = self.db["history"].find_one()
        elif len(input) == 2:
            if re.match('^\d+$', input[1]) is None or int(input[1]) > 50 or int(input[1]) < 1:
                await ctx.message.channel.send("```Usage: !recent [n] (where 1 <= n <= 50)```")
                return
            else:
                history = self.db["history"].find_one({"_id" : int(input[1]) - 1})
        else:
            await ctx.message.channel.send("```Usage: !recent [n] (where 1 <= n <= 50)```")
            return

        record = self.db["records"].find({"song" : history['song'], "version" : history['version']})[0]
        embed = discord.Embed(title=history['song'], color=0x2e86c1)
        embed.set_thumbnail(url=history['song_icon'])
        embed.add_field(name='Version:', value=f"{history['version']}", inline=False)
        embed.add_field(name='Difficulty:', value=f"{history['diff']} ({record['records'][history['diff']]['level']})", inline=False)
        embed.add_field(name='Score:', value=f"{history['score']} ({history['rank']})", inline=False)
        embed.add_field(name='Time Played:', value=f"{history['time_played']}", inline=False)
        await ctx.message.channel.send(embed=embed)

    # Returns most recently played.
    @commands.command(help='Searches the database for a result.')
    async def search(self, ctx):
        
        message = ctx.message.content
        input = message.split(' ', 1)
        records = self.db["records"]

        if len(input) == 2:
            pattern = input[1]
            pattern = re.sub(r"\'", "", pattern)
            pattern = re.sub(r"\"", "", pattern)
            r = records.find_one({ "song" : {"$regex": pattern} })

            if not r:
                await ctx.message.channel.send("Could not find specified title.")
                return
            else:
                embed = discord.Embed(title=r['song'], color=0x2e86c1)
                embed.add_field(name='Genre:', value=f"{r['genre']}", inline=False)
                embed.add_field(name='Version:', value=f"{r['version']}", inline=False)
                embed.add_field(name='Difficulty:', value=f"{r['records']['MASTER']['diff']} ({r['records']['MASTER']['level']})", inline=False)
                embed.add_field(name='Score:', value=f"{r['records']['MASTER']['score']} ({r['records']['MASTER']['rank']})", inline=False)
        else:
            await ctx.message.channel.send("```Usage: !search <title>```")
            return

        await ctx.message.channel.send(embed=embed)

    # Manually shut bot down.
    @commands.command(help='Shuts the bot down')
    @commands.is_owner()
    async def nap(self, ctx):

        # Alert everyone that bot is shutting down.
        await ctx.message.channel.send("Good night...")

        # Closes the bot gracefully.
        await self.bot.logout()