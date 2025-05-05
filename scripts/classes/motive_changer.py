import json
import datetime
from discord.ext import commands, tasks


class MotiveChanger(commands.Cog):
    def __init__(self, bot, default_motive_name="Default", json_motive_file_name="motives.json"):
        self.bot = bot
        self.available_guilds = {}
        self.current_motive = None
        self.default_motive = default_motive_name
        self.json_motive_file_name = json_motive_file_name

    async def on_custom_ready(self):
        """This function is called when the bot is ready."""
        self.check_date.start()
        print("MotiveChanger cog is ready.")
        with open('config.json', 'r', encoding='utf8') as f:
            config = json.load(f)
            self.available_guilds = await self.get_bot_channel_with_guild(config['bot_channel'])
            self.current_motive = config['current_motive']

    async def cog_unload(self):
        self.check_date.cancel()

    @tasks.loop(hours=1)  # Check every hour
    async def check_date(self):
        if self.available_guilds == {}:
            print('No guilds found. Register the bot to a guild first.')
            return
        if self.current_motive is None:
            print('No current motive found in the config file.')
            return
        with open('config.json', 'r', encoding='utf8') as f:
            config = json.load(f)
            now = datetime.datetime.now()
            motive_dates = config['motive_dates']
            is_motive_loaded = False
            for motive_name, date_frames in motive_dates.items():
                if self.is_date_in_range(now.month, date_frames['date_start']['month'], date_frames['date_end']['month']):
                    if self.is_date_in_range(now.day, date_frames['date_start']['day'], date_frames['date_end']['day']):
                        if self.current_motive != motive_name:
                            is_motive_loaded = await self.change_guild_motives(motive_name)
                            if is_motive_loaded:
                                self.current_motive = motive_name
                                config['current_motive'] = motive_name
                                with open('config.json', 'w', encoding='utf8') as f:
                                    json.dump(config, f, indent=4,
                                              ensure_ascii=False)
                                return
            if self.current_motive != self.default_motive:
                is_motive_loaded = await self.change_guild_motives(self.default_motive)
                if is_motive_loaded:
                    config['current_motive'] = self.default_motive
                    with open('config.json', 'w', encoding='utf8') as f:
                        json.dump(config, f, indent=4,
                                  ensure_ascii=False)
                    self.current_motive = self.default_motive

    @check_date.before_loop
    async def before_check_date(self):
        await self.bot.wait_until_ready()
        print('Waiting for the bot to be ready...')

    @commands.command(name="save_motive")
    @commands.has_permissions(administrator=True)
    async def save_motive(self, ctx):
        if len(ctx.message.content.split()) < 2:
            await ctx.send('Please provide a motive name.')
            return
        else:
            with open(self.json_motive_file_name, 'r', encoding='utf8') as f:
                try:
                    existing_data = json.load(f)
                    if ctx.message.content.split()[1] in existing_data.keys():
                        await ctx.send('Motive already exists. Please use a different name.')
                        return
                    else:
                        motive_dict = await self.encapsulate_motive(ctx)
                        existing_data.update(motive_dict)
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
            with open(self.json_motive_file_name, 'r', encoding='utf8') as f:
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
            with open(self.json_motive_file_name, 'r', encoding='utf8') as f:
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
            with open(self.json_motive_file_name, 'r', encoding='utf8') as f:
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

    @commands.command(name="manual_load_motive")
    @commands.has_permissions(administrator=True)
    async def manual_load_motive(self, ctx):
        if len(ctx.message.content.split()) < 2:
            await ctx.send('Please provide a motive name.')
            return
        motive_name = ctx.message.content.split()[1]
        try:
            with open(self.json_motive_file_name, 'r', encoding='utf8') as f:
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

    @commands.command(name="load_motive_on_date")
    @commands.has_permissions(administrator=True)
    async def load_motive_on_date(self, guild_id, channel_id, motive_name):
        """Load the motive on a specific date."""
        with open(self.json_motive_file_name, 'r', encoding='utf8') as f:
            channel_dict = json.load(f)
            if motive_name not in channel_dict.keys():
                await channel_id.send('Motive not found. Please check the name.')
                return False
            else:
                channel_dict = channel_dict[motive_name]
                for channel in guild_id.text_channels:
                    for c in channel_dict['text_channels']:
                        if str(channel.id) == str(c[0]):
                            await channel.edit(name=c[1])
                            channel_dict['text_channels'].remove(c)
                for channel in guild_id.voice_channels:
                    for c in channel_dict['voice_channels']:
                        if str(channel.id) == str(c[0]):
                            await channel.edit(name=c[1])
                            channel_dict['voice_channels'].remove(c)
                await channel_id.send('Motive loaded successfully.')
                return True

    async def save_motive_to_file(self, ctx, channel_dict, send_message):
        with open(self.json_motive_file_name, 'w', encoding='utf8') as f:
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

    async def get_bot_channel_with_guild(self, channel_name):
        """Get the guilds the bot is in."""
        guilds = {}
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == channel_name:
                    guilds[guild.id] = channel.id
        return guilds

    def is_date_in_range(self, current, start, end):
        """Check if the current month is in the range."""
        if start <= end:
            return start <= current <= end
        else:
            # Range crosses year-end (e.g., December–January)
            return current >= start or current <= end

    async def change_guild_motives(self, motive_name):
        is_motive_loaded = False
        for guild_id, channel_id in self.available_guilds.items():
            guild_id = self.bot.get_guild(guild_id)
            channel_id = guild_id.get_channel(channel_id)
            is_motive_loaded = await self.load_motive_on_date(guild_id, channel_id, motive_name)
        return is_motive_loaded
