import requests, json
from modules.client import *
from discord.ext import commands

# DXNet cog for maibot DX+, specifically for database manipulation.
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

    # Dumps album art database.
    @commands.command(help='Dumps album art database.')
    @commands.is_owner()
    async def dump(self, ctx):

        images = self.db["images"].find()

        if images.count() == 0:
            await ctx.message.channel.send("Image database does not exist.")
            return
        else:
            with open('data/images.json', 'w') as fp:
                db = []
                for entry in images:
                    db.append(entry)
                json.dump(db, fp, indent=3, ensure_ascii=False)
            fp.close()

        await ctx.message.channel.send("Images successfully dumped.")

    # Loads album art database.
    @commands.command(help='Loads album art database.')
    @commands.is_owner()
    async def load(self, ctx):

        images = self.db["images"]

        with open('data/images.json', 'r') as fp:
            db = json.load(fp)
            fp.close()

        for _s in db:
            _q = { "_id" : _s['_id']}
            _v = { "$set": _s }
            if images.find_one(_q):
                images.update_one(_q, _v)
            else:
                images.insert_one(_s)

        # Alert user that process is done.
        await ctx.message.channel.send("Image database successfully loaded.")

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
            if profile.find_one(_q):
                playlist = profile.find_one(_q)['playlist']
                p['playlist'] = playlist
                _v = { "$set": p }
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