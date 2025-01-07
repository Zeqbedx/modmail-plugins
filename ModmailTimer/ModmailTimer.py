import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

class ModmailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timers = {}
        self._task = None
        self.start_timer()

    def start_timer(self):
        self._task = self.bot.loop.create_task(self.timer_loop())

    async def timer_loop(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                now = datetime.now(timezone.utc)
                for cid in list(self.timers.keys()):
                    if channel := self.bot.get_channel(cid):
                        minutes = (now - self.timers[cid]).total_seconds() / 60
                        emoji = self.get_emoji(minutes)
                        if not channel.name.startswith(emoji):
                            name = channel.name.split('│')[-1].strip() if '│' in channel.name else channel.name
                            try:
                                await channel.edit(name=f"{emoji}│{name}"[:100])
                            except:
                                self.timers.pop(cid, None)
                    else:
                        self.timers.pop(cid, None)
            except:
                pass
            await asyncio.sleep(60)

    def get_emoji(self, minutes):
        if seconds <= 3: return "🟢"
        if seconds <= 5: return "🟡"
        if seconds <= 10: return "🟠"
        if seconds <= 15: return "🔴"
        if seconds <= 20: return "💀"
        return "☠️"

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.channel:
            self.timers[thread.channel.id] = datetime.now(timezone.utc)
            try:
                await thread.channel.edit(name=f"🟢│{thread.channel.name}")
            except:
                pass

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        if not channel or is_anonymous or creator.bot:
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
