import discord
from auth_key import token  # Ensure you have a token.py file with your bot token


class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.content.upper() == 'READ':
            await message.channel.send('Detected text channels...')
            for channel in message.guild.text_channels:
                await message.channel.send(f'Channel: {channel.name}')
            await message.channel.send('Detected voice channels...')
            for channel in message.guild.voice_channels:
                await message.channel.send(f'Channel: {channel.name}')
            await message.channel.send('Detected categories...')
            for category in message.guild.categories:
                await message.channel.send(f'Category: {category.name}')


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token)
