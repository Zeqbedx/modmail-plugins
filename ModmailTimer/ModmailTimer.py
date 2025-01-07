import discord
from discord.ext import commands, tasks
import datetime
import re

class ModMailTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_timers = {}
        self.check_timers.start()

    def cog_unload(self):
        self.check_timers.cancel()

    @tasks.loop(minutes=1)
    async def check_timers(self):
        current_time = datetime.datetime.now()
        for channel_id, timer_data in list(self.ticket_timers.items()):
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            elapsed_minutes = (current_time - timer_data['last_user_message']).total_seconds() / 60
            new_emoji = self.get_status_emoji(elapsed_minutes)
            
            if new_emoji != timer_data['current_emoji']:
                ticket_number = re.search(r'ticket-(\d{4})', channel.name)
                if ticket_number:
                    await channel.edit(name=f"{new_emoji}︱ticket-{ticket_number.group(1)}")
                    self.ticket_timers[channel_id]['current_emoji'] = new_emoji

    def get_status_emoji(self, minutes):
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
    async def on_message(self, message):
        if not message.guild or not isinstance(message.channel, discord.TextChannel):
            return

        if not message.channel.name.startswith(('🟢', '🟡', '🟠', '🔴', '💀', '☠️')):
            return

        is_staff = any(role.name.lower() == "staff" for role in message.author.roles)
        
        if is_staff:
            if message.channel.id in self.ticket_timers:
                del self.ticket_timers[message.channel.id]
                ticket_number = re.search(r'ticket-(\d{4})', message.channel.name)
                if ticket_number:
                    await message.channel.edit(name=f"🟢︱ticket-{ticket_number.group(1)}")
        else:
            self.ticket_timers[message.channel.id] = {
                'last_user_message': datetime.datetime.now(),
                'current_emoji': "🟢"
            }

async def setup(bot):
    await bot.add_cog(ModMailTimer(bot))