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
                        await self.save_motive_to_file(ctx, existing_data, "Motive saved successfully.")
                except json.JSONDecodeError:
                    motive_dict = await self.encapsulate_motive(ctx)
                    await self.save_motive_to_file(ctx, motive_dict, "Motive saved successfully.")
                    return

    @commands.command(name="delete_motive")
    @commands.has_permissions(administrator=True)
    async def delete_motive(self, ctx):
        if len(ctx.message.content.split()) < 2:
            await ctx.send('Please provide a motive name.')
            return
        motive_name = ctx.message.content.split()[1]
        try:
            with open('motives.json', 'r', encoding='utf8') as f:
                channel_dict = json.load(f)
                if motive_name not in channel_dict.keys():
                    await ctx.send('Motive not found. Please check the name.')
                    return
                else:
                    del channel_dict[motive_name]
                    await self.save_motive_to_file(ctx, channel_dict, "Motive deleted successfully.")
        except FileNotFoundError:
            await ctx.send('No saved motive found. Please save a motive first.')

    @commands.command(name="remove_channel")
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx):
        """Manually remove a channel from the motive."""
        try:
            with open('motives.json', 'r', encoding='utf8') as f:
                channel_dict = json.load(f)
                channel_to_remove = await self.get_channel_id(ctx)
                if channel_to_remove is None:
                    return
                channel_found = False
                for channel in channel_dict.values():
                    for value in channel['text_channels']:
                        if str(value[0]) == str(channel_to_remove):
                            channel['text_channels'].remove(value)
                            await self.save_motive_to_file(ctx, channel_dict, 'Channel removed successfully.')
                            channel_found = True
                if not channel_found:
                    for channel in channel_dict.values():
                        for value in channel['voice_channels']:
                            if str(value[0]) == str(channel_to_remove):
                                channel['voice_channels'].remove(value)
                                await self.save_motive_to_file(ctx, channel_dict, 'Channel removed successfully.')
                                channel_found = True
                if not channel_found:
                    await ctx.send('Channel not found in the motive.')
        except FileNotFoundError:
            await ctx.send('No saved motive found. Please save a motive first.')

    @commands.command(name="update_missing_channels")
    @commands.has_permissions(administrator=True)
    async def update_missing_channels(self, ctx):
        try:
            with open('motives.json', 'r', encoding='utf8') as f:
                channel_dict = json.load(f)
                motives_text_disparity = False
                motives_voice_disparity = False
                for channels in channel_dict.values():
                    if len(channels['text_channels']) > len(ctx.guild.text_channels):
                        channels['text_channels'] = await self.remove_additional_channels(ctx, channels['text_channels'], ctx.guild.text_channels)
                        motives_text_disparity = True
                    else:
                        break
                for channels in channel_dict.values():
                    if len(channels['voice_channels']) > len(ctx.guild.voice_channels):
                        channels['voice_channels'] = await self.remove_additional_channels(ctx, channels['voice_channels'], ctx.guild.voice_channels)
                        motives_voice_disparity = True
                    else:
                        break
                if not motives_text_disparity:
                    for channel in channel_dict.values():
                        if len(channel['text_channels']) < len(ctx.guild.text_channels):
                            channel['text_channels'] = await self.add_missing_channels(ctx, channel['text_channels'], ctx.guild.text_channels)
                            motives_text_disparity = True
                if not motives_voice_disparity:
                    for channel in channel_dict.values():
                        if len(channel['voice_channels']) < len(ctx.guild.voice_channels):
                            channel['voice_channels'] = await self.add_missing_channels(ctx, channel['voice_channels'], ctx.guild.voice_channels)
                            motives_voice_disparity = True
                if not motives_text_disparity and not motives_voice_disparity:
                    await ctx.send('No errors found in motive file / channel layout.')
                    return
                await self.save_motive_to_file(ctx, channel_dict, 'Motives updated successfully.')
        except FileNotFoundError:
            await ctx.send('No saved motive found. Please save a motive first.')

    @commands.command(name="load_motive")
    @commands.has_permissions(administrator=True)
    async def load_motive(self, ctx):
        if len(ctx.message.content.split()) < 2:
            await ctx.send('Please provide a motive name.')
            return
        motive_name = ctx.message.content.split()[1]
        try:
            with open('motives.json', 'r', encoding='utf8') as f:
                channel_dict = json.load(f)
                if motive_name not in channel_dict.keys():
                    await ctx.send('Motive not found. Please check the name.')
                    return
                else:
                    channel_dict = channel_dict[motive_name]
                    for channel in ctx.guild.text_channels:
                        for c in channel_dict['text_channels']:
                            if str(channel.id) == str(c[0]):
                                await channel.edit(name=c[1])
                                channel_dict['text_channels'].remove(c)
                    for channel in ctx.guild.voice_channels:
                        for c in channel_dict['voice_channels']:
                            if str(channel.id) == str(c[0]):
                                await channel.edit(name=c[1])
                                channel_dict['voice_channels'].remove(c)
                    await ctx.send('Motive loaded successfully.')
        except FileNotFoundError:
            await ctx.send('No saved motive found. Please save a motive first.')

    async def save_motive_to_file(self, ctx, channel_dict, send_message):
        with open('motives.json', 'w', encoding='utf8') as f:
            try:
                json.dump(channel_dict, f, indent=4, ensure_ascii=False)
                await ctx.send(send_message)
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

    async def get_channel_id(self, ctx):
        if len(ctx.message.content.split()) < 2:
            await ctx.send('Please provide a channel name.')
            return
        elif len(ctx.message.content.split()) > 2:  # In case of encountering a voice channel
            channel_name = ' '.join(ctx.message.content.split()[1:])
        else:  # In case of encountering a text channel
            channel_name = ctx.message.content.split()
        print(channel_name)
        for channel in ctx.guild.text_channels:
            if channel.name == channel_name:
                return channel.id
        for channel in ctx.guild.voice_channels:
            if channel.name == channel_name:
                return channel.id
        await ctx.send('Channel not found. Please check the name.')
        return None

    async def remove_additional_channels(self, ctx, motive_channels, guild_text_channels):
        for channel in motive_channels:
            if str(channel[0]) not in [str(c.id) for c in guild_text_channels]:
                motive_channels.remove(channel)
                await ctx.send(f'Removed additional channel: {channel[1]}')
        return motive_channels

    async def add_missing_channels(self, ctx, motive_channels, guild_voice_channels):
        for channel in guild_voice_channels:
            if str(channel.id) not in [str(c[0]) for c in motive_channels]:
                motive_channels.append([channel.id, channel.name])
                await ctx.send(f'Added missing channel: {channel.name}')
        return motive_channels
