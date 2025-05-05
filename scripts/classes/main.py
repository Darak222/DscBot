import discord
from discord.ext import commands
from traitlets import default
from auth_key import token, json_motive_file, default_motive_name
from motive_changer import MotiveChanger

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# json_motive_file contains the path to the JSON file with motives
# default_motive_name is the name of the default motive to be used if no motive is found in the JSON file


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    cog = MotiveChanger(bot, default_motive_name, json_motive_file)
    await bot.add_cog(cog)
    await cog.on_custom_ready()
    print('Cog loaded.')

bot.run(token)
