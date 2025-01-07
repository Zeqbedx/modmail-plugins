import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

class ModmailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timers = {}
        self._ready = asyncio.Event()
        self.task = self.bot.loop.create_task(self.timer_loop())

    def cog_unload(self):
        self.task.cancel()

    async def timer_loop(self):
        try:
            await self.bot.wait_until_ready()
            self._ready.set()
            
            while True:
                now = datetime.now(timezone.utc)
                channels_to_update = {}

                for channel_id, last_time in list(self.timers.items()):
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        self.timers.pop(channel_id, None)
                        continue

                    minutes = (now - last_time).total_seconds() / 60
                    emoji = self.get_emoji(minutes)
                    
                    current_name = channel.name
                    if not current_name.startswith(emoji):
                        base_name = current_name.split('│', 1)[-1].strip() if '│' in current_name else current_name
                        channels_to_update[channel] = f"{emoji}│{base_name}"

                for channel, new_name in channels_to_update.items():
                    try:
                        await channel.edit(name=new_name[:100])
                    except (discord.NotFound, discord.Forbidden):
                        self.timers.pop(channel.id, None)
                    except Exception:
                        pass

                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Timer loop error: {e}")

    def get_emoji(self, minutes):
        if minutes <= 15: return "🟢"
        if minutes <= 30: return "🟡"
        if minutes <= 45: return "🟠"
        if minutes <= 60: return "🔴"
        if minutes <= 120: return "💀"
        return "☠️"

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        await self._ready.wait()
        if hasattr(thread, 'channel') and thread.channel:
            self.timers[thread.channel.id] = datetime.now(timezone.utc)
            try:
                await thread.channel.edit(name=f"🟢│{thread.channel.name}")
            except:
                pass

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        await self._ready.wait()
        if not channel or not creator or is_anonymous:
            return
            
        if creator.bot:
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
