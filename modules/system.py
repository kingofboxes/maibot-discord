import discord
from datetime import datetime
from discord.ext import commands

# System cog.
class System(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    @commands.Cog.listener()
    async def on_ready(self):

        # Activate background checks.
        print(f'[{datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}] Logged in as {self.bot.user}!')

        # Fluff.
        custom_activity = discord.Game(name="maimai DX+")
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

    # Manually shut bot down.
    @commands.command(help='Shuts the bot down')
    @commands.is_owner()
    async def nap(self, ctx):

        # Alert everyone that bot is shutting down.
        await ctx.message.channel.send("I sleep.")

        # Closes the bot gracefully.
        await self.bot.logout()
