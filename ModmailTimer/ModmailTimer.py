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
        self.db = bot.api.get_plugin_partition(self)
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
                    threads = self.bot.threads.cache.items()
                    
                    for thread_id, thread in threads:
                        if not thread.channel:
                            continue
                            
                        if thread.channel.id not in self.ticket_timers and not thread.close_time:
                            # Initialize timer for existing open threads
                            self.ticket_timers[thread.channel.id] = {
                                'last_user_message': current_time,
                                'current_emoji': "🟢"
                            }
                            continue

                        if thread.channel.id in self.ticket_timers:
                            elapsed_minutes = (current_time - self.ticket_timers[thread.channel.id]['last_user_message']).total_seconds() / 60
                            new_emoji = self.get_status_emoji(elapsed_minutes)
                            
                            if new_emoji != self.ticket_timers[thread.channel.id]['current_emoji']:
                                try:
                                    current_name = thread.channel.name
                                    if any(current_name.startswith(emoji) for emoji in ['🟢', '🟡', '🟠', '🔴', '💀', '☠️']):
                                        new_name = f"{new_emoji}{current_name[1:]}"
                                    else:
                                        new_name = f"{new_emoji}│{current_name}"
                                    
                                    await thread.channel.edit(name=new_name)
                                    print(f"[ModmailTimer] Updated channel {thread.channel.id} to {new_emoji}")
                                    self.ticket_timers[thread.channel.id]['current_emoji'] = new_emoji
                                except Exception as e:
                                    print(f"[ModmailTimer] Error updating channel: {e}")

                except Exception as e:
                    print(f"[ModmailTimer] Error in timer check: {e}")
            
            await asyncio.sleep(60)  # Check every minute

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
    async def on_thread_create(self, thread, creator, category, initial_message, message, silent):
        """Initialize timer when a new thread is created"""
        if thread.channel:
            self.ticket_timers[thread.channel.id] = {
                'last_user_message': datetime.now(timezone.utc),
                'current_emoji': "🟢"
            }
            try:
                current_name = thread.channel.name
                await thread.channel.edit(name=f"🟢│{current_name}")
                print(f"[ModmailTimer] Initialized new thread {thread.channel.id}")
            except Exception as e:
                print(f"[ModmailTimer] Error initializing thread: {e}")

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, message, creator, channel, is_anonymous):
        """Handle replies in the thread"""
        if not channel or is_anonymous:
            return

        try:
            is_mod = not isinstance(creator, discord.Member)  # ModMail's way of identifying staff
            
            if is_mod:
                # Reset timer when staff replies
                if channel.id in self.ticket_timers:
                    del self.ticket_timers[channel.id]
                    current_name = channel.name
                    if any(current_name.startswith(emoji) for emoji in ['🟢', '🟡', '🟠', '🔴', '💀', '☠️']):
                        new_name = f"🟢{current_name[1:]}"
                        await channel.edit(name=new_name)
                        print(f"[ModmailTimer] Reset timer for {channel.id} - Staff replied")
            else:
                # Start/update timer when user replies
                self.ticket_timers[channel.id] = {
                    'last_user_message': datetime.now(timezone.utc),
                    'current_emoji': "🟢"
                }
                print(f"[ModmailTimer] Updated timer for {channel.id} - User replied")
        except Exception as e:
            print(f"[ModmailTimer] Error in on_thread_reply: {e}")

    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled):
        """Clean up timer when thread is closed"""
        if thread.channel and thread.channel.id in self.ticket_timers:
            del self.ticket_timers[thread.channel.id]
            print(f"[ModmailTimer] Cleaned up timer for closed thread {thread.channel.id}")

async def setup(bot):
    await bot.add_cog(ModmailTimer(bot))
