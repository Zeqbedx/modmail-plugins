import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

class ModmailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._timers = {}
        self._lock = asyncio.Lock()
        self._task = self.bot.loop.create_task(self._timer_loop())
    
    def cog_unload(self):
        self._task.cancel()

    async def _timer_loop(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                async with self._lock:
                    await self._update_channels()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Timer error: {e}")
                await asyncio.sleep(60)

    async def _update_channels(self):
        now = datetime.now(timezone.utc)
        for channel_id, data in list(self._timers.items()):
            try:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    del self._timers[channel_id]
                    continue

                minutes = (now - data['timestamp']).total_seconds() / 60
                emoji = self._get_emoji(minutes)
                
                if emoji != data['emoji']:
                    name = channel.name.split('│')[-1].strip() if '│' in channel.name else channel.name
                    new_name = f"{emoji}│{name}"[:100]
                    
                    try:
                        await channel.edit(name=new_name)
                        self._timers[channel_id]['emoji'] = emoji
                    except (discord.NotFound, discord.Forbidden):
                        del self._timers[channel_id]
                    except Exception as e:
                        print(f"Channel update error: {e}")
            except Exception as e:
                print(f"Channel {channel_id} error: {e}")

    def _get_emoji(self, minutes: float) -> str:
        if minutes <= 15: return "🟢"
        if minutes <= 30: return "🟡"
        if minutes <= 45: return "🟠"
        if minutes <= 60: return "🔴"
        if minutes <= 120: return "💀"
        return "☠️"

    def _start_timer(self, channel):
        if not channel:
            return
        self._timers[channel.id] = {
            'timestamp': datetime.now(timezone.utc),
            'emoji': "🟢"
        }

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if hasattr(thread, 'channel') and thread.channel:
            self._start_timer(thread.channel)
            await thread.channel.edit(name=f"🟢│{thread.channel.name}")

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        if not channel or is_anonymous or creator.bot:
            return

        is_mod = hasattr(creator, 'roles')
        if is_mod:
            if channel.id in self._timers:
                del self._timers[channel.id]
                name = channel.name.split('│')[-1].strip() if '│' in channel.name else channel.name
                await channel.edit(name=f"🟢│{name}")
        else:
            self._start_timer(channel)

    @commands.Cog.listener()
    async def on_thread_close(self, thread, *args, **kwargs):
        if thread.channel and thread.channel.id in self._timers:
            del self._timers[thread.channel.id]

async def setup(bot):
    await bot.add_cog(ModmailTimer(bot))
