import discord
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
            \nFrom the songs you played, you hit a total of {fast+late} notes inaccurately. {'{0:.2f}'.format(round(fast/(fast+late), 4) * 100)}% of the inaccurate notes were FAST and {'{0:.2f}'.format(round(late/(fast+late), 4) * 100)}% were LATE.")