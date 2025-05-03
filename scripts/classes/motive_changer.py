import json
from discord.ext import commands


class MotiveChanger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="save_motive")
    @commands.has_permissions(administrator=True)
    async def save_motive(self, ctx):
        if len(ctx.message.content.split()) < 2:
            await ctx.send('Please provide a motive name.')
            return
        else:
            with open('motives.json', 'r', encoding='utf8') as f:
                try:
                    existing_data = json.load(f)
                    if ctx.message.content.split()[1] in existing_data.keys():
                        await ctx.send('Motive already exists. Please use a different name.')
                        return
                    else:
                        motive_dict = await self.encapsulate_motive(ctx)
                        existing_data.update(motive_dict)
                        print(motive_dict)  # For debugging purposes
                        await self.save_motive_to_file(ctx, existing_data)
                except json.JSONDecodeError:
                    motive_dict = await self.encapsulate_motive(ctx)
                    existing_data = {
                        ctx.message.content.split()[1]: motive_dict
                    }
                    await self.save_motive_to_file(ctx, existing_data)
                    return

    @commands.command(name="load_motive")
    @commands.has_permissions(administrator=True)
    async def load_motive(self, ctx):
        """Work in progress"""
        try:
            with open('motives.json', 'r', encoding='utf8') as f:
                channel_dict = json.load(f)
            await ctx.send('Channel data loaded from file.')
            await ctx.send(f"Text Channels: {channel_dict['text_channels']}")
            await ctx.send(f"Voice Channels: {channel_dict['voice_channels']}")
        except FileNotFoundError:
            await ctx.send('No saved motive found. Please save a motive first.')

    async def save_motive_to_file(self, ctx, channel_dict):
        with open('motives.json', 'w', encoding='utf8') as f:
            try:
                json.dump(channel_dict, f, indent=4, ensure_ascii=False)
                await ctx.send('Motive saved successfully.')
            except json.JSONDecodeError as e:
                await ctx.send(f'Error saving motive: {e}')

    async def encapsulate_motive(self, ctx):
        channels_dict = {
            "text_channels": [[channel.id, channel.name] for channel in ctx.guild.text_channels],
            "voice_channels": [[channel.id, channel.name] for channel in ctx.guild.voice_channels],
        }
        motive_dict = {
            ctx.message.content.split()[1]: channels_dict,
        }
        return motive_dict
