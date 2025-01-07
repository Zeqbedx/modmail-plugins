import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

class ModmailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timers = {}
        self.bot.loop.create_task(self.timer_loop())

    async def timer_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = datetime.now(timezone.utc)
                for channel_id in list(self.timers.keys()):
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        self.timers.pop(channel_id, None)
                        continue
                    
                    minutes = (now - self.timers[channel_id]).total_seconds() / 60
                    emoji = self.get_emoji(minutes)
                    
                    try:
                        if not channel.name.startswith(emoji):
                            name = channel.name
                            if '│' in name:
                                name = name.split('│', 1)[1].strip()
                            await channel.edit(name=f"{emoji}│{name}")
                    except:
                        self.timers.pop(channel_id, None)
            except:
                pass
            await asyncio.sleep(60)

    def get_emoji(self, minutes):
        if minutes <= 15: return "🟢"
        if minutes <= 30: return "🟡"
        if minutes <= 45: return "🟠"
        if minutes <= 60: return "🔴"
        if minutes <= 120: return "💀"
        return "☠️"

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.channel:
            self.timers[thread.channel.id] = datetime.now(timezone.utc)
            await thread.channel.edit(name=f"🟢│{thread.channel.name}")

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        if channel and not creator.bot and not is_anonymous:
            if hasattr(creator, 'roles'):
                self.timers.pop(channel.id, None)
            else:
                self.timers[channel.id] = datetime.now(timezone.utc)

    @commands.Cog.listener()
    async def on_thread_close(self, thread, *args, **kwargs):
        if thread.channel:
            self.timers.pop(thread.channel.id, None)

async def setup(bot):
    await bot.add_cog(ModmailTimer(bot))
