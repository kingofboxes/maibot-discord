import discord, re, requests, json
from modules.client import *
from discord.ext import commands

# DXNet cog for maibot DX+.
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

    # Scrapes a list of album art covers.
    # Heavily hammers everything, should only be used when new songs come out.
    @commands.command(help='Scrapes a list of album art covers.')
    @commands.is_owner()
    async def images(self, ctx):

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

        i = mdx.getImageURLs()

        images = self.db["images"]
        for _i in i:
            _q = { "_id" : _i['_id']}
            _v = { "$set": _i }
            if images.find_one(_q):
                images.update_one(_q, _v)
            else:
                images.insert_one(_i)
        
        # Alert user that process is starting.
        await ctx.message.channel.send("Images successfully ripped.")

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
    @commands.command(help='Gives you overall accuracy from 50 games.')
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
        last_played = history.find_one()['time_played']
        date_played = last_played[:-6]

        records = history.find()
        for _r in records:
            if date_played in _r['time_played']:
                if _r['pb']: pb += 1
                if _r['solo']: solo += 1
                songs += 1

        solo_games = solo/3
        duo_games = (songs-solo)/4

        if songs == 50:
            await ctx.message.channel.send(f"From your last session of maimai DX+ ({date_played}), you played a total of at least {songs} songs.\
            \nOut of those {songs} songs, you achieved a new record in {pb} of them.")
        else:
            await ctx.message.channel.send(f"From your last session of maimai DX+ ({date_played}), you played a total of {songs} songs.\
            \nOut of those {songs} songs, you achieved a new record in {pb} of them. You played a total of {int(solo_games+duo_games)} games: {int(solo_games)} by yourself and {int(duo_games)} with someone else.")
