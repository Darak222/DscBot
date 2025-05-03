import discord
from discord.ext import commands
from auth_key import token
from motive_changer import MotiveChanger

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.add_cog(MotiveChanger(bot))
    print('Cog loaded.')

bot.run(token)
