import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

class ModmailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timers = {}
        self.task = self.bot.loop.create_task(self.timer_loop())

    async def timer_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = datetime.now(timezone.utc)
                for cid, time in list(self.timers.items()):
                    try:
                        if channel := self.bot.get_channel(cid):
                            minutes = (now - time).total_seconds() / 60
                            emoji = self.get_emoji(minutes)
                            if not channel.name.startswith(emoji):
                                name = channel.name.split('│')[-1].strip() if '│' in channel.name else channel.name
                                await asyncio.wait_for(channel.edit(name=f"{emoji}│{name}"[:100]), timeout=5.0)
                    except Exception:
                        self.timers.pop(cid, None)
            except Exception:
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
            try:
                await asyncio.wait_for(thread.channel.edit(name=f"🟢│{thread.channel.name}"), timeout=5.0)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        if not (channel and creator and not is_anonymous and not creator.bot):
            return
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
