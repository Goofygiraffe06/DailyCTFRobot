# cogs/misc.py - It contains all the miscellaneous functions used by the bot such as help and ping (just decluttering)

import discord
from discord.ext import commands
import time


class misc(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(name="ding")
  async def _ping(self, ctx):
    """ Pong with latency! """
    before = time.monotonic()
    message = await ctx.send("Dong!")
    ping = (time.monotonic() - before) * 1000
    await message.edit(content=f"Dong!  `{int(ping)}ms`")
    print(f"Dong {int(ping)}ms")

  @discord.app_commands.command(name="ping",
                                description="Check if the bot is alive or not.")
  async def ping(self, interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong!")

    # Custom help command
  @discord.app_commands.command(
      name="help",
      description="Displays the list of commands and their descriptions.")
  async def help_command(self, interaction: discord.Interaction) -> None:
    embed = discord.Embed(
        title="DailyCTF Robot Help",
        description="List of available commands. DailyCTF Robot is a bot to automate ...",
        color=0x55A7F7)

    # General Commands
    general_commands = """
    `/ping` - Check if the bot is alive.
    `/submit <flag>` - Submit the CTF flag.
    `/timeleft` - Tells the time left for the hint and the challenge end.
    `/feedback` - Submit feedback, bugs, or suggestions.
    `/rate` - Rate an active challenge.
    """
    embed.add_field(name="General Commands",
                    value=general_commands,
                    inline=False)

    # Admin Commands
    admin_commands = """
    `/setchallenge` - Create a new challenge.
    `/shutdown` - Shutdown the active challenge.
    `/setup` - Setup bot settings for the server.
    """
    embed.add_field(name="Admin Commands (for CTF creators)",
                    value=admin_commands,
                    inline=False)

    await interaction.response.send_message(embed=embed)


async def setup(bot) -> None:
  await bot.add_cog(misc(bot))
