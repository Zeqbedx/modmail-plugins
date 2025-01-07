import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone

class ModmailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_timers = {}
        self.checking = asyncio.Lock()
        self.bot.loop.create_task(self.check_timers())

    async def safe_edit_channel(self, channel, **kwargs):
        try:
            await channel.edit(**kwargs)
            return True
        except discord.NotFound:
            if channel.id in self.ticket_timers:
                del self.ticket_timers[channel.id]
            return False
        except discord.Forbidden:
            print(f"[ModmailTimer] Missing permissions to edit channel {channel.id}")
            return False
        except Exception as e:
            print(f"[ModmailTimer] Error editing channel {channel.id}: {e}")
            return False

    async def check_timers(self):
        while True:
            try:
                await self.bot.wait_until_ready()
                async with self.checking:
                    current_time = datetime.now(timezone.utc)
                    for channel_id, timer_data in list(self.ticket_timers.items()):
                        try:
                            channel = self.bot.get_channel(channel_id)
                            if not channel:
                                del self.ticket_timers[channel_id]
                                continue

                            elapsed_minutes = (current_time - timer_data['last_user_message']).total_seconds() / 60
                            new_emoji = self.get_status_emoji(elapsed_minutes)
                            
                            if new_emoji != timer_data['current_emoji']:
                                current_name = channel.name
                                if '│' in current_name:
                                    current_name = current_name.split('│')[-1].strip()
                                elif '-' in current_name:
                                    current_name = current_name.split('-', 1)[-1].strip()
                                new_name = f"{new_emoji}│{current_name}"
                                if len(new_name) > 100:
                                    new_name = new_name[:97] + "..."
                                
                                if await self.safe_edit_channel(channel, name=new_name):
                                    self.ticket_timers[channel_id]['current_emoji'] = new_emoji

                        except Exception as e:
                            print(f"[ModmailTimer] Error processing channel {channel_id}: {e}")
                            continue

                await asyncio.sleep(60)
            except asyncio.CancelledError:
                return
            except Exception as e:
                print(f"[ModmailTimer] Main loop error: {e}")
                await asyncio.sleep(60)

    def get_status_emoji(self, minutes: float) -> str:
        if minutes <= 15:
            return "🟢"
        elif minutes <= 30:
            return "🟡"
        elif minutes <= 45:
            return "🟠"
        elif minutes <= 60:
            return "🔴"
        elif minutes <= 120:
            return "💀"
        else:
            return "☠️"

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if not hasattr(thread, 'channel') or not thread.channel:
            return
            
        try:
            channel = thread.channel
            if not channel:
                return
                
            self.ticket_timers[channel.id] = {
                'last_user_message': datetime.now(timezone.utc),
                'current_emoji': "🟢"
            }
            await self.safe_edit_channel(channel, name=f"🟢│{channel.name}")
        except Exception as e:
            print(f"[ModmailTimer] Error in thread create: {e}")

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        if not channel or is_anonymous:
            return

        try:
            if creator.bot:
                return
                
            is_mod = hasattr(creator, 'roles')
            
            if is_mod:
                if channel.id in self.ticket_timers:
                    del self.ticket_timers[channel.id]
                    current_name = channel.name
                    if '│' in current_name:
                        current_name = current_name.split('│')[-1].strip()
                    elif '-' in current_name:
                        current_name = current_name.split('-', 1)[-1].strip()
                    await self.safe_edit_channel(channel, name=f"🟢│{current_name}")
            else:
                self.ticket_timers[channel.id] = {
                    'last_user_message': datetime.now(timezone.utc),
                    'current_emoji': "🟢"
                }
        except Exception as e:
            print(f"[ModmailTimer] Error in thread reply: {e}")

    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled=False):
        try:
            if thread.channel and thread.channel.id in self.ticket_timers:
                del self.ticket_timers[thread.channel.id]
        except Exception as e:
            print(f"[ModmailTimer] Error in thread close: {e}")

async def setup(bot):
    await bot.add_cog(ModmailTimer(bot))
