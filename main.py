# main.py - It initialises the bot, imports cogs and entrypoint of the bot.

import discord
import logging
from discord.ext import commands
import os
import asyncio
import pyfiglet

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

# Suppress Flask development server log
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

os.system("clear")
print(pyfiglet.figlet_format("DailyCTF Robot"))


async def main():
    async with bot:
        # Load cogs
        for filename in os.listdir('./cogs'):
            # utils.py is a non cog file and used to import neccesary functions
            if (
                filename.endswith('.py')
                and filename != '__init__.py'
                and filename != 'utils.py'
                and filename != 'db_utils.py'
            ):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    logging.info(f"Loaded {filename} cog successfully.")
                except Exception as e:
                    logging.error(f"Error loading {filename}: {e}")
        await bot.start(os.environ['token'])

try:
    asyncio.run(main())
except (discord.errors.HTTPException, discord.app_commands.errors.CommandInvokeError):
    logging.error("Being Rate Limited!")
    os.system("kill 1")  # Kill the current running process
    os.system("python restart.py")
