import discord, re, time
from discord.ext import commands

# DXNet cog for maibot DX+, specifically for user history.
class DXNetHistory(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    # Returns a profile of the user.
    @commands.command(help='Returns the current user who is logged in.')
    async def user(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )

        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            data = self.db[f"{user['segaID']}-profile"].find_one()

        # Create an embed and send back to user.
        embed = discord.Embed(title=data['name'], color=0x2e86c1)
        embed.set_thumbnail(url=data['player_logo'])
        embed.add_field(name='Rating:', value=f"{data['rating']}", inline=False)
        embed.add_field(name='Play Count:', value=f"{data['play_count']}", inline=False)
        embed.add_field(name='Last Played:', value=f"{data['last_played']}", inline=False)
        await ctx.message.channel.send(embed=embed)
    
    # Returns most recently played.
    @commands.command(help='Returns the most recently played song by user.')
    async def recent(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            pass
        
        # Attempt to get arguments from input.
        message = ctx.message.content
        input = message.split()

        # Do error checking on arguments.
        if len(input) == 1:
            history = self.db[f"{user['segaID']}-history"].find_one()
        elif len(input) == 2:
            if re.match('^\d+$', input[1]) is None or int(input[1]) > 50 or int(input[1]) < 1:
                await ctx.message.channel.send("```Usage: !recent [n] (where 1 <= n <= 50)```")
                return

        else:
            await ctx.message.channel.send("```Usage: !recent [n] (where 1 <= n <= 50)```")
            return

        # Create an embed and send back to user.
        if len(input) == 1:
            record = self.db[f"{user['segaID']}-records"].find({"song" : history['song'], "version" : history['version']})[0]
            embed = discord.Embed(title=history['song'], color=0x2e86c1)
            embed.set_thumbnail(url=history['song_icon'])
            embed.add_field(name='Version:', value=f"{history['version']}", inline=False)
            embed.add_field(name='Difficulty:', value=f"{history['diff']} ({record['records'][history['diff']]['level']})", inline=False)
            embed.add_field(name='Score:', value=f"{history['score']} ({history['rank']})", inline=False)
            embed.add_field(name='Time Played:', value=f"{history['time_played']}", inline=False)
            await ctx.message.channel.send(embed=embed)
        else:
            await ctx.message.channel.send(f"A list of your {input[1]} most recents songs will be sent to you via DM.")
            records = self.db[f"{user['segaID']}-history"].find({"_id" : {"$lt" : int(input[1])}})
            for history in records:
                record = self.db[f"{user['segaID']}-records"].find({"song" : history['song'], "version" : history['version']})[0]
                embed = discord.Embed(title=history['song'], color=0x2e86c1)
                embed.set_thumbnail(url=history['song_icon'])
                embed.add_field(name='Version:', value=f"{history['version']}", inline=False)
                embed.add_field(name='Difficulty:', value=f"{history['diff']} ({record['records'][history['diff']]['level']})", inline=False)
                embed.add_field(name='Score:', value=f"{history['score']} ({history['rank']})", inline=False)
                embed.add_field(name='Time Played:', value=f"{history['time_played']}", inline=False)
                await ctx.message.author.send(embed=embed)
                time.sleep(.5)

    # Returns stats regarding accuracy.
    @commands.command(help='Gives you overall accuracy from 50 games.')
    async def accuracy(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            history = self.db[f"{user['segaID']}-history"]
        
        fast = 0
        late = 0

        records = history.find()
        for _r in records:
            fast += _r['fast']
            late += _r['late']

        await ctx.message.channel.send(f"From your last 50 songs, you hit a total of {fast+late} notes inaccurately.\
        \n{round(fast/(fast+late), 4) * 100}% of the inaccurate notes were FAST and {round(late/(fast+late), 4) * 100}% were LATE.")

    # Returns information regarding last session.
    @commands.command(help='Gives you information for the last played session.')
    async def session(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            history = self.db[f"{user['segaID']}-history"]
        
        pb = 0
        solo = 0
        songs = 0
        fast = 0
        late = 0
        last_played = history.find_one()['time_played']
        date_played = last_played[:-6]

        records = history.find()
        for _r in records:
            if date_played in _r['time_played']:
                if _r['pb']: pb += 1
                if _r['solo']: solo += 1
                songs += 1
                fast += _r['fast']
                late += _r['late']

        solo_games = solo/3
        duo_games = (songs-solo)/4

        if songs == 50:
            await ctx.message.channel.send(f"From your last session of maimai DX+ ({date_played}), you played a total of at least {songs} songs.\
            \nOut of those {songs} songs, you achieved a new record in {pb} of them.\
            \nFrom the songs you played, you hit a total of {fast+late} notes inaccurately. {round(fast/(fast+late), 4) * 100}% of the inaccurate notes were FAST and {round(late/(fast+late), 4) * 100}% were LATE.")
        else:
            await ctx.message.channel.send(f"From your last session of maimai DX+ ({date_played}), you played a total of {songs} songs.\
            \nOut of those {songs} songs, you achieved a new record in {pb} of them. You played a total of {int(solo_games+duo_games)} games: {int(solo_games)} by yourself and {int(duo_games)} with someone else.\
            \nFrom the songs you played, you hit a total of {fast+late} notes inaccurately. {round(fast/(fast+late), 4) * 100}% of the inaccurate notes were FAST and {round(late/(fast+late), 4) * 100}% were LATE.")

    # Returns most recently played.
    @commands.command(help='Returns the songs played on the previous session session.')
    async def previous(self, ctx):

        # Get data about user.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            history = self.db[f"{user['segaID']}-history"]

        records = history.find()
        last_played = history.find_one()['time_played']
        date_played = last_played[:-6]

        await ctx.message.channel.send(f"A list of the songs played in your previous session will be sent to you via DM.")
        for _r in records:
            if date_played in _r['time_played']:
                record = self.db[f"{user['segaID']}-records"].find({"song" : _r['song'], "version" : _r['version']})[0]
                embed = discord.Embed(title=_r['song'], color=0x2e86c1)
                embed.set_thumbnail(url=_r['song_icon'])
                embed.add_field(name='Version:', value=f"{_r['version']}", inline=False)
                embed.add_field(name='Difficulty:', value=f"{_r['diff']} ({record['records'][_r['diff']]['level']})", inline=False)
                embed.add_field(name='Score:', value=f"{_r['score']} ({_r['rank']})", inline=False)
                embed.add_field(name='Time Played:', value=f"{_r['time_played']}", inline=False)
                await ctx.message.author.send(embed=embed)
                time.sleep(.5)
