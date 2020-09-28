import discord, re, requests, json
from modules.client import *
from discord.ext import commands

# System cog.
class DXNet(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    # Get an instance of DX Net client.
    def getDXNetClient(self, ctx):
        account = self.db['users'].find_one( { "_id" : ctx.message.author.id } )
        if account is None:
            return None
        else:
            jar = requests.cookies.RequestsCookieJar()
            for entry in json.loads(account['cookie']):
                jar.set(**entry)
            mdx = MaiDXClient(jar)
            return mdx

    # Checks if player state has changed.
    def stateChanged(self, p, ctx):
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )['segaID']
        cache = self.db[f"{user}-profile"].find_one({ "_id" : p['_id']})

        if cache is None:
            return True

        for key in p:
            if (p[key] != cache[key]):
                 return True

        return False

    # Updates the user cookies stored in MongoDB for future requests.
    def updateUserCookies(self, ctx, mdx):
        cookie_attrs = ["version", "name", "value", "port", "domain", "path", "secure", "expires", "discard", "comment", "comment_url", "rfc2109"]
        cookies = json.dumps([{attr: getattr(cookie, attr) for attr in cookie_attrs} for cookie in mdx.getSessionCookies()])
        if len(cookies) == 1482:
            query = { "_id" : ctx.message.author.id }
            newValues = { "$set" : { "cookie" :  cookies} }
            self.db["users"].update_one(query, newValues)

    # Returns a profile of the user.
    @commands.command(help='Updates the current client instance of maibot.')
    async def refresh(self, ctx):

        # Alert user that process is starting.
        await ctx.message.channel.send("Refreshing data from maimai DX NET, this could take up to a minute...")

        # Get DX Net Client.
        user = self.db['users'].find_one( {"_id" : ctx.message.author.id} )
        if user is None or user['segaID'] is None:
            await ctx.message.channel.send("You have not yet mapped your Discord account to a SEGA ID. Please use !map to do.")
            return
        elif user['cookie'] is None:
            await ctx.message.channel.send("You have not yet provided a password. Please use !password to do.")
            return
        else:
            mdx = self.getDXNetClient(ctx)

        p = mdx.getPlayerData()
        if not self.stateChanged(p, ctx):
            self.updateUserCookies(ctx, mdx)
            await ctx.message.channel.send("Game history and records are already up to date.")

        else:

            # Update profile.
            profile = self.db[f"{user['segaID']}-profile"]
            _q = { "_id" : p['_id']}
            _v = { "$set": p }
            if profile.find_one(_q):
                profile.update_one(_q, _v)
            else:
                profile.insert_one(p)

            # Update player history.
            history = self.db[f"{user['segaID']}-history"]
            h = mdx.getPlayerHistory()

            for _h in h:
                _q = { "_id": _h['_id']}
                _v = { "$set": _h}
                if history.find_one(_q):
                    history.update_one(_q, _v)
                else:
                    history.insert_one(_h)

            # Update player records.
            records = self.db[f"{user['segaID']}-records"]
            r = mdx.getPlayerRecord()

            for _r in r:
                _q = { "_id": _r['_id']}
                _v = { "$set": _r}
                if records.find_one(_q) is not None:
                    records.update_one(_q, _v)
                else:
                    records.insert_one(_r)

            self.updateUserCookies(ctx, mdx)
            await ctx.message.channel.send(f"Your game history and records have been updated, {ctx.message.author.mention}!")
            

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
                history = self.db[f"{user['segaID']}-history"].find_one({"_id" : int(input[1]) - 1})
        else:
            await ctx.message.channel.send("```Usage: !recent [n] (where 1 <= n <= 50)```")
            return

        # Create an embed and send back to user.
        record = self.db[f"{user['segaID']}-records"].find({"song" : history['song'], "version" : history['version']})[0]
        embed = discord.Embed(title=history['song'], color=0x2e86c1)
        embed.set_thumbnail(url=history['song_icon'])
        embed.add_field(name='Version:', value=f"{history['version']}", inline=False)
        embed.add_field(name='Difficulty:', value=f"{history['diff']} ({record['records'][history['diff']]['level']})", inline=False)
        embed.add_field(name='Score:', value=f"{history['score']} ({history['rank']})", inline=False)
        embed.add_field(name='Time Played:', value=f"{history['time_played']}", inline=False)
        await ctx.message.channel.send(embed=embed)

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
        input = message.split(' ', 1)
        
        # Do error checking on arguments.
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

    # Returns most recently played.
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