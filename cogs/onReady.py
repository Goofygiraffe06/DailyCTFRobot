# cogs/onReady.py - Manages activity status, On join messages and also unexpected bot restarts.

import logging
from discord.ext import commands, tasks
import random
from .utils import release_hints, end_challenge
import discord


class onReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Fun 1337-styled activities for bot presence
    ACTIVITIES = [
        "Proving P = NP...",
        "Computing 6 x 9...",
        "Mining bitcoin...",
        "Dividing by 0...",
        "Initialising Skynet...",
        "[REDACTED]",
        "Downloading more RAM...",
        "Ordering 1s and 0s...",
        "Navigating neural network...",
        "Importing machine learning...",
        "Issuing Alice and Bob one-time pads...",
        "Mining bitcoin cash...",
        "Generating key material by trying to escape vim...",
        "for i in range(additional): Pylon()",
        "(creating unresolved tension...",
        "Symlinking emacs and vim to ed...",
        "Training branch predictor...",
        "Timing cache hits...",
        "Speculatively executing recipes...",
        "Adding LLM hallucinations...",
        "Cracking quantum encryption...",
        "Breaching mainframe...",
        "Accessing secret databases...",
        "Decompiling neural algorithms...",
        "Launching DDoS on Matrix...",
        "Rooting cyberspace...",
        "Bypassing firewall...",
        "Infiltrating digital fortress...",
        "Overriding security protocols...",
        "Decrypting alien communications...",
        "Running penetration tests...",
        "Compiling stealth trojans...",
        "Exploiting zero-day vulnerabilities...",
        "Activating VPN...",
        "Cloaking IP address...",
        "Hijacking satellite...",
        "Routing through proxies...",
        "Establishing darknet connection...",
        "Uploading virus to the Grid...",
        "Initializing worm propagation...",
    ]

    # Task to change bot's activity every 30 minutes
    @tasks.loop(minutes=30)
    async def change_activity(self) -> None:
        activity = random.choice(self.ACTIVITIES)
        await self.bot.change_presence(activity=discord.Game(name=activity))
        logging.info(f"Activity set to: {activity}")

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"We have logged in as {self.bot.user}")
        try:
            synced = await self.bot.tree.sync()
            logging.info(f"Synced {len(synced)} command(s)...")
        except Exception as e:
            logging.error(f"Error syncing commands!: {e}")
        try:
            self.bot.loop.create_task(release_hints(self.bot))
        except Exception as e:
            logging.error(e)
        self.bot.loop.create_task(end_challenge(self.bot))
        await self.change_activity.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = guild.system_channel or next(
            (
                channel
                for channel in guild.channels
                if isinstance(channel, discord.TextChannel)
            ),
            None,
        )
        if channel is not None:
            await channel.send(
                "Hello, thanks for adding DailyCTF Robot to your server! 🎉\n"
                "DailyCTF Robot is a bot designed to automate and enhance the experience of hosting Capture The Flag challenges, making it seamless for both organizers and participants."
            )
            await channel.send(
                "To get started, please use the `/setup` command to configure me for your server."
            )
            cheatsheet = """
			**Basic Commands Cheatsheet:**
			`/setup` - Configure the bot for your server.
			`/help` - Shows a list of available commands.
			`/setchallenge` - Create a new challenge.
			`/shutdown` - Shutdown the active CTF challenge.
			`/timeleft` - Shows the remaining time for hint and for the challenege to end.
			`/feedback` - Allows to submit feedback to bot creator.
			"""
            await channel.send(cheatsheet)


async def setup(bot) -> None:
    await bot.add_cog(onReady(bot))
