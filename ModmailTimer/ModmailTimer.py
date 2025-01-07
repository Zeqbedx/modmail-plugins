import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone

class ModmailTimer(commands.Cog):
    """
    Timer plugin for ModMail that updates channel names based on response time.
    """

    def __init__(self, bot):
        self.bot = bot
        self.ticket_timers = {}
        self.checking = asyncio.Lock()
        self.bot.loop.create_task(self.check_timers())
        print("[ModmailTimer] Plugin initialized")

    async def check_timers(self):
        await self.bot.wait_until_ready()
        print("[ModmailTimer] Starting timer checks")
        while not self.bot.is_closed():
            async with self.checking:
                try:
                    current_time = datetime.now(timezone.utc)
                    for channel_id, timer_data in list(self.ticket_timers.items()):
                        try:
                            channel = self.bot.get_channel(channel_id)
                            if not channel:
                                # Remove invalid channel from tracking
                                del self.ticket_timers[channel_id]
                                print(f"[ModmailTimer] Removed invalid channel {channel_id}")
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
                                await channel.edit(name=new_name)
                                print(f"[ModmailTimer] Updated {channel.name} to {new_name}")
                                self.ticket_timers[channel_id]['current_emoji'] = new_emoji
                        except discord.NotFound:
                            # Channel was deleted or is invalid
                            if channel_id in self.ticket_timers:
                                del self.ticket_timers[channel_id]
                            print(f"[ModmailTimer] Removed not found channel {channel_id}")
                        except Exception as e:
                            print(f"[ModmailTimer] Error updating channel {channel_id}: {e}")
                except Exception as e:
                    print(f"[ModmailTimer] Error in timer check: {e}")
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
        """Initialize timer when a new thread is created"""
        if not hasattr(thread, 'channel') or not thread.channel:
            print("[ModmailTimer] Thread has no channel, skipping")
            return
            
        try:
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(thread.channel.id)
            if not channel:
                print(f"[ModmailTimer] Could not find channel for thread {thread.id}")
                return
            
        self.ticket_timers[thread.channel.id] = {
            'last_user_message': datetime.now(timezone.utc),
            'current_emoji': "🟢"
        }
        current_name = thread.channel.name
        try:
            await thread.channel.edit(name=f"🟢│{current_name}")
            print(f"[ModmailTimer] Initialized thread {thread.channel.name}")
        except Exception as e:
            print(f"[ModmailTimer] Error in thread create: {e}")

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous=False):
        """Update timer on replies"""
        if not channel or is_anonymous:
            return

        try:
            if creator.bot:  # Skip bot messages
                return
                
            is_mod = hasattr(creator, 'roles')  # Staff members have roles
            
            if is_mod:
                if channel.id in self.ticket_timers:
                    del self.ticket_timers[channel.id]
                    current_name = channel.name.split('│')[-1].strip()
                    await channel.edit(name=f"🟢│{current_name}")
                    print(f"[ModmailTimer] Reset timer - Staff replied in {channel.name}")
            else:
                self.ticket_timers[channel.id] = {
                    'last_user_message': datetime.now(timezone.utc),
                    'current_emoji': "🟢"
                }
                print(f"[ModmailTimer] Started timer - User replied in {channel.name}")
        except Exception as e:
            print(f"[ModmailTimer] Error in thread reply: {e}")

    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled=False):
        """Clean up timer when thread is closed"""
        if thread.channel and thread.channel.id in self.ticket_timers:
            del self.ticket_timers[thread.channel.id]
            print(f"[ModmailTimer] Cleaned up timer for {thread.channel.name}")

async def setup(bot):
    await bot.add_cog(ModmailTimer(bot))
